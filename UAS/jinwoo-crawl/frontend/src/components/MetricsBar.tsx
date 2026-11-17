import React from 'react';
import { Database, Share2, Layers, TrendingUp } from 'lucide-react';
import { DashboardStats } from '../types';

interface MetricsBarProps {
  stats: DashboardStats | null;
}

export const MetricsBar: React.FC<MetricsBarProps> = ({ stats }) => {
  const total = stats?.total_documents || 0;
  const platformCount = Object.keys(stats?.platforms || {}).length;
  const toolCount = Object.keys(stats?.tools || {}).length;

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
      {/* 1. Total Ingested Docs */}
      <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800/80 backdrop-blur-sm relative overflow-hidden group hover:border-slate-700 transition-all">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Total Ingested Data</span>
          <div className="p-2 rounded-lg bg-red-950/40 border border-red-800/30 text-red-400">
            <Database className="w-4 h-4" />
          </div>
        </div>
        <div className="mt-3 flex items-baseline gap-2">
          <span className="text-2xl font-extrabold text-white">{total.toLocaleString('id-ID')}</span>
          <span className="text-xs text-slate-400 font-medium">dokumen di MongoDB</span>
        </div>
        <div className="mt-2 text-[11px] text-slate-500">
          Target riset UAS: <span className="text-slate-300 font-semibold">20.000+ data baris</span>
        </div>
      </div>

      {/* 2. Multi-Platform Coverage */}
      <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800/80 backdrop-blur-sm relative overflow-hidden group hover:border-slate-700 transition-all">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Liputan Platform</span>
          <div className="p-2 rounded-lg bg-blue-950/40 border border-blue-800/30 text-blue-400">
            <Share2 className="w-4 h-4" />
          </div>
        </div>
        <div className="mt-3 flex items-baseline gap-2">
          <span className="text-2xl font-extrabold text-white">{platformCount}</span>
          <span className="text-xs text-slate-400 font-medium">Platform Media Aktif</span>
        </div>
        <div className="mt-2 text-[11px] text-slate-400 truncate">
          GDELT News, TikTok, IG, FB, YT, Meta Ads
        </div>
      </div>

      {/* 3. Scrapers Active */}
      <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800/80 backdrop-blur-sm relative overflow-hidden group hover:border-slate-700 transition-all">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Pipeline Ingestion</span>
          <div className="p-2 rounded-lg bg-emerald-950/40 border border-emerald-800/30 text-emerald-400">
            <Layers className="w-4 h-4" />
          </div>
        </div>
        <div className="mt-3 flex items-baseline gap-2">
          <span className="text-2xl font-extrabold text-white">8/8</span>
          <span className="text-xs text-emerald-400 font-semibold">Tools Siap Pakai</span>
        </div>
        <div className="mt-2 text-[11px] text-slate-400">
          Export format: <span className="text-slate-300 font-mono">HDFS (JSON) & Spark (CSV)</span>
        </div>
      </div>

      {/* 4. Issue Attention Modeling */}
      <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800/80 backdrop-blur-sm relative overflow-hidden group hover:border-slate-700 transition-all">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Siklus Isu (Downs)</span>
          <div className="p-2 rounded-lg bg-amber-950/40 border border-amber-800/30 text-amber-400">
            <TrendingUp className="w-4 h-4" />
          </div>
        </div>
        <div className="mt-3 flex items-baseline gap-2">
          <span className="text-base font-bold text-amber-400">5 Tahap Kurva</span>
          <span className="text-xs text-slate-400">Anthony Downs</span>
        </div>
        <div className="mt-2 text-[11px] text-slate-400">
          Target MLlib: <span className="text-slate-300 font-semibold">Durasi Isu (Hari) & Decay</span>
        </div>
      </div>
    </div>
  );
};
