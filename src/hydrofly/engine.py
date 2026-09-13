"""The only production groundwater solver adapter. Units: metres and days.

Positive Q is extraction. timflow returns head change relative to zero;
HydroFly adds the synthetic initial head datum. No analytical well equations
are reimplemented here.
"""
from dataclasses import dataclass
from functools import lru_cache
from threading import RLock

import numpy as np
import timflow.transient as tft


@dataclass(frozen=True)
class Aquifer:
    conductivity: float = 10.0  # m/day
    thickness: float = 80.0  # m
    storativity: float = 0.001  # dimensionless
    initial_head: float = 100.0  # m datum
    roof: float = 0.0  # m datum; keep head above this in this experiment

    def __post_init__(self):
        if not all(np.isfinite(v) for v in self.__dict__.values()):
            raise ValueError("Aquifer parameters must be finite")
        if min(self.conductivity, self.thickness, self.storativity) <= 0:
            raise ValueError("K, thickness and storativity must be positive")
        if self.initial_head <= self.roof:
            raise ValueError("Confined initial head must exceed the aquifer roof")

    @property
    def transmissivity(self):
        return self.conductivity * self.thickness


ANGLE = np.arange(10) * 2 * np.pi / 10
WELLS = np.column_stack((330 * np.cos(ANGLE), 270 * np.sin(ANGLE)))
CP_ANGLE = np.arange(24) * 2 * np.pi / 24
CONTROL_POINTS = np.vstack(([0, 0], np.column_stack((180 * np.cos(CP_ANGLE), 120 * np.sin(CP_ANGLE)))))
PIT_FLOOR = 80.0
TARGET_HEAD = PIT_FLOOR - 5.0
QMAX = 6000.0
TMIN = 0.001
TMAX = 365.0
GRID_AXIS = np.linspace(-650, 650, 35)
GX, GY = np.meshgrid(GRID_AXIS, GRID_AXIS)
GRID_POINTS = np.column_stack((GX.ravel(), GY.ravel()))
@dataclass(frozen=True)
class Level:
    name: str = "classic"
    well_rx: float = 330
    well_ry: float = 270
    floor_rx: float = 180
    floor_ry: float = 120
    rim_rx: float = 270
    rim_ry: float = 190
    floor: float = 80
    crest: float = 110
    extent: float = 650
    aquifer: Aquifer = Aquifer()
    day: float = 30

    @property
    def wells(self): return np.column_stack((self.well_rx*np.cos(ANGLE), self.well_ry*np.sin(ANGLE)))
    @property
    def controls(self): return np.vstack(([0,0],np.column_stack((self.floor_rx*np.cos(CP_ANGLE),self.floor_ry*np.sin(CP_ANGLE)))))
    @property
    def axis(self): return np.linspace(-self.extent,self.extent,35)
    @property
    def grid(self):
        x,y=np.meshgrid(self.axis,self.axis)
        return np.column_stack((x.ravel(),y.ravel()))
    @property
    def target(self): return self.floor-5

CLASSIC=Level()
SUPERPIT=Level("superpit",2140,1055,800,100,1890,805,-390,360,2600,
               Aquifer(.2,200,.001,-365,-900),365)
LEVELS={level.name:level for level in (CLASSIC,SUPERPIT)}
_lock = RLock()


def build_model(aquifer=Aquifer(), wells=WELLS, schedules=None, well_radius=0.15):
    """Construct actual interacting timflow elements. Schedules are absolute Q.

    Each well schedule is [(start_day, extraction_m3_per_day), ...].
    Multiple aquifers/boundary elements can later be introduced in this factory
    without changing the renderer or agent protocol.
    """
    wells = np.asarray(wells, dtype=float)
    if not np.isfinite(well_radius) or well_radius <= 0:
        raise ValueError("Well radius must be positive and finite")
    if wells.ndim != 2 or wells.shape[1] != 2 or not np.isfinite(wells).all():
        raise ValueError("Well coordinates must be finite (n,2)")
    if schedules is None:
        schedules = [[(0.0, 1.0)] for _ in wells]
    if len(schedules) != len(wells):
        raise ValueError("One pumping schedule per well is required")
    model = tft.ModelMaq(kaq=aquifer.conductivity,
                         z=[aquifer.roof, aquifer.roof - aquifer.thickness],
                         Saq=aquifer.storativity / aquifer.thickness,
                         topboundary="conf", tmin=TMIN, tmax=TMAX, M=15)
    for i, ((x, y), schedule) in enumerate(zip(wells, schedules)):
        steps = np.asarray(schedule, dtype=float)
        if steps.ndim != 2 or steps.shape[1] != 2 or len(steps) == 0:
            raise ValueError("Schedules must contain (day, rate) pairs")
        if not np.isfinite(steps).all() or (steps < 0).any() or (steps[:, 0] > TMAX).any():
            raise ValueError("Schedule times/rates must be finite and nonnegative")
        if steps[0, 0] != 0 or (np.diff(steps[:, 0]) <= 0).any():
            raise ValueError("Schedules start at day zero and increase strictly")
        tft.Well(model, xw=float(x), yw=float(y), rw=well_radius,
                 tsandQ=steps.tolist(), layers=0, label=f"W{i+1:02d}")
    model.solve(silent=True)
    return model


