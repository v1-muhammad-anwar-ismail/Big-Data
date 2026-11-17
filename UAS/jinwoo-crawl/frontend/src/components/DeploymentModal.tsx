import React, { useState } from 'react';
import { X, Copy, Check, Server, Globe, Database, Shield } from 'lucide-react';

interface DeploymentModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const DeploymentModal: React.FC<DeploymentModalProps> = ({ isOpen, onClose }) => {
  const [copiedEnv, setCopiedEnv] = useState(false);
  const [copiedServer, setCopiedServer] = useState(false);

  if (!isOpen) return null;

  const envLocalContent = `# Local Development Environment (.env)
APP_NAME=JinwooCrawl
APP_ENV=local
PORT=5002
HOST=0.0.0.0
CORS_ORIGINS=http://localhost:5001,http://127.0.0.1:5001,https://crawl.jinwoostream.lol

MONGODB_URI=mongodb://localhost:27017/
MONGODB_DB_NAME=jinwoo-crawl
MONGODB_COLLECTION=api

# Scraper Credentials (Optional)
INSTAGRAM_USERNAME=
INSTAGRAM_PASSWORD=
TIKTOK_SESSION_KEY=
YOUTUBE_API_KEY=
META_ACCESS_TOKEN=`;

  const envServerContent = `# Production Server Environment (.env.server)
# Salin file ini menjadi .env di server saat deployment
APP_NAME=JinwooCrawl
APP_ENV=production
PORT=5002
HOST=0.0.0.0
CORS_ORIGINS=https://crawl.jinwoostream.lol,http://localhost:5001

MONGODB_URI=mongodb://localhost:27017/
MONGODB_DB_NAME=jinwoo-crawl
MONGODB_COLLECTION=api

# Scraper Credentials
INSTAGRAM_USERNAME=
INSTAGRAM_PASSWORD=
TIKTOK_SESSION_KEY=
YOUTUBE_API_KEY=
META_ACCESS_TOKEN=`;

  const handleCopy = (text: string, type: 'env' | 'server') => {
    navigator.clipboard.writeText(text);
    if (type === 'env') {
      setCopiedEnv(true);
      setTimeout(() => setCopiedEnv(false), 2000);
    } else {
      setCopiedServer(true);
      setTimeout(() => setCopiedServer(false), 2000);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fadeIn">
      <div className="w-full max-w-3xl rounded-2xl bg-slate-900 border border-slate-800 shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-slate-800 bg-slate-950/60">
          <div className="flex items-center gap-2.5">
            <Server className="w-5 h-5 text-red-500" />
            <div>
              <h3 className="text-base font-bold text-white">Panduan Konfigurasi & Deployment Cloudflare Tunnel</h3>
              <p className="text-xs text-slate-400">Sinkronisasi Port 5001 (FE) & Port 5002 (BE) ke domain produksi</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 overflow-y-auto space-y-6 text-xs text-slate-300">
          {/* Tunnel Route Card */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 p-4 rounded-xl bg-slate-950 border border-slate-800">
            <div className="space-y-1">
              <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Frontend Route (React .tsx)</span>
              <div className="flex items-center gap-2">
                <Globe className="w-4 h-4 text-emerald-400" />
                <span className="font-mono text-sm font-bold text-white">crawl.jinwoostream.lol</span>
              </div>
              <div className="text-[11px] text-slate-400">
                Service: <code className="text-emerald-400 font-mono">http://localhost:5001</code>
              </div>
            </div>

            <div className="space-y-1">
              <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Backend Route (FastAPI)</span>
              <div className="flex items-center gap-2">
                <Globe className="w-4 h-4 text-blue-400" />
                <span className="font-mono text-sm font-bold text-white">scrape.jinwoostream.lol</span>
              </div>
              <div className="text-[11px] text-slate-400">
                Service: <code className="text-blue-400 font-mono">http://localhost:5002</code>
              </div>
            </div>
          </div>

          {/* Database Info */}
          <div className="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800 flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <Database className="w-4 h-4 text-amber-400" />
              <div>
                <span className="font-bold text-white">Target Database:</span> MongoDB <code className="text-amber-400 font-mono">jinwoo-crawl</code>
              </div>
            </div>
            <span className="text-[11px] px-2 py-0.5 rounded bg-emerald-950/60 text-emerald-300 border border-emerald-800/40 font-mono">
              Collection: api
            </span>
          </div>

          {/* .env Files Display */}
          <div className="space-y-4">
            {/* .env local */}
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <span className="font-bold text-slate-200">1. File Lokal: <code className="text-red-400">backend/.env</code></span>
                <button
                  onClick={() => handleCopy(envLocalContent, 'env')}
                  className="flex items-center gap-1 text-[11px] text-slate-400 hover:text-white px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 transition-colors"
                >
                  {copiedEnv ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                  <span>{copiedEnv ? 'Tersalin' : 'Salin'}</span>
                </button>
              </div>
              <pre className="p-3 rounded-lg bg-black/60 border border-slate-800 font-mono text-[11px] text-slate-300 overflow-x-auto">
                {envLocalContent}
              </pre>
            </div>

            {/* .env.server */}
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <span className="font-bold text-slate-200">2. File Siap Deploy: <code className="text-emerald-400">backend/.env.server</code></span>
                <button
                  onClick={() => handleCopy(envServerContent, 'server')}
                  className="flex items-center gap-1 text-[11px] text-slate-400 hover:text-white px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 transition-colors"
                >
                  {copiedServer ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                  <span>{copiedServer ? 'Tersalin' : 'Salin'}</span>
                </button>
              </div>
              <pre className="p-3 rounded-lg bg-black/60 border border-slate-800 font-mono text-[11px] text-slate-300 overflow-x-auto">
                {envServerContent}
              </pre>
              <p className="text-[11px] text-slate-500 mt-1">
                Tip: Di VPS/Server, cukup jalankan perintah: <code className="text-slate-300 font-mono">cp .env.server .env</code> lalu jalankan service FastAPI.
              </p>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-slate-800 bg-slate-950 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-white transition-colors"
          >
            Tutup
          </button>
        </div>
      </div>
    </div>
  );
};
