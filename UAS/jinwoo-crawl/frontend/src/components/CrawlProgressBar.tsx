import React from 'react';
import { RefreshCw, Download, Database } from 'lucide-react';
import { api } from '../services/api';

export interface CrawlProgressState {
  isActive: boolean;
  isComplete: boolean;
  totalTools: number;
  completedTools: number;
  currentToolName: string;
  totalCollected: number;
  percent: number;
  toolStatuses: Record<string, { status: 'pending' | 'running' | 'success' | 'empty' | 'error'; count: number; name: string; message?: string }>;
}

interface CrawlProgressBarProps {
  progress: CrawlProgressState;
  onClose: () => void;
}

export const CrawlProgressBar: React.FC<CrawlProgressBarProps> = ({ progress, onClose }) => {
  if (!progress.isActive && !progress.isComplete) return null;

  const statusText = progress.isComplete
    ? 'Crawling Selesai!'
    : 'Sedang Melakukan Crawling Dataset...';

  const summaryText = progress.isComplete
    ? `Total ${progress.totalCollected.toLocaleString('id-ID')} data berhasil dikumpulkan & tersimpan di MongoDB.`
    : `Sedang memproses: ${progress.currentToolName}...`;

  return (
    <div className="bg-slate-950 border border-slate-800 rounded-2xl p-4 sm:p-5 shadow-2xl mb-6 transition-all animate-fadeIn">
      {/* MOBILE HEADER: STRICTLY 1 COMPONENT PER LINE (Vertical Text-Wrapper Stack) */}
      <div className="sm:hidden flex flex-col items-start gap-2 mb-3 w-full">
        {/* Baris 1: Judul Status */}
        <h4 className="text-base font-extrabold text-white leading-snug w-full">
          {statusText}
        </h4>

        {/* Baris 2: Badge Sumber Selesai (Tidak terjepit) */}
        <span
          className={`inline-block w-fit whitespace-nowrap text-[11px] font-bold px-2.5 py-1 rounded-full ${
            progress.isComplete
              ? 'bg-emerald-900/60 text-emerald-300 border border-emerald-700/50'
              : 'bg-red-900/60 text-red-300 border border-red-700/50'
          }`}
        >
          {progress.completedTools}/{progress.totalTools} Sumber Selesai
        </span>

        {/* Baris 3: Persentase Besar */}
        <div className={`text-3xl font-black tracking-tight w-full ${progress.isComplete ? 'text-emerald-400' : 'text-red-500'}`}>
          {progress.percent}%
        </div>

        {/* Baris 4: Ringkasan */}
        <p className="text-xs text-slate-400 leading-relaxed w-full">
          {summaryText}
        </p>
      </div>

      {/* DESKTOP HEADER */}
      <div className="hidden sm:flex items-center justify-between gap-3 mb-3">
        <div className="flex items-center gap-2.5">
          <div className={`p-2 rounded-xl ${progress.isComplete ? 'bg-emerald-950 border border-emerald-700/60 text-emerald-400' : 'bg-red-950 border border-red-800/60 text-red-400'}`}>
            <RefreshCw className={`w-4 h-4 ${progress.isComplete ? '' : 'animate-spin'}`} />
          </div>
          <div>
            <h4 className="text-sm font-bold text-white flex items-center gap-2">
              <span>{statusText}</span>
              <span
                className={`text-[10px] font-bold px-2 py-0.5 rounded-full whitespace-nowrap ${
                  progress.isComplete
                    ? 'bg-emerald-900/60 text-emerald-300 border border-emerald-700/50'
                    : 'bg-red-900/60 text-red-300 border border-red-700/50'
                }`}
              >
                {progress.completedTools}/{progress.totalTools} Sumber Selesai
              </span>
            </h4>
            <p className="text-xs text-slate-400 mt-0.5">{summaryText}</p>
          </div>
        </div>

        <div className="text-right shrink-0">
          <span className={`text-3xl font-black tracking-tight ${progress.isComplete ? 'text-emerald-400' : 'text-red-500'}`}>
            {progress.percent}%
          </span>
        </div>
      </div>

      {/* Progress Bar Track */}
      <div className="w-full bg-slate-900 h-3 rounded-full overflow-hidden border border-slate-800/80 mb-3 relative">
        <div
          className={`h-full transition-all duration-300 ease-out rounded-full ${
            progress.isComplete
              ? 'bg-gradient-to-r from-emerald-500 to-teal-400'
              : 'bg-gradient-to-r from-red-600 via-rose-500 to-amber-500'
          }`}
          style={{ width: `${Math.min(Math.max(progress.percent, 3), 100)}%` }}
        />
      </div>

      {/* Real-time Tally & Action Buttons: Mobile strictly 1 component per line */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2.5 text-xs pt-2.5 border-t border-slate-900 w-full">
        <div className="flex items-center gap-2 text-slate-400 w-full sm:w-auto">
          <Database className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
          <span>
            Data Terkumpul: <strong className="text-white font-bold">{progress.totalCollected.toLocaleString('id-ID')}</strong> baris
          </span>
        </div>

        {progress.isComplete ? (
          <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2 w-full sm:w-auto">
            <a
              href={api.getExportCsvUrl()}
              target="_blank"
              rel="noreferrer"
              download="dataset_bigdata.csv"
              className="w-full sm:w-auto flex items-center justify-center gap-1.5 px-3.5 py-2 sm:py-1.5 rounded-xl sm:rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs shadow-md transition-all"
            >
              <Download className="w-3.5 h-3.5 shrink-0" />
              <span>Unduh .CSV (Spark)</span>
            </a>
            <button
              onClick={onClose}
              className="w-full sm:w-auto px-3.5 py-2 sm:py-1.5 rounded-xl sm:rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold transition-colors text-center"
            >
              Tutup
            </button>
          </div>
        ) : (
          <span className="text-[11px] text-slate-500 animate-pulse font-medium w-full sm:w-auto">
            Mengambil data paralel & menyimpan ke MongoDB...
          </span>
        )}
      </div>

      {/* Checklist Grid of Running Tools: 1 column vertical stack on mobile, 2 on tablet, 4 on desktop */}
      <div className="mt-3 pt-3 border-t border-slate-900 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2">
        {Object.entries(progress.toolStatuses).map(([toolId, info]) => {
          return (
            <div
              key={toolId}
              title={info.message || info.name}
              className={`w-full px-3 py-2.5 sm:p-2 rounded-xl sm:rounded-lg border text-xs sm:text-[11px] flex items-center justify-between gap-2 ${
                info.status === 'running'
                  ? 'bg-red-950/40 border-red-800/60 text-white'
                  : info.status === 'success'
                  ? 'bg-slate-900/60 border-slate-800 text-slate-300'
                  : info.status === 'empty'
                  ? 'bg-slate-900/30 border-slate-800/60 text-slate-400'
                  : info.status === 'error'
                  ? 'bg-amber-950/30 border-amber-800/40 text-amber-300'
                  : 'bg-slate-950 border-slate-900 text-slate-500'
              }`}
            >
              <span className="truncate font-medium">{info.name}</span>
              <div className="shrink-0 flex items-center whitespace-nowrap">
                {info.status === 'running' && (
                  <RefreshCw className="w-3.5 h-3.5 sm:w-3 sm:h-3 text-red-400 animate-spin" />
                )}
                {info.status === 'success' && (
                  <span className="text-emerald-400 font-bold">+{info.count}</span>
                )}
                {info.status === 'empty' && (
                  <span className="text-slate-400 font-semibold">0</span>
                )}
                {info.status === 'error' && (
                  <span className="text-amber-400 font-semibold">Err</span>
                )}
                {info.status === 'pending' && (
                  <span className="text-slate-600">...</span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
