import React from 'react';
import { Globe, Video, Facebook, Instagram, Youtube, Megaphone, Play, RefreshCw, Key } from 'lucide-react';
import { ScraperTool } from '../types';

interface ScrapersGridProps {
  tools: ScraperTool[];
  onRunSingle: (toolId: string) => Promise<void>;
  loadingTool: string | null;
  keyword: string;
}

export const ScrapersGrid: React.FC<ScrapersGridProps> = ({
  tools,
  onRunSingle,
  loadingTool,
  keyword
}) => {
  const getPlatformIcon = (platform: string) => {
    switch (platform.toLowerCase()) {
      case 'global news media':
      case 'news':
        return <Globe className="w-4 h-4 text-emerald-400" />;
      case 'tiktok':
        return <Video className="w-4 h-4 text-cyan-400" />;
      case 'facebook':
        return <Facebook className="w-4 h-4 text-blue-400" />;
      case 'instagram':
        return <Instagram className="w-4 h-4 text-pink-400" />;
      case 'youtube':
        return <Youtube className="w-4 h-4 text-red-400" />;
      case 'meta ads (fb & ig)':
      case 'metaads':
        return <Megaphone className="w-4 h-4 text-purple-400" />;
      default:
        return <Globe className="w-4 h-4 text-slate-400" />;
    }
  };

  return (
    <div className="mb-8">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            <span>Daftar 8 Tool & API Scraping Mandiri</span>
            <span className="text-xs px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
              100% Free / Open Source
            </span>
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Setiap tool dapat diuji coba secara mandiri untuk demonstrasi pengumpulan data di depan dosen penguji
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {tools.map((tool) => {
          const isThisLoading = loadingTool === tool.id;

          return (
            <div
              key={tool.id}
              className="p-4 rounded-xl bg-slate-900/70 border border-slate-800 hover:border-slate-700 transition-all flex flex-col justify-between group hover:shadow-lg hover:shadow-black/40"
            >
              <div>
                {/* Header card */}
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-1.5 px-2 py-1 rounded-md bg-slate-800/80 border border-slate-700/60 text-[11px] font-semibold text-slate-200">
                    {getPlatformIcon(tool.platform)}
                    <span>{tool.platform}</span>
                  </div>
                  {tool.auth_required && (
                    <span className="inline-flex items-center gap-1 text-[10px] text-amber-400 font-medium bg-amber-950/30 px-1.5 py-0.5 rounded border border-amber-800/40">
                      <Key className="w-2.5 h-2.5" />
                      .env Auth
                    </span>
                  )}
                </div>

                {/* Name */}
                <h4 className="text-sm font-bold text-white group-hover:text-red-400 transition-colors">
                  {tool.name}
                </h4>

                {/* Description */}
                <p className="text-xs text-slate-400 mt-1.5 line-clamp-3 leading-relaxed">
                  {tool.description}
                </p>

                {/* Auth status tag */}
                <div className="mt-3">
                  <span className="inline-block text-[10px] font-semibold text-slate-400 bg-slate-950 px-2 py-0.5 rounded border border-slate-800">
                    Status: <span className="text-slate-200">{tool.auth_status}</span>
                  </span>
                </div>
              </div>

              {/* Action Button */}
              <div className="mt-4 pt-3 border-t border-slate-800/80">
                <button
                  onClick={() => onRunSingle(tool.id)}
                  disabled={Boolean(loadingTool)}
                  className="w-full py-1.5 px-3 rounded-lg bg-slate-800 hover:bg-red-950/40 text-slate-200 hover:text-red-300 border border-slate-700 hover:border-red-800/50 text-xs font-semibold flex items-center justify-center gap-1.5 transition-all disabled:opacity-50"
                >
                  {isThisLoading ? (
                    <>
                      <RefreshCw className="w-3.5 h-3.5 animate-spin text-red-400" />
                      <span>Mengambil Data...</span>
                    </>
                  ) : (
                    <>
                      <Play className="w-3.5 h-3.5 fill-current" />
                      <span>Crawl '{keyword}'</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
