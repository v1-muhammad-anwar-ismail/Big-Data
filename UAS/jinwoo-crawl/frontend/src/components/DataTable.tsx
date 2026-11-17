import React, { useState } from 'react';
import { Database, Download, Filter, ExternalLink, RefreshCw } from 'lucide-react';
import { ScrapedItem } from '../types';
import { CategoryBadge } from './CategoryBadge';
import { api } from '../services/api';

interface DataTableProps {
  items: ScrapedItem[];
  totalCount: number;
  onRefresh: () => void;
  isLoading: boolean;
  selectedTool: string;
  onSelectTool: (tool: string) => void;
  selectedCategory: string;
  onSelectCategory: (cat: string) => void;
}

export const DataTable: React.FC<DataTableProps> = ({
  items,
  totalCount,
  onRefresh,
  isLoading,
  selectedTool,
  onSelectTool,
  selectedCategory,
  onSelectCategory
}) => {
  const [searchTerm, setSearchTerm] = useState('');

  // Local filter
  const filteredItems = items.filter(item => {
    if (!searchTerm) return true;
    const term = searchTerm.toLowerCase();
    return (
      item.title.toLowerCase().includes(term) ||
      item.content.toLowerCase().includes(term) ||
      item.author_or_source.toLowerCase().includes(term)
    );
  });

  return (
    <div className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-xl backdrop-blur-sm">
      {/* Table Header & Export Buttons */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pb-5 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <Database className="w-5 h-5 text-red-500" />
            <h3 className="text-lg font-bold text-white">
              Dataset Ingestion Explorer (MongoDB: <code className="text-red-400 font-mono text-sm">jinwoo-crawl.api</code>)
            </h3>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Data mentah siap diekspor ke Hadoop HDFS untuk diproses menggunakan Apache Spark SQL & Spark MLlib
          </p>
        </div>

        {/* Export & Refresh Actions */}
        <div className="flex flex-wrap items-center gap-2.5">
          <button
            onClick={onRefresh}
            disabled={isLoading}
            className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs text-slate-200 font-medium border border-slate-700 transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
            <span>Segarkan</span>
          </button>

          {/* Export JSON for HDFS */}
          <a
            href={api.getExportJsonUrl()}
            target="_blank"
            rel="noreferrer"
            download="jinwoo_crawl_dataset.json"
            className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-blue-600/20 hover:bg-blue-600/30 text-blue-300 text-xs font-semibold border border-blue-500/40 transition-all shadow-sm"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Ekspor JSON (HDFS)</span>
          </a>

          {/* Export CSV for Spark DataFrame */}
          <a
            href={api.getExportCsvUrl()}
            target="_blank"
            rel="noreferrer"
            download="jinwoo_crawl_dataset.csv"
            className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-300 text-xs font-semibold border border-emerald-500/40 transition-all shadow-sm"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Ekspor CSV (Spark MLlib)</span>
          </a>
        </div>
      </div>

      {/* Filter Toolbar */}
      <div className="mt-5 flex flex-wrap items-center justify-between gap-3 bg-slate-950/60 p-3 rounded-xl border border-slate-800/80">
        <div className="flex flex-wrap items-center gap-3">
          {/* Tool Source Filter */}
          <div className="flex items-center gap-2 text-xs">
            <Filter className="w-3.5 h-3.5 text-slate-400" />
            <span className="text-slate-400 font-medium">Tool:</span>
            <select
              value={selectedTool}
              onChange={(e) => onSelectTool(e.target.value)}
              className="bg-slate-900 border border-slate-700 rounded-lg px-2.5 py-1 text-xs text-white focus:outline-none focus:border-red-500"
            >
              <option value="all">Semua 8 Tools</option>
              <option value="gdelt">GDELT 2.0</option>
              <option value="tiktok_search">TikTok Search</option>
              <option value="pyktok">Pyktok Academic</option>
              <option value="facebook_pages">Facebook Pages</option>
              <option value="instaloader">Instaloader (IG)</option>
              <option value="tiktok_api">TikTok-Api (Teather)</option>
              <option value="youtube_api">YouTube Data API</option>
              <option value="meta_ad_library">Meta Ad Library</option>
            </select>
          </div>

          {/* Category Filter */}
          <div className="flex items-center gap-2 text-xs">
            <span className="text-slate-400 font-medium">Kategori:</span>
            <select
              value={selectedCategory}
              onChange={(e) => onSelectCategory(e.target.value)}
              className="bg-slate-900 border border-slate-700 rounded-lg px-2.5 py-1 text-xs text-white focus:outline-none focus:border-red-500"
            >
              <option value="all">Semua Kategori</option>
              <option value="Disaster">Bencana / Karhutla</option>
              <option value="Politics">Politik / Nasional</option>
              <option value="Economy">Ekonomi / Bisnis</option>
              <option value="Technology">Teknologi / Data</option>
              <option value="Social">Sosial & Budaya</option>
              <option value="News">Berita Utama</option>
            </select>
          </div>
        </div>

        {/* Quick Search in Table */}
        <div className="w-full sm:w-64">
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Cari dalam hasil tabel..."
            className="w-full px-3 py-1.5 bg-slate-900 border border-slate-700 rounded-lg text-xs text-white placeholder-slate-500 focus:outline-none focus:border-red-500"
          />
        </div>
      </div>

      {/* Table Content */}
      <div className="mt-4 overflow-x-auto rounded-xl border border-slate-800">
        <table className="w-full text-left border-collapse text-xs">
          <thead>
            <tr className="bg-slate-950/80 border-b border-slate-800 text-slate-400 font-semibold uppercase tracking-wider">
              <th className="py-3 px-4">Sumber & Platform</th>
              <th className="py-3 px-4">Kategori</th>
              <th className="py-3 px-4">Judul / Cuplikan Konten</th>
              <th className="py-3 px-4">Metrik Keterlibatan</th>
              <th className="py-3 px-4">Tanggal Publikasi</th>
              <th className="py-3 px-4 text-center">Tautan</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 font-medium">
            {filteredItems.length === 0 ? (
              <tr>
                <td colSpan={6} className="py-12 text-center text-slate-500">
                  <div className="flex flex-col items-center justify-center gap-2">
                    <Database className="w-8 h-8 text-slate-600" />
                    <span>Belum ada data untuk filter ini. Silakan jalankan salah satu scraper di atas.</span>
                  </div>
                </td>
              </tr>
            ) : (
              filteredItems.map((item) => (
                <tr key={item.id} className="hover:bg-slate-800/40 transition-colors group">
                  {/* Source */}
                  <td className="py-3 px-4 whitespace-nowrap">
                    <div className="font-bold text-white">{item.author_or_source}</div>
                    <div className="text-[11px] text-slate-400 font-mono flex items-center gap-1 mt-0.5">
                      <span className="w-1.5 h-1.5 rounded-full bg-slate-500" />
                      <span>{item.tool_source}</span> • <span className="text-slate-300">{item.platform}</span>
                    </div>
                  </td>

                  {/* Category */}
                  <td className="py-3 px-4 whitespace-nowrap">
                    <CategoryBadge category={item.category} />
                  </td>

                  {/* Title & snippet */}
                  <td className="py-3 px-4 max-w-md">
                    <div className="font-semibold text-slate-200 line-clamp-1 group-hover:text-red-400 transition-colors">
                      {item.title}
                    </div>
                    <div className="text-slate-400 line-clamp-2 text-[11px] mt-0.5 leading-relaxed">
                      {item.content}
                    </div>
                  </td>

                  {/* Metrics */}
                  <td className="py-3 px-4 whitespace-nowrap">
                    <div className="flex items-center gap-2 font-mono text-[11px]">
                      {item.metrics.views > 0 && (
                        <span className="text-slate-300">
                          {item.metrics.views.toLocaleString()} <span className="text-slate-500 text-[10px]">views</span>
                        </span>
                      )}
                      {item.metrics.likes > 0 && (
                        <span className="text-rose-400">
                          {item.metrics.likes.toLocaleString()} <span className="text-slate-500 text-[10px]">likes</span>
                        </span>
                      )}
                      {item.metrics.comments > 0 && (
                        <span className="text-blue-400">
                          {item.metrics.comments.toLocaleString()} <span className="text-slate-500 text-[10px]">cmts</span>
                        </span>
                      )}
                    </div>
                    <div className="text-[10px] text-slate-400 mt-0.5">
                      Tone sentimen: <span className="text-amber-400 font-mono">{item.metrics.sentiment_tone}</span>
                    </div>
                  </td>

                  {/* Date */}
                  <td className="py-3 px-4 whitespace-nowrap text-slate-400 font-mono text-[11px]">
                    {item.published_date || item.published_at?.substring(0, 10)}
                  </td>

                  {/* Link */}
                  <td className="py-3 px-4 text-center whitespace-nowrap">
                    {item.url ? (
                      <a
                        href={item.url}
                        target="_blank"
                        rel="noreferrer"
                        className="p-1.5 rounded-lg bg-slate-800 text-slate-300 hover:text-white hover:bg-slate-700 inline-flex items-center justify-center transition-colors"
                      >
                        <ExternalLink className="w-3.5 h-3.5" />
                      </a>
                    ) : (
                      <span className="text-slate-600">-</span>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Footer Counter */}
      <div className="mt-4 flex items-center justify-between text-xs text-slate-400">
        <span>Menampilkan {filteredItems.length} dari {totalCount} total dokumen</span>
        <span className="text-[11px] text-slate-500 font-mono">Collection: jinwoo-crawl.api</span>
      </div>
    </div>
  );
};
