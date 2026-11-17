/**
 * =====================================================================
 * JinwooCrawl - PM2 Ecosystem Configuration for STB (ARM Linux / 2GB RAM)
 * =====================================================================
 * Menjalankan Backend FastAPI dan Static Frontend secara efisien,
 * terisolasi, dan hemat memori pada perangkat STB.
 */

module.exports = {
  apps: [
    // -----------------------------------------------------------------
    // 1. BACKEND API (FastAPI / Uvicorn) - Port 5002
    // -----------------------------------------------------------------
    {
      name: "jinwoocrawl-backend",
      cwd: "./backend",
      script: "run.py",
      interpreter: "python3", // atau arahkan ke venv: "./backend/venv/bin/python3"
      args: "",
      instances: 1, // 1 instance/worker sangat ideal untuk STB 2GB RAM agar hemat memori
      autorestart: true,
      watch: false,
      max_memory_restart: "150M", // Otomatis restart jika memori melewati 150MB
      env: {
        APP_ENV: "production",
        PORT: 5002,
        HOST: "0.0.0.0"
      }
    },

    // -----------------------------------------------------------------
    // 2. FRONTEND STATIC SERVER - Port 5001
    // (Digunakan jika Cloudflare Tunnel memetakan http://localhost:5001)
    // Catatan: Jika menggunakan Nginx langsung sebagai web server,
    // blok ini opsional karena Nginx sudah melayani folder frontend/dist
    // -----------------------------------------------------------------
    {
      name: "jinwoocrawl-frontend",
      cwd: "./frontend",
      script: "npx",
      args: "serve -s dist -l 5001",
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: "80M",
      env: {
        NODE_ENV: "production"
      }
    }
  ]
};
