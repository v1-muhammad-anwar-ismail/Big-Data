/**
 * =====================================================================
 * JinwooCrawl - PM2 Ecosystem Configuration for ARM Linux STB (2GB RAM)
 * =====================================================================
 * Kompatibel dengan Armbian / Ubuntu / Debian ARM64 & ARMv7 di STB:
 * - Memakai path absolut via __dirname agar aman dijalankan dari direktori mana saja (termasuk pm2 startup)
 * - Auto-deteksi venv Python (.venv / venv / python3 sistem)
 * - Static preview langsung memakai vite.js lokal tanpa npx/network overhead
 * - Batas memori aman untuk RAM STB 2GB selama proses crawling & MongoDB berjalan bersamaan
 */
const fs = require("fs");
const path = require("path");

function resolvePythonInterpreter() {
  const candidates = [
    path.resolve(__dirname, "backend/venv/bin/python3"),
    path.resolve(__dirname, "backend/.venv/bin/python3"),
    path.resolve(__dirname, "backend/venv/Scripts/python.exe"),
    path.resolve(__dirname, "backend/.venv/Scripts/python.exe"),
  ];
  for (const candidate of candidates) {
    if (fs.existsSync(candidate)) {
      return candidate;
    }
  }
  return "python3";
}

function buildBackendEnv() {
  const runtimeTmpDir = path.resolve(__dirname, ".pw-tmp");
  fs.mkdirSync(runtimeTmpDir, { recursive: true });
  const env = {
    APP_ENV: "production",
    PORT: 5002,
    HOST: "0.0.0.0",
    PYTHONUNBUFFERED: "1",
    PYTHONDONTWRITEBYTECODE: "1",
    TMPDIR: runtimeTmpDir,
    TEMP: runtimeTmpDir,
    TMP: runtimeTmpDir,
  };
  const localPwDir = path.resolve(__dirname, ".pw-browsers");
  if (fs.existsSync(localPwDir)) {
    env.PLAYWRIGHT_BROWSERS_PATH = localPwDir;
  }
  return env;
}

module.exports = {
  apps: [
    // -----------------------------------------------------------------
    // 1. BACKEND API (FastAPI / Uvicorn) - Port 5002 -> scrape.jinwoostream.lol
    // -----------------------------------------------------------------
    {
      name: "jinwoocrawl-backend",
      cwd: path.resolve(__dirname, "backend"),
      script: "run.py",
      interpreter: resolvePythonInterpreter(),
      interpreter_args: "-u",
      exec_mode: "fork",
      instances: 1,
      autorestart: true,
      watch: false,
      max_restarts: 10,
      restart_delay: 3000,
      max_memory_restart: "950M",
      env: buildBackendEnv(),
    },

    // -----------------------------------------------------------------
    // 2. FRONTEND STATIC SERVER - Port 5001 -> crawl.jinwoostream.lol
    // Memakai serve-dist.cjs (built-in Node.js http/fs, tanpa node_modules)
    // -----------------------------------------------------------------
    {
      name: "jinwoocrawl-frontend",
      cwd: path.resolve(__dirname, "frontend"),
      script: "serve-dist.cjs",
      exec_mode: "fork",
      instances: 1,
      autorestart: true,
      watch: false,
      max_restarts: 10,
      restart_delay: 2000,
      max_memory_restart: "120M",
      env: {
        NODE_ENV: "production",
        PORT: 5001,
        HOST: "0.0.0.0",
      },
    },
  ],
};
