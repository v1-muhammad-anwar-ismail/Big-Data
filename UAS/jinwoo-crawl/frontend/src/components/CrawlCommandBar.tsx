import React, { useState, useRef, useEffect } from 'react';
import { Search, Play, Filter, Download, Trash2, RefreshCw, X, ChevronDown, Hash, Calendar } from 'lucide-react';
import { api } from '../services/api';

export interface ToolOption {
  id: string;
  name: string;
  platform: string;
}

export const ALL_TOOLS: ToolOption[] = [
  { id: 'gdelt', name: 'GDELT 2.0 & Berita ID', platform: 'GDELT Master + Multi-Portal Berita' },
  { id: 'tiktok_search', name: 'TikTok Web Search', platform: 'TikTok Publik' },
  { id: 'pyktok', name: 'dfreelon/pyktok', platform: 'Riset Akademik TikTok' },
  { id: 'facebook_pages', name: 'Facebook Pages Scraper', platform: 'Fanpage FB Media' },
  { id: 'instaloader', name: 'Instaloader', platform: 'Instagram' },
  { id: 'tiktok_api', name: 'davidteather/TikTok-Api', platform: 'TikTok API Akun' },
  { id: 'youtube_api', name: 'YouTube Data API v3', platform: 'YouTube Video & Komentar' }
];

interface CrawlCommandBarProps {
  keyword: string;
  onKeywordChange: (val: string) => void;
  selectedTools: string[];
  onSelectedToolsChange: (tools: string[]) => void;
  countPerTool: number;
  onCountChange: (count: number) => void;
  yearRange: number;
  onYearRangeChange: (yr: number) => void;
  onStartCrawl: () => Promise<void>;
  onClearDb: () => Promise<void>;
  isLoading: boolean;
  totalDocs: number;
}

