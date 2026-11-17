import React from 'react';
import { Newspaper, Database, Server, Terminal, Settings } from 'lucide-react';
import { SystemHealth } from '../types';

interface HeaderProps {
  health: SystemHealth | null;
  onOpenConfig: () => void;
}

export const Header: React.FC<HeaderProps> = ({ health, onOpenConfig }) => {
  const isDbConnected = health?.database?.status === 'connected';

  return (
    <header className="sticky top-0 z-40 bg-[#090d16]/90 backdrop-blur-md border-b border-slate-800/80 px-4 lg:px-8 py-3.5 transition-all">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
        {/* Branding & Title */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-red-600 to-rose-900 flex items-center justify-center shadow-lg shadow-red-900/30 border border-red-500/30">
            <Newspaper className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xl font-extrabold tracking-tight text-white">
                Jinwoo<span className="text-red-500">Crawl</span>
              </span>
              <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-red-950/70 text-red-300 border border-red-800/50">
                News Intelligence
              </span>
            </div>
            <p className="text-xs text-slate-400 font-medium">
              Proyek Akhir Big Data 2026 • Siklus Hidup Isu Berita (Downs' 1972)
            </p>
          </div>
        </div>

        {/* System Indicators & Quick Actions */}
        <div className="flex flex-wrap items-center gap-3">
          {/* MongoDB Status */}
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-900/80 border border-slate-800 text-xs">
            <Database className="w-3.5 h-3.5 text-emerald-400" />
            <span className="text-slate-400">DB:</span>
            <span className="font-semibold text-slate-200">
              {health?.database?.database || 'jinwoo-crawl'}
            </span>
            <span className={`w-2 h-2 rounded-full ${isDbConnected ? 'bg-emerald-500 shadow-[0_0_6px_#10b981]' : 'bg-red-500'}`} />
          </div>

          {/* Backend Port & Host */}
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-900/80 border border-slate-800 text-xs">
            <Server className="w-3.5 h-3.5 text-blue-400" />
            <span className="text-slate-400">BE:</span>
            <span className="font-semibold text-blue-300">Port 5002</span>
          </div>

          {/* Swagger API Docs */}
          <a
            href="http://localhost:5002/docs"
            target="_blank"
            rel="noreferrer"
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800/80 hover:bg-slate-700/80 border border-slate-700 text-xs text-slate-200 font-medium transition-colors"
          >
            <Terminal className="w-3.5 h-3.5 text-slate-300" />
            <span>FastAPI Docs</span>
          </a>

          {/* Deployment Config Modal Button */}
          <button
            onClick={onOpenConfig}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-red-600/20 hover:bg-red-600/30 border border-red-500/40 text-xs text-red-300 font-medium transition-all"
          >
            <Settings className="w-3.5 h-3.5 text-red-400" />
            <span>Deployment (.env)</span>
          </button>
        </div>
      </div>
    </header>
  );
};