def heads(model, points, times, aquifer=Aquifer()):
    """Return (point, time) heads in m datum. Reject unsupported time lags."""
    points, times = np.asarray(points, float), np.atleast_1d(times).astype(float)
    if points.ndim != 2 or points.shape[1] != 2 or not np.isfinite(points).all():
        raise ValueError("Points must be finite (n,2)")
    if not np.isfinite(times).all() or (times < TMIN).any() or (times > TMAX).any():
        raise ValueError(f"Evaluation days must be in [{TMIN}, {TMAX}]")
    # Check tmin after every forcing change, including exact change times.
    for element in model.elementlist:
        if hasattr(element, "tstart"):
            for start in element.tstart:
                lag = times - start
                if ((lag >= 0) & (lag < TMIN)).any():
                    raise ValueError("Evaluation is too close to a pumping step")
    result = np.array([model.head(float(x), float(y), times, layers=[0])[0]
                       for x, y in points]) + aquifer.initial_head
    if not np.isfinite(result).all():
        raise ArithmeticError("Non-finite timflow result")
    return result


def _matrix(aquifer, points, day, level=CLASSIC):
    columns = []
    for well in level.wells:
        model = build_model(aquifer, [well], [[(0, 1000)]])
        columns.append((aquifer.initial_head - heads(model, points, [day], aquifer)[:, 0]) / 1000)
    result = np.column_stack(columns)
    result.setflags(write=False)
    return result


@lru_cache(maxsize=6)
def response(aquifer=Aquifer(), day=30.0, grid=True, level=CLASSIC):
    """Exact linear response basis from timflow, not a surrogate equation.

    Cached coefficients apply only to constant rates since day zero. General
    pumping histories use build_model/heads and timflow's time superposition.
    """
    if not np.isfinite(day) or not 0.1 <= day <= TMAX:
        raise ValueError("Scenario duration must be 0.1–365 days")
    points = np.vstack((level.controls, level.wells, level.grid)) if grid else level.controls
    with _lock:
        return _matrix(aquifer, points, day, level)


def validate_rates(rates):
    q = np.asarray(rates, float)
    if q.shape != (10,) or not np.isfinite(q).all() or (q < 0).any() or (q > QMAX).any():
        raise ValueError("Provide 10 finite extraction rates between 0 and 6000 m³/day")
    return q


def evaluate(rates, aquifer=Aquifer(), day=30.0, grid=True, level=CLASSIC):
    q = validate_rates(rates)
    matrix = response(aquifer, day, grid, level)
    h = aquifer.initial_head - matrix @ q
    result = {"control_heads": h[:len(CONTROL_POINTS)].tolist(),
              "worst_head": float(h[:len(CONTROL_POINTS)].max()),
              "rates": q.tolist(), "total_rate": float(q.sum()), "day": day,
              "target_head": level.target,
              "feasible": bool(h[:len(CONTROL_POINTS)].max() <= level.target + 1e-5),
              "confined_valid_at_samples": bool(h.min() > aquifer.roof),
              "engine": "timflow.transient 0.5.0"}
    if grid:
        result["well_heads"] = h[len(CONTROL_POINTS):len(CONTROL_POINTS)+10].tolist()
        result["surface"] = h[len(CONTROL_POINTS)+10:].reshape(GX.shape).tolist()
        result["axis"] = level.axis.tolist()
    return result