export const CrawlCommandBar: React.FC<CrawlCommandBarProps> = ({
  keyword,
  onKeywordChange,
  selectedTools,
  onSelectedToolsChange,
  countPerTool,
  onCountChange,
  yearRange,
  onYearRangeChange,
  onStartCrawl,
  onClearDb,
  isLoading,
  totalDocs
}) => {
  const [isFilterOpen, setIsFilterOpen] = useState(false);
  const [showClearConfirm, setShowClearConfirm] = useState(false);
  const filterRef = useRef<HTMLDivElement>(null);

  // Close filter dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (filterRef.current && !filterRef.current.contains(e.target as Node)) {
        setIsFilterOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const toggleTool = (toolId: string) => {
    if (selectedTools.includes(toolId)) {
      onSelectedToolsChange(selectedTools.filter(id => id !== toolId));
    } else {
      onSelectedToolsChange([...selectedTools, toolId]);
    }
  };

  const selectAll = () => {
    onSelectedToolsChange(ALL_TOOLS.map(t => t.id));
  };

  const clearAll = () => {
    onSelectedToolsChange([]);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (keyword.trim() && selectedTools.length > 0 && !isLoading) {
      onStartCrawl();
    }
  };

  return (
    <div className="w-full mb-6">
      <form onSubmit={handleSubmit} className="flex flex-col gap-3">
        {/* BARIS PERTAMA: Kolom Search & Filter Sumber */}
        {/* Di mobile: 1 baris 1 komponen murni (w-full stack) */}
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2.5">
          {/* Kolom Search Input */}
          <div className="relative flex-1 w-full">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
            <input
              type="text"
              value={keyword}
              onChange={(e) => onKeywordChange(e.target.value)}
              placeholder="Masukkan kata kunci isu/berita (contoh: karhutla, gibran mundur, pemilu)..."
              disabled={isLoading}
              required
              className="w-full pl-10 pr-9 py-2.5 bg-slate-900 border border-slate-800 rounded-xl text-sm text-white placeholder-slate-500 focus:outline-none focus:border-red-500 font-medium transition-colors"
            />
            {keyword && !isLoading && (
              <button
                type="button"
                onClick={() => onKeywordChange('')}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300"
              >
                <X className="w-4 h-4" />
              </button>
            )}
          </div>

          {/* Filter Sumber Button (1 Tombol Menyatukan 7 Tool dengan Checklist) */}
          <div className="relative w-full sm:w-auto shrink-0" ref={filterRef}>
            <button
              type="button"
              onClick={() => setIsFilterOpen(!isFilterOpen)}
              disabled={isLoading}
              className={`w-full sm:w-auto flex items-center justify-between sm:justify-start gap-2 px-4 py-2.5 rounded-xl border text-xs font-semibold transition-all ${
                selectedTools.length > 0
                  ? 'bg-slate-900 hover:bg-slate-800 border-slate-800 text-white'
                  : 'bg-red-950/40 border-red-800/60 text-red-300'
              }`}
            >
              <div className="flex items-center gap-2">
                <Filter className="w-3.5 h-3.5 text-red-400" />
                <span>Filter Sumber:</span>
                <span className="px-1.5 py-0.5 rounded bg-red-600 text-white font-bold text-[10px]">
                  {selectedTools.length}/{ALL_TOOLS.length}
                </span>
              </div>
              <ChevronDown className={`w-3.5 h-3.5 transition-transform ${isFilterOpen ? 'rotate-180' : ''}`} />
            </button>

            {/* Dropdown Menu Checklist */}
            {isFilterOpen && (
              <div className="absolute left-0 sm:right-0 sm:left-auto top-full mt-2 w-full sm:w-80 bg-slate-950 border border-slate-800 rounded-2xl shadow-2xl p-3.5 z-50 animate-fadeIn">
                <div className="flex items-center justify-between pb-2.5 mb-2.5 border-b border-slate-800 text-xs font-bold text-white">
                  <span>Pilih 7 Tool Scraping</span>
                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      onClick={selectAll}
                      className="text-[11px] text-red-400 hover:underline font-semibold"
                    >
                      Pilih Semua
                    </button>
                    <span className="text-slate-600">|</span>
                    <button
                      type="button"
                      onClick={clearAll}
                      className="text-[11px] text-slate-400 hover:underline"
                    >
                      Kosongkan
                    </button>
                  </div>
                </div>

                <div className="space-y-1.5 max-h-64 overflow-y-auto pr-1">
                  {ALL_TOOLS.map((t) => {
                    const isChecked = selectedTools.includes(t.id);
                    return (
                      <label
                        key={t.id}
                        className={`flex items-start gap-2.5 p-2 rounded-xl cursor-pointer text-xs transition-colors ${
                          isChecked
                            ? 'bg-slate-900 border border-slate-800 text-white'
                            : 'hover:bg-slate-900/50 text-slate-400'
                        }`}
                      >
                        <input
                          type="checkbox"
                          checked={isChecked}
                          onChange={() => toggleTool(t.id)}
                          className="mt-0.5 rounded border-slate-700 text-red-600 focus:ring-0 cursor-pointer"
                        />
                        <div className="min-w-0">
                          <div className="font-semibold text-slate-200 truncate">{t.name}</div>
                          <div className="text-[10px] text-slate-500 truncate">{t.platform}</div>
                        </div>
                      </label>
                    );
                  })}
                </div>

                <div className="pt-2.5 mt-2.5 border-t border-slate-800 flex justify-end">
                  <button
                    type="button"
                    onClick={() => setIsFilterOpen(false)}
                    className="px-3.5 py-1 bg-red-600 hover:bg-red-500 text-white text-xs font-bold rounded-lg transition-colors"
                  >
                    Terapkan ({selectedTools.length})
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* BARIS KEDUA: Target Volume (Input Angka Langsung) + Button Mulai Crawling + Export + Kosongkan */}
        {/* Di mobile: STRICTLY 1 COMPONENT PER LINE (w-full vertical stack) */}
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-2.5">
          <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2.5 w-full sm:w-auto">
            {/* Target Volume INPUT ANGKA (Tanpa Toggle Atas-Bawah, Lebih Leluasa) */}
            <div className="flex items-center gap-2 px-3.5 py-2 bg-slate-900 border border-slate-800 rounded-xl text-xs text-slate-300 w-full sm:w-auto">
              <Hash className="w-3.5 h-3.5 text-slate-400 shrink-0" />
              <span className="text-slate-400 text-xs shrink-0 font-medium">Target / tool:</span>
              <input
                type="number"
                min={1}
                max={50000}
                value={countPerTool}
                onChange={(e) => onCountChange(Math.max(1, parseInt(e.target.value) || 1))}
                disabled={isLoading}
                title="Ketikkan jumlah target data per tool (contoh: 25, 100, 500, 50000)"
                className="w-full sm:w-24 bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1 text-white font-bold text-xs focus:outline-none focus:border-red-500 [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
              />
            </div>

            {/* Rentang Tahun (1 - 5 Tahun Terakhir) */}
            <div className="flex items-center gap-2 px-3 py-2 bg-slate-900 border border-slate-800 rounded-xl text-xs text-slate-300 w-full sm:w-auto">
              <Calendar className="w-3.5 h-3.5 text-slate-400 shrink-0" />
              <span className="text-slate-400 text-xs shrink-0 font-medium">Rentang:</span>
              <select
                value={yearRange}
                onChange={(e) => onYearRangeChange(parseInt(e.target.value) || 5)}
                disabled={isLoading}
                style={{ appearance: 'none', WebkitAppearance: 'none', MozAppearance: 'none' }}
                className="appearance-none bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1 text-white font-bold text-xs focus:outline-none focus:border-red-500 cursor-pointer w-full sm:w-auto"
                title="Pilih rentang tahun agar berita tidak usang/ampas"
              >
                <option value={5}>5 Tahun (2021 - 2026)</option>
                <option value={3}>3 Tahun (2023 - 2026)</option>
                <option value={2}>2 Tahun (2024 - 2026)</option>
                <option value={1}>1 Tahun (2025 - 2026)</option>
              </select>
            </div>

            {/* Button Mulai Crawling */}
            <button
              type="submit"
              disabled={isLoading || !keyword.trim() || selectedTools.length === 0}
              className="w-full sm:w-auto flex items-center justify-center gap-2 px-6 py-2.5 bg-red-600 hover:bg-red-500 active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed text-white text-xs font-extrabold rounded-xl transition-all shadow-md shrink-0"
            >
              {isLoading ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span>Memproses Data...</span>
                </>
              ) : (
                <>
                  <Play className="w-4 h-4 fill-white" />
                  <span>Mulai Crawling</span>
                </>
              )}
            </button>

            {/* Export CSV (Spark MLlib) */}
            <a
              href={api.getExportCsvUrl()}
              target="_blank"
              rel="noreferrer"
              download="dataset_bigdata.csv"
              className="w-full sm:w-auto flex items-center justify-center gap-1.5 px-3.5 py-2.5 rounded-xl bg-emerald-600/20 hover:bg-emerald-600/30 border border-emerald-500/50 text-emerald-300 text-xs font-bold transition-all"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Unduh .CSV (Spark MLlib)</span>
            </a>

            {/* Export JSON (HDFS) */}
            <a
              href={api.getExportJsonUrl()}
              target="_blank"
              rel="noreferrer"
              download="dataset_bigdata.json"
              className="w-full sm:w-auto flex items-center justify-center gap-1.5 px-3.5 py-2.5 rounded-xl bg-blue-600/20 hover:bg-blue-600/30 border border-blue-500/50 text-blue-300 text-xs font-bold transition-all"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Unduh .JSON (HDFS)</span>
            </a>
          </div>

          {/* Tombol Kosongkan! */}
          <div className="w-full sm:w-auto flex justify-end">
            {showClearConfirm ? (
              <div className="w-full sm:w-auto flex items-center justify-between sm:justify-start gap-2 bg-red-950/80 px-3 py-2 rounded-xl border border-red-800 text-xs">
                <span className="text-red-300">Yakin kosongkan?</span>
                <div className="flex items-center gap-1.5">
                  <button
                    type="button"
                    onClick={async () => {
                      await onClearDb();
                      setShowClearConfirm(false);
                    }}
                    className="px-2.5 py-1 rounded bg-red-600 text-white font-bold hover:bg-red-500 transition-colors"
                  >
                    Ya
                  </button>
                  <button
                    type="button"
                    onClick={() => setShowClearConfirm(false)}
                    className="px-2.5 py-1 rounded bg-slate-800 text-slate-300 hover:bg-slate-700 transition-colors"
                  >
                    Batal
                  </button>
                </div>
              </div>
            ) : (
              <button
                type="button"
                onClick={() => setShowClearConfirm(true)}
                disabled={isLoading || totalDocs === 0}
                className="w-full sm:w-auto flex items-center justify-center gap-1.5 px-3 py-2 rounded-xl text-xs text-slate-400 hover:text-red-400 hover:bg-slate-900 border border-transparent hover:border-slate-800 transition-colors disabled:opacity-40"
              >
                <Trash2 className="w-3.5 h-3.5" />
                <span>Kosongkan!</span>
              </button>
            )}
          </div>
        </div>
      </form>
    </div>
  );
};
