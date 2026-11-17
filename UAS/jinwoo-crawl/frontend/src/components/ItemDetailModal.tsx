import React, { useEffect } from 'react';
import { X, ExternalLink, Eye, Heart, MessageCircle, Share2, Code, Check } from 'lucide-react';
import { ScrapedItem } from '../types';
import { CategoryBadge } from './CategoryBadge';

interface ItemDetailModalProps {
  item: ScrapedItem | null;
  onClose: () => void;
}

export const ItemDetailModal: React.FC<ItemDetailModalProps> = ({ item, onClose }) => {
  const [showJson, setShowJson] = React.useState(false);
  const [copied, setCopied] = React.useState(false);

  // Close modal when pressing Escape key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  if (!item) return null;

  const copyJson = () => {
    navigator.clipboard.writeText(JSON.stringify(item, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    /* Outer Backdrop with Click-to-Close */
    <div
      onClick={onClose}
      className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-5 bg-black/85 backdrop-blur-md animate-fadeIn cursor-pointer font-['Plus_Jakarta_Sans',sans-serif]"
    >
      {/* Center Modal Container (Stop Propagation so clicking inside does not close) */}
      <div
        onClick={(e) => e.stopPropagation()}
        className="w-full max-w-2xl max-h-[92vh] bg-slate-900 border border-slate-700/80 rounded-2xl shadow-2xl flex flex-col overflow-hidden text-slate-100 cursor-default"
      >
        {/* Modal Header: 1 Baris Tidak Boleh Lebih dari 1 Komponen (Text-Wrapper Stack) */}
        <div className="px-5 py-4 border-b border-slate-800 bg-slate-950/80 relative">
          {/* Tombol Tutup X di Pojok Kanan Atas */}
          <button
            onClick={onClose}
            className="absolute right-4 top-4 p-1.5 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
            title="Tutup (Esc)"
          >
            <X className="w-5 h-5" />
          </button>

          {/* Vertical Stack: 1 Baris 1 Komponen */}
          <div className="flex flex-col items-start gap-2 pr-10">
            {/* Baris 1: Platform */}
            <span className="font-extrabold text-base text-white tracking-tight">
              {item.platform}
            </span>

            {/* Baris 2: Badge Kategori */}
            <div>
              <CategoryBadge category={item.category} />
            </div>

            {/* Baris 3: Engine Scraping */}
            <span className="text-[11px] font-mono text-slate-400 bg-slate-800 px-2.5 py-1 rounded-lg border border-slate-700/60">
              via {item.tool_source}
            </span>
          </div>
        </div>

        {/* Modal Scrollable Body */}
        <div className="p-5 overflow-y-auto space-y-4">
          {/* 16:9 Aspect Ratio Thumbnail */}
          {item.thumbnail_url && (
            <div className="w-full aspect-video rounded-xl overflow-hidden bg-black/70 border border-slate-800 flex items-center justify-center relative">
              <img
                src={item.thumbnail_url}
                alt={item.title}
                referrerPolicy="no-referrer"
                className="w-full h-full object-contain"
                onError={(e) => {
                  (e.target as HTMLElement).style.display = 'none';
                }}
              />
            </div>
          )}

          {/* Judul Berita */}
          <h2 className="text-base sm:text-lg font-bold text-white leading-snug">
            {item.title}
          </h2>

          {/* Cuplikan Konten Lengkap */}
          <div className="p-3.5 rounded-xl bg-slate-950/80 border border-slate-800 text-xs text-slate-300 leading-relaxed break-words whitespace-pre-wrap">
            {item.content}
          </div>

          {/* Detail Metadata Dataset (HDFS / Spark Ready) */}
          {/* TANPA ICON - 1 Baris Label, 1 Baris Value (Semua Atribut Terpisah Rapi) */}
          <div className="rounded-xl border border-slate-800 overflow-hidden text-xs">
            {/* Header Metadata TANPA ICON */}
            <div className="bg-slate-950/90 px-4 py-2.5 font-bold text-slate-300 uppercase text-[11px] tracking-wider border-b border-slate-800">
              DETAIL METADATA DATASET (HDFS / SPARK READY)
            </div>

            <div className="divide-y divide-slate-800/80 bg-slate-900/60">
              {/* ID Dokumen: Label Baris 1, Value Baris 2 */}
              <div className="flex flex-col gap-1 p-3">
                <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wide">
                  ID Dokumen
                </span>
                <span className="font-mono text-xs text-slate-200 break-all select-all">
                  {item.id || item._id}
                </span>
              </div>

              {/* Kata Kunci Isu: Label Baris 1, Value Baris 2 */}
              <div className="flex flex-col gap-1 p-3">
                <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wide">
                  Kata Kunci Isu
                </span>
                <span className="font-bold text-xs sm:text-sm text-red-400">
                  #{item.keyword}
                </span>
              </div>

              {/* Sumber / Penulis: Label Baris 1, Value Baris 2 */}
              <div className="flex flex-col gap-1 p-3">
                <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wide">
                  Sumber / Penulis
                </span>
                <span className="text-xs sm:text-sm text-slate-200 font-medium">
                  {item.author_or_source || 'Anonim'}
                </span>
              </div>

              {/* Tanggal Terbit: Label Baris 1, Value Baris 2 */}
              <div className="flex flex-col gap-1 p-3">
                <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wide">
                  Tanggal Terbit
                </span>
                <span className="text-xs sm:text-sm text-slate-200 font-medium">
                  {item.published_date || item.published_at?.split('T')[0] || '-'}
                </span>
              </div>

              {/* Timestamp Lengkap: Label Baris 1, Value Baris 2 */}
              <div className="flex flex-col gap-1 p-3">
                <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wide">
                  Timestamp Lengkap
                </span>
                <span className="font-mono text-xs text-slate-300 break-all">
                  {item.published_at || '-'}
                </span>
              </div>

              {/* Metrik Keterlibatan: Label Baris 1, Value Baris 2 */}
              <div className="flex flex-col gap-1 p-3">
                <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wide">
                  Metrik Keterlibatan
                </span>
                <div className="flex flex-wrap items-center gap-3 sm:gap-4 pt-1 text-xs text-slate-200">
                  <span className="flex items-center gap-1.5" title="Views">
                    <Eye className="w-4 h-4 text-cyan-400 shrink-0" />
                    <span>{(item.metrics.views || 0).toLocaleString('id-ID')} views</span>
                  </span>
                  <span className="flex items-center gap-1.5" title="Likes">
                    <Heart className="w-4 h-4 text-red-400 shrink-0" />
                    <span>{(item.metrics.likes || 0).toLocaleString('id-ID')} likes</span>
                  </span>
                  <span className="flex items-center gap-1.5" title="Comments">
                    <MessageCircle className="w-4 h-4 text-blue-400 shrink-0" />
                    <span>{(item.metrics.comments || 0).toLocaleString('id-ID')} comments</span>
                  </span>
                  <span className="flex items-center gap-1.5" title="Shares">
                    <Share2 className="w-4 h-4 text-emerald-400 shrink-0" />
                    <span>{(item.metrics.shares || 0).toLocaleString('id-ID')} shares</span>
                  </span>
                </div>
              </div>

              {/* Skor Sentimen Tone: Label Baris 1, Value Baris 2 */}
              <div className="flex flex-col gap-1 p-3">
                <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wide">
                  Skor Sentimen Tone
                </span>
                <span className="font-mono font-bold text-sm text-amber-400">
                  {item.metrics.sentiment_tone ?? 0.0}
                </span>
              </div>
            </div>
          </div>

          {/* Raw JSON Accordion */}
          <div className="pt-1">
            <button
              onClick={() => setShowJson(!showJson)}
              className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-200 font-medium"
            >
              <Code className="w-3.5 h-3.5" />
              <span>{showJson ? 'Sembunyikan Raw JSON' : 'Lihat Dokumen Raw JSON'}</span>
            </button>

            {showJson && (
              <div className="mt-2 relative">
                <button
                  onClick={copyJson}
                  className="absolute right-2 top-2 px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-[10px] text-slate-200 rounded-lg flex items-center gap-1"
                >
                  {copied ? <Check className="w-3 h-3 text-emerald-400" /> : null}
                  <span>{copied ? 'Tersalin' : 'Salin JSON'}</span>
                </button>
                <pre className="p-3 bg-slate-950 border border-slate-800 rounded-xl text-[10px] font-mono text-emerald-300 overflow-x-auto max-h-48">
                  {JSON.stringify(item, null, 2)}
                </pre>
              </div>
            )}
          </div>
        </div>

        {/* Modal Footer: Mobile 1 Komponen Per Baris (w-full stack) */}
        <div className="px-5 py-3.5 border-t border-slate-800 bg-slate-950/80 flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-2.5">
          {item.url && item.url !== '#' && (
            <a
              href={item.url}
              target="_blank"
              rel="noreferrer"
              className="w-full sm:w-auto flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl bg-red-600 hover:bg-red-500 text-xs font-bold text-white transition-all shadow-md order-1 sm:order-2"
            >
              <span>Kunjungi Sumber Asli</span>
              <ExternalLink className="w-3.5 h-3.5" />
            </a>
          )}

          <button
            onClick={onClose}
            className="w-full sm:w-auto px-5 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-300 transition-colors order-2 sm:order-1 text-center"
          >
            Tutup
          </button>
        </div>
      </div>
    </div>
  );
};
