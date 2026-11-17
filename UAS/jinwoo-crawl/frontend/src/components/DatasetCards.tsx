import React, { useState, useEffect, useMemo } from 'react';
import { Download, RefreshCw, Search, Eye, Heart, MessageCircle, Share2, Layers, ChevronLeft, ChevronRight } from 'lucide-react';
import { ScrapedItem } from '../types';
import { CategoryBadge } from './CategoryBadge';
import { api } from '../services/api';

interface DatasetCardsProps {
  items: ScrapedItem[];
  totalCount: number;
  onRefresh: () => void;
  isLoading: boolean;
  isFetching?: boolean;
  selectedTool: string;
  onSelectTool: (tool: string) => void;
  selectedCategory: string;
  onSelectCategory: (cat: string) => void;
  selectedYear: string;
  onSelectYear: (yr: string) => void;
  onSelectItem: (item: ScrapedItem) => void;
}

const PLATFORM_FILTERS = [
  { id: 'all', label: 'Semua Platform' },
  { id: 'gdelt', label: 'GDELT News' },
  { id: 'tiktok_search', label: 'TikTok Web' },
  { id: 'tiktok_api', label: 'TikTok API' },
  { id: 'pyktok', label: 'Pyktok' },
  { id: 'youtube', label: 'YouTube' },
  { id: 'instagram', label: 'Instagram' },
  { id: 'facebook', label: 'Facebook' }
];

