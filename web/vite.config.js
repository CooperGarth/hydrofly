import {defineConfig} from 'vite';
import {resolve} from 'node:path';
export default defineConfig({server:{host:'0.0.0.0',allowedHosts:['terminal.local'],proxy:{'/api':'http://127.0.0.1:8000'}},build:{rollupOptions:{input:{main:resolve(import.meta.dirname,'index.html'),classic:resolve(import.meta.dirname,'classic.html')}}}});
