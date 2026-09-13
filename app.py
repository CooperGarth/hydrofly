"""Vercel FastAPI entrypoint. Native Python keeps timflow and Numba intact."""
import os
import sys
from pathlib import Path
os.environ.setdefault('NUMBA_CACHE_DIR','/tmp/hydrofly-numba')
os.environ.setdefault('MPLCONFIGDIR','/tmp/hydrofly-matplotlib')
os.environ.setdefault('HYDROFLY_SKIP_WARMUP','1')
sys.path.insert(0,str(Path(__file__).parent/'src'))
from hydrofly.api import app