export const DatasetCards: React.FC<DatasetCardsProps> = ({
  items,
  totalCount,
  onRefresh,
  isLoading,
  isFetching = false,
  selectedTool,
  onSelectTool,
  selectedCategory,
  onSelectCategory,
  selectedYear,
  onSelectYear,
  onSelectItem
}) => {
  const [searchFilter, setSearchFilter] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [failedThumbs, setFailedThumbs] = useState<Record<string, boolean>>({});
  const [pageSize, setPageSize] = useState(() => (typeof window !== 'undefined' && window.innerWidth < 640 ? 10 : 20));

  // Handle responsive page size (10 for mobile, 20 for desktop)
  useEffect(() => {
    const handleResize = () => {
      setPageSize(window.innerWidth < 640 ? 10 : 20);
    };
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const matchesToolFilter = (item: ScrapedItem, filterId: string): boolean => {
    if (filterId === 'all') return true;
    const tool = (item.tool_source || '').toLowerCase();
    const plat = (item.platform || '').toLowerCase();
    switch (filterId) {
      case 'gdelt':
        return tool === 'gdelt';
      case 'tiktok_search':
        return tool === 'tiktok_search';
      case 'tiktok_api':
        return tool === 'tiktok_api';
      case 'pyktok':
        return tool === 'pyktok';
      case 'youtube':
        return tool === 'youtube_api' || tool === 'youtube' || plat === 'youtube';
      case 'instagram':
        return tool === 'instaloader' || tool === 'instagram' || plat === 'instagram';
      case 'facebook':
        return tool === 'facebook_pages' || tool === 'facebook' || plat === 'facebook';
      default:
        return tool === filterId;
    }
  };

  // Deduplicate cards defensively by canonical URL and normalized content key
  const uniqueItems = useMemo(() => {
    const seenUrls = new Set<string>();
    const seenFingerprints = new Set<string>();
    const out: ScrapedItem[] = [];
    for (const item of items) {
      if ((item.tool_source || '').toLowerCase() === 'meta_ad_library') continue;
      const cleanUrl = (item.url || '').split('#')[0].replace(/\/+$/, '').toLowerCase();
      if (cleanUrl && seenUrls.has(cleanUrl)) continue;
      const cleanTitle = (item.title || '')
        .replace(/^(?:TikTok API|TikTok|Pyktok)\s+/i, '')
        .toLowerCase()
        .replace(/\s+/g, ' ')
        .trim();
      const author = (item.author_or_source || '').toLowerCase().trim();
      const snippet = (item.content || '').toLowerCase().replace(/\s+/g, ' ').trim().slice(0, 120);
      const fp = `${author}|${cleanTitle}|${snippet}`;
      if (fp !== '||' && seenFingerprints.has(fp)) continue;
      if (cleanUrl) seenUrls.add(cleanUrl);
      if (fp !== '||') seenFingerprints.add(fp);
      out.push(item);
    }
    return out;
  }, [items]);

  // Filter items locally by tool, category, year, and search query (strict client-side guard)
  const filteredItems = uniqueItems.filter(item => {
    if (!matchesToolFilter(item, selectedTool)) return false;
    if (selectedCategory !== 'all' && (item.category || '').toLowerCase() !== selectedCategory.toLowerCase()) {
      return false;
    }
    if (selectedYear !== 'all') {
      const itemDate = item.published_date || item.published_at || '';
      if (!itemDate.startsWith(selectedYear)) return false;
    }
    if (!searchFilter.trim()) return true;
    const q = searchFilter.toLowerCase();
    return (
      (item.title && item.title.toLowerCase().includes(q)) ||
      (item.content && item.content.toLowerCase().includes(q)) ||
      (item.author_or_source && item.author_or_source.toLowerCase().includes(q)) ||
      (item.keyword && item.keyword.toLowerCase().includes(q)) ||
      (item.tool_source && item.tool_source.toLowerCase().includes(q))
    );
  });

  // Reset to page 1 whenever search or filter changes
  useEffect(() => {
    setCurrentPage(1);
  }, [searchFilter, selectedTool, selectedCategory, selectedYear, items.length]);

  const totalPages = Math.max(1, Math.ceil(filteredItems.length / pageSize));
  const startIndex = (currentPage - 1) * pageSize;
  const paginatedItems = filteredItems.slice(startIndex, startIndex + pageSize);

  return (
    <div className="w-full mb-10 font-['Plus_Jakarta_Sans',sans-serif]">
      {/* Title & Info Section: "27 dari 27 Data" ditaruh di baris berikutnya */}
      <div className="flex flex-col gap-1 pb-3 mb-4 border-b border-slate-800/80">
        <h3 className="text-lg sm:text-xl font-extrabold text-white tracking-tight">
          Dataset Hasil Crawling
        </h3>
        <span className="text-xs font-semibold text-slate-400">
          {filteredItems.length} dari {totalCount} Data
        </span>
      </div>

      {/* Action Controls Toolbar */}
      {/* DESKTOP LAYOUT (sm:flex) */}
      <div className="hidden sm:flex flex-col gap-3 mb-5">
        <div className="flex items-center justify-between gap-3">
          {/* Search inside results */}
          <div className="relative w-72">
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
            <input
              type="text"
              value={searchFilter}
              onChange={(e) => setSearchFilter(e.target.value)}
              placeholder="Cari dalam hasil data..."
              className="w-full pl-9 pr-3 py-2 bg-slate-900 border border-slate-800 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-red-500 transition-colors"
            />
          </div>

          {/* Action buttons */}
          <div className="flex items-center gap-2">
            <button
              onClick={onRefresh}
              disabled={isLoading}
              title="Segarkan data dari server"
              className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 hover:text-white text-xs font-semibold transition-colors"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin text-red-400' : ''}`} />
              <span>Segarkan Data</span>
            </button>

            <a
              href={api.getExportCsvUrl()}
              target="_blank"
              rel="noreferrer"
              download="jinwoo_crawl_dataset.csv"
              className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-emerald-600/20 hover:bg-emerald-600/30 border border-emerald-500/50 text-emerald-300 text-xs font-bold transition-all"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Unduh CSV</span>
            </a>

            <a
              href={api.getExportJsonUrl()}
              target="_blank"
              rel="noreferrer"
              download="jinwoo_crawl_dataset.json"
              className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-blue-600/20 hover:bg-blue-600/30 border border-blue-500/50 text-blue-300 text-xs font-bold transition-all"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Unduh JSON</span>
            </a>
          </div>
        </div>

        {/* Filter Bar Desktop: Platform Pills & Category Dropdown (Hilangkan toggle panah bawah) */}
        <div className="flex items-center justify-between gap-3 pt-1">
          <div className="flex items-center gap-1.5 overflow-x-auto no-scrollbar">
            {PLATFORM_FILTERS.map((f) => (
              <button
                key={f.id}
                onClick={() => onSelectTool(f.id)}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors shrink-0 ${
                  selectedTool === f.id
                    ? 'bg-red-600 text-white shadow-sm'
                    : 'bg-slate-900 hover:bg-slate-800 text-slate-400 hover:text-slate-200 border border-slate-800'
                }`}
              >
                {f.label}
              </button>
            ))}
          </div>

          <div className="flex items-center gap-2 shrink-0">
            {/* Year Dropdown TANPA toggle panah bawah */}
            <select
              value={selectedYear}
              onChange={(e) => onSelectYear(e.target.value)}
              style={{ appearance: 'none', WebkitAppearance: 'none', MozAppearance: 'none' }}
              className="appearance-none bg-slate-900 border border-slate-800 text-slate-300 text-xs font-medium rounded-xl px-3 py-1.5 focus:outline-none cursor-pointer"
              title="Filter tahun terbit berita"
            >
              <option value="all">Semua Tahun</option>
              <option value="2026">2026</option>
              <option value="2025">2025</option>
              <option value="2024">2024</option>
              <option value="2023">2023</option>
              <option value="2022">2022</option>
              <option value="2021">2021</option>
            </select>

            {/* Category Dropdown TANPA toggle panah bawah */}
            <select
              value={selectedCategory}
              onChange={(e) => onSelectCategory(e.target.value)}
              style={{ appearance: 'none', WebkitAppearance: 'none', MozAppearance: 'none' }}
              className="appearance-none bg-slate-900 border border-slate-800 text-slate-300 text-xs font-medium rounded-xl px-3 py-1.5 focus:outline-none cursor-pointer"
            >
              <option value="all">Semua Kategori</option>
              <option value="Disaster">Disaster (Bencana)</option>
              <option value="Politics">Politics (Politik)</option>
              <option value="Economy">Economy (Ekonomi)</option>
              <option value="Tech">Tech (Teknologi)</option>
              <option value="Social">Social (Sosial)</option>
              <option value="News">Berita Utama</option>
            </select>
          </div>
        </div>
      </div>

      {/* MOBILE CONTROLS: STRICTLY 1 COMPONENT PER LINE (w-full stack) */}
      <div className="sm:hidden flex flex-col gap-2.5 w-full mb-5">
        {/* Baris 1: Search */}
        <div className="relative w-full">
          <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
          <input
            type="text"
            value={searchFilter}
            onChange={(e) => setSearchFilter(e.target.value)}
            placeholder="Cari dalam hasil data..."
            className="w-full pl-9 pr-3 py-2.5 bg-slate-900 border border-slate-800 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-red-500"
          />
        </div>

        {/* Baris 2: Segarkan Data */}
        <button
          onClick={onRefresh}
          disabled={isLoading}
          className="w-full flex items-center justify-center gap-2 py-2.5 rounded-xl bg-slate-900 text-slate-200 text-xs font-semibold border border-slate-800"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin text-red-400' : ''}`} />
          <span>Segarkan Data</span>
        </button>

        {/* Baris 3: Unduh CSV */}
        <a
          href={api.getExportCsvUrl()}
          target="_blank"
          rel="noreferrer"
          download="jinwoo_crawl_dataset.csv"
          className="w-full flex items-center justify-center gap-2 py-2.5 rounded-xl bg-emerald-600/20 border border-emerald-500/50 text-emerald-300 text-xs font-bold"
        >
          <Download className="w-3.5 h-3.5" />
          <span>Unduh CSV (Spark)</span>
        </a>

        {/* Baris 4: Unduh JSON */}
        <a
          href={api.getExportJsonUrl()}
          target="_blank"
          rel="noreferrer"
          download="jinwoo_crawl_dataset.json"
          className="w-full flex items-center justify-center gap-2 py-2.5 rounded-xl bg-blue-600/20 border border-blue-500/50 text-blue-300 text-xs font-bold"
        >
          <Download className="w-3.5 h-3.5" />
          <span>Unduh JSON (HDFS)</span>
        </a>

        {/* Baris 5: Dropdown Filter Platform (TANPA toggle panah bawah) */}
        <select
          value={selectedTool}
          onChange={(e) => onSelectTool(e.target.value)}
          style={{ appearance: 'none', WebkitAppearance: 'none', MozAppearance: 'none' }}
          className="appearance-none w-full bg-slate-900 border border-slate-800 text-slate-200 text-xs font-medium rounded-xl px-3.5 py-2.5 focus:outline-none cursor-pointer"
        >
          {PLATFORM_FILTERS.map(f => (
            <option key={f.id} value={f.id}>{f.label}</option>
          ))}
        </select>

        {/* Baris 6: Dropdown Filter Tahun (1 Baris 1 Komponen) */}
        <select
          value={selectedYear}
          onChange={(e) => onSelectYear(e.target.value)}
          style={{ appearance: 'none', WebkitAppearance: 'none', MozAppearance: 'none' }}
          className="appearance-none w-full bg-slate-900 border border-slate-800 text-slate-200 text-xs font-medium rounded-xl px-3.5 py-2.5 focus:outline-none cursor-pointer"
        >
          <option value="all">Semua Tahun Berita</option>
          <option value="2026">Tahun 2026</option>
          <option value="2025">Tahun 2025</option>
          <option value="2024">Tahun 2024</option>
          <option value="2023">Tahun 2023</option>
          <option value="2022">Tahun 2022</option>
          <option value="2021">Tahun 2021</option>
        </select>

        {/* Baris 7: Dropdown Filter Kategori (1 Baris 1 Komponen) */}
        <select
          value={selectedCategory}
          onChange={(e) => onSelectCategory(e.target.value)}
          style={{ appearance: 'none', WebkitAppearance: 'none', MozAppearance: 'none' }}
          className="appearance-none w-full bg-slate-900 border border-slate-800 text-slate-200 text-xs font-medium rounded-xl px-3.5 py-2.5 focus:outline-none cursor-pointer"
        >
          <option value="all">Semua Kategori Berita</option>
          <option value="Disaster">Disaster (Bencana)</option>
          <option value="Politics">Politics (Politik)</option>
          <option value="Economy">Economy (Ekonomi)</option>
          <option value="Tech">Tech (Teknologi)</option>
          <option value="Social">Social (Sosial)</option>
          <option value="News">Breaking News</option>
        </select>
      </div>

      {/* CARD GRID DISPLAY (EXPANSIVE, BERSIH, THUMBNAIL TANPA BADGE YANG MENUTUPI) */}
      {paginatedItems.length === 0 ? (
        isFetching ? (
          <div className="p-12 text-center rounded-2xl bg-slate-900/50 border border-slate-800/80">
            <div className="w-10 h-10 mx-auto rounded-xl bg-slate-800/60 border border-slate-700/50 flex items-center justify-center text-red-400 mb-2.5">
              <RefreshCw className="w-5 h-5 animate-spin" />
            </div>
            <h4 className="text-sm font-semibold text-slate-200">Memuat Dataset dari MongoDB...</h4>
            <p className="text-xs text-slate-400 max-w-sm mx-auto mt-1">
              Sedang mengambil data ({totalCount.toLocaleString('id-ID')} baris tersimpan di server).
            </p>
          </div>
        ) : (
          <div className="p-12 text-center rounded-2xl bg-slate-900/50 border border-slate-800/80">
            <div className="w-10 h-10 mx-auto rounded-xl bg-slate-800/60 border border-slate-700/50 flex items-center justify-center text-slate-400 mb-2.5">
              <Search className="w-5 h-5 text-slate-400" />
            </div>
            <h4 className="text-sm font-semibold text-slate-200">Belum Ada Data</h4>
            <p className="text-xs text-slate-400 max-w-sm mx-auto mt-1">
              Gunakan tombol <span className="text-red-400 font-semibold">Mulai Crawling</span> di atas untuk mengumpulkan data baru.
            </p>
          </div>
        )
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {paginatedItems.map((item) => (
            <div
              key={item.id}
              onClick={() => onSelectItem(item)}
              className="group bg-slate-900 border border-slate-800 hover:border-red-500/70 rounded-2xl overflow-hidden shadow-lg hover:shadow-2xl hover:shadow-black/60 transition-all duration-200 flex flex-col justify-between cursor-pointer"
            >
              <div>
                {/* 16:9 Aspect Ratio Thumbnail Container (MURNI GAMBAR SAJA, TANPA BADGE ATAU TEKS MENIMPA) */}
                <div className="w-full aspect-video bg-black relative overflow-hidden flex items-center justify-center border-b border-slate-800/80">
                  {item.thumbnail_url && !failedThumbs[item.id] ? (
                    <img
                      src={item.thumbnail_url}
                      alt={item.title}
                      referrerPolicy="no-referrer"
                      className="w-full h-full object-contain group-hover:scale-105 transition-transform duration-300"
                      onError={() => {
                        setFailedThumbs(prev => ({ ...prev, [item.id]: true }));
                      }}
                    />
                  ) : (
                    <div className="flex flex-col items-center justify-center text-slate-600 gap-1">
                      <Layers className="w-6 h-6 text-slate-500" />
                      <span className="text-[10px] font-semibold uppercase">{item.platform}</span>
                    </div>
                  )}
                </div>

                {/* Card Content (SEMUA TEKS & BADGE DITARUH DI BAWAH THUMBNAIL) */}
                <div className="p-4 space-y-2">
                  {/* Baris 1 di Bawah Thumbnail: Platform, Tool Source, & Kategori */}
                  <div className="flex items-center gap-1.5 flex-wrap">
                    <span className="px-2 py-0.5 rounded-md text-[10px] font-bold bg-slate-800 text-white border border-slate-700">
                      {item.platform}
                    </span>
                    <span className="px-2 py-0.5 rounded-md text-[10px] font-semibold bg-slate-950 text-slate-300 border border-slate-800">
                      {item.tool_source}
                    </span>
                    <CategoryBadge category={item.category} />
                  </div>

                  {/* Baris 2: Tanggal Terbit di baris sendiri (tidak tumpang tindih) */}
                  <div className="text-[11px] text-slate-400 font-medium">
                    {item.published_date || item.published_at?.split('T')[0] || '-'}
                  </div>

                  {/* Baris 3: Judul Berita */}
                  <h4 className="font-bold text-xs sm:text-sm text-white line-clamp-2 leading-snug group-hover:text-red-400 transition-colors">
                    {item.title}
                  </h4>

                  {/* Baris 4: Cuplikan Konten */}
                  <p className="text-[11px] text-slate-400 line-clamp-2 break-words leading-relaxed">
                    {item.content}
                  </p>

                  {/* Baris 5: Sumber / Penulis */}
                  <div className="text-[11px] text-slate-400 truncate pt-1">
                    Sumber: <span className="font-semibold text-slate-200">{item.author_or_source || 'Anonim'}</span>
                  </div>
                </div>
              </div>

              {/* Card Footer: Metrik Keterlibatan (Tanpa teks 'Detail ->') */}
              <div className="px-4 py-2.5 bg-slate-950/70 border-t border-slate-800/80 flex items-center justify-between text-[11px] text-slate-400">
                <div className="flex items-center gap-3">
                  {item.metrics.views !== undefined && item.metrics.views > 0 && (
                    <span className="flex items-center gap-1" title="Views">
                      <Eye className="w-3.5 h-3.5 text-cyan-400" />
                      {item.metrics.views.toLocaleString('id-ID')}
                    </span>
                  )}
                  {item.metrics.likes !== undefined && item.metrics.likes > 0 && (
                    <span className="flex items-center gap-1" title="Likes">
                      <Heart className="w-3.5 h-3.5 text-red-400" />
                      {item.metrics.likes.toLocaleString('id-ID')}
                    </span>
                  )}
                  {item.metrics.comments !== undefined && item.metrics.comments > 0 && (
                    <span className="flex items-center gap-1" title="Comments">
                      <MessageCircle className="w-3.5 h-3.5 text-blue-400" />
                      {item.metrics.comments.toLocaleString('id-ID')}
                    </span>
                  )}
                  {item.metrics.shares !== undefined && item.metrics.shares > 0 && (
                    <span className="flex items-center gap-1" title="Shares">
                      <Share2 className="w-3.5 h-3.5 text-emerald-400" />
                      {item.metrics.shares.toLocaleString('id-ID')}
                    </span>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* PAGINATION BAR: RESPONSIVE & STRICT 1 LINE PER COMPONENT ON MOBILE */}
      {totalPages > 1 && (
        <div className="mt-6 pt-4 border-t border-slate-800/80">
          {/* MOBILE PAGINATION: STRICTLY 1 COMPONENT PER LINE (w-full vertical stack) */}
          <div className="sm:hidden flex flex-col gap-2.5 w-full">
            {/* Baris 1: Informasi Range Data */}
            <div className="text-center text-xs text-slate-400 font-medium py-1">
              Menampilkan data ke <strong className="text-white">{startIndex + 1}</strong> -{' '}
              <strong className="text-white">{Math.min(startIndex + pageSize, filteredItems.length)}</strong> dari{' '}
              <strong className="text-white">{filteredItems.length}</strong>
            </div>

            {/* Baris 2: Indikator Halaman (Tidak akan pernah wrap) */}
            <div className="text-center">
              <span className="inline-block px-4 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-xs font-bold text-white whitespace-nowrap shadow-sm">
                Halaman {currentPage} dari {totalPages}
              </span>
            </div>

            {/* Baris 3: Tombol Halaman Sebelumnya (Full Width) */}
            <button
              onClick={() => setCurrentPage(prev => Math.max(prev - 1, 1))}
              disabled={currentPage === 1}
              className="w-full flex items-center justify-center gap-2 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-xs font-semibold text-slate-200 hover:bg-slate-800 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
            >
              <ChevronLeft className="w-4 h-4" />
              <span>Halaman Sebelumnya</span>
            </button>

            {/* Baris 4: Tombol Halaman Berikutnya (Full Width) */}
            <button
              onClick={() => setCurrentPage(prev => Math.min(prev + 1, totalPages))}
              disabled={currentPage === totalPages}
              className="w-full flex items-center justify-center gap-2 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-xs font-semibold text-slate-200 hover:bg-slate-800 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
            >
              <span>Halaman Berikutnya</span>
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>

          {/* DESKTOP PAGINATION: CLEAN HORIZONTAL BAR */}
          <div className="hidden sm:flex items-center justify-between gap-3">
            <span className="text-xs text-slate-400 font-medium">
              Menampilkan data ke <strong className="text-white">{startIndex + 1}</strong> -{' '}
              <strong className="text-white">{Math.min(startIndex + pageSize, filteredItems.length)}</strong> dari{' '}
              <strong className="text-white">{filteredItems.length}</strong>
            </span>

            <div className="flex items-center gap-2 shrink-0">
              <button
                onClick={() => setCurrentPage(prev => Math.max(prev - 1, 1))}
                disabled={currentPage === 1}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-xs font-semibold text-slate-300 hover:text-white hover:bg-slate-800 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
              >
                <ChevronLeft className="w-3.5 h-3.5" />
                <span>Sebelumnya</span>
              </button>

              <span className="px-3.5 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-xs font-bold text-white whitespace-nowrap">
                {currentPage} / {totalPages}
              </span>

              <button
                onClick={() => setCurrentPage(prev => Math.min(prev + 1, totalPages))}
                disabled={currentPage === totalPages}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-xs font-semibold text-slate-300 hover:text-white hover:bg-slate-800 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
              >
                <span>Berikutnya</span>
                <ChevronRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
