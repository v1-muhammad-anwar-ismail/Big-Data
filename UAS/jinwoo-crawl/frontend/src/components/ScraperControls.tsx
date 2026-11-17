import React, { useState } from 'react';
import { Search, Play, RefreshCw, Trash2, ArrowRight } from 'lucide-react';

interface ScraperControlsProps {
  keyword: string;
  onKeywordChange: (val: string) => void;
  countPerTool: number;
  onCountChange: (val: number) => void;
  onRunAll: () => Promise<void>;
  onClear: () => Promise<void>;
  isLoading: boolean;
}

const PRESET_TOPICS = [
  { label: 'Karhutla & Bencana', value: 'karhutla', color: 'border-amber-600/40 text-amber-300 bg-amber-950/20' },
  { label: 'Isu Politik / Gibran', value: 'gibran mundur', color: 'border-blue-600/40 text-blue-300 bg-blue-950/20' },
  { label: 'IKN Nusantara', value: 'IKN Nusantara', color: 'border-emerald-600/40 text-emerald-300 bg-emerald-950/20' },
  { label: 'Pilkada Serentak', value: 'pilkada serentak', color: 'border-indigo-600/40 text-indigo-300 bg-indigo-950/20' },
  { label: 'Polusi Udara Jakarta', value: 'polusi udara', color: 'border-purple-600/40 text-purple-300 bg-purple-950/20' },
  { label: 'Inflasi & Daya Beli', value: 'inflasi pangan', color: 'border-cyan-600/40 text-cyan-300 bg-cyan-950/20' }
];

export const ScraperControls: React.FC<ScraperControlsProps> = ({
  keyword,
  onKeywordChange,
  countPerTool,
  onCountChange,
  onRunAll,
  onClear,
  isLoading
}) => {
  const [confirmClear, setConfirmClear] = useState(false);

  return (
    <div className="p-6 rounded-2xl bg-gradient-to-b from-slate-900/90 to-slate-950/90 border border-slate-800 shadow-xl mb-8 backdrop-blur-sm">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-800/80">
        <div>
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-red-500 animate-pulse" />
            Command Center Crawling Multikanal
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Ekstraksi paralel data isu dari berita & medsos untuk pemodelan <span className="text-slate-200 font-semibold">Issue Attention Cycle</span>
          </p>
        </div>

        {/* Action button clear dataset */}
        <div>
          {confirmClear ? (
            <div className="flex items-center gap-2">
              <span className="text-xs text-red-400 font-medium">Yakin hapus?</span>
              <button
                onClick={async () => {
                  await onClear();
                  setConfirmClear(false);
                }}
                className="px-2.5 py-1 text-xs font-bold rounded bg-red-600 text-white hover:bg-red-700 transition-colors"
              >
                Ya, Bersihkan DB
              </button>
              <button
                onClick={() => setConfirmClear(false)}
                className="px-2.5 py-1 text-xs rounded bg-slate-800 text-slate-300 hover:bg-slate-700 transition-colors"
              >
                Batal
              </button>
            </div>
          ) : (
            <button
              onClick={() => setConfirmClear(true)}
              disabled={isLoading}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-slate-400 hover:text-red-400 hover:bg-red-950/20 border border-slate-800 hover:border-red-900/40 transition-all"
            >
              <Trash2 className="w-3.5 h-3.5" />
              <span>Kosongkan MongoDB</span>
            </button>
          )}
        </div>
      </div>

      {/* Input controls */}
      <div className="mt-5 grid grid-cols-1 md:grid-cols-12 gap-4 items-center">
        {/* Keyword input */}
        <div className="md:col-span-7 relative">
          <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
            Target Kata Kunci Isu / Berita
          </label>
          <div className="relative">
            <Search className="w-4 h-4 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={keyword}
              onChange={(e) => onKeywordChange(e.target.value)}
              placeholder="Masukkan topik isu berita (misal: karhutla, gibran, pemilu, subsidi)..."
              disabled={isLoading}
              className="w-full pl-10 pr-4 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none focus:border-red-500 focus:ring-1 focus:ring-red-500 transition-all font-medium"
            />
          </div>
        </div>

        {/* Count target per tool */}
        <div className="md:col-span-2">
          <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
            Target Data / Tool
          </label>
          <input
            type="number"
            min={1}
            max={50}
            value={countPerTool}
            onChange={(e) => onCountChange(parseInt(e.target.value) || 5)}
            disabled={isLoading}
            className="w-full px-3 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-sm text-white text-center font-bold focus:outline-none focus:border-red-500 transition-all"
          />
        </div>

        {/* Unified Crawl Run Button */}
        <div className="md:col-span-3 pt-6 md:pt-5">
          <button
            onClick={onRunAll}
            disabled={isLoading || !keyword.trim()}
            className="w-full py-2.5 px-4 rounded-xl bg-gradient-to-r from-red-600 via-rose-600 to-red-700 hover:from-red-500 hover:to-red-600 text-white font-bold text-sm shadow-lg shadow-red-900/40 border border-red-500/50 flex items-center justify-center gap-2 transition-all disabled:opacity-50 disabled:cursor-not-allowed group"
          >
            {isLoading ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin text-white" />
                <span>Crawling 8 Tools...</span>
              </>
            ) : (
              <>
                <Play className="w-4 h-4 fill-white group-hover:translate-x-0.5 transition-transform" />
                <span>Jalankan 8 Scraper Sekaligus</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Preset Topics Quick Chips */}
      <div className="mt-4 pt-3 border-t border-slate-800/60 flex flex-wrap items-center gap-2">
        <span className="text-xs text-slate-400 font-medium">Rekomendasi Isu Siklus Cepat:</span>
        {PRESET_TOPICS.map((topic) => (
          <button
            key={topic.value}
            onClick={() => onKeywordChange(topic.value)}
            disabled={isLoading}
            className={`text-xs px-2.5 py-1 rounded-lg border font-medium transition-all hover:brightness-125 ${topic.color} ${
              keyword.toLowerCase() === topic.value.toLowerCase() ? 'ring-2 ring-red-500 font-bold' : ''
            }`}
          >
            {topic.label}
          </button>
        ))}
      </div>
    </div>
  );
};
