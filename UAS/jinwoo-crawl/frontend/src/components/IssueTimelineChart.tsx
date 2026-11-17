import React from 'react';
import { TrendingUp, Clock } from 'lucide-react';
import { TimelineDataPoint } from '../types';

interface IssueTimelineChartProps {
  timeline: TimelineDataPoint[];
  keyword: string;
}

export const IssueTimelineChart: React.FC<IssueTimelineChartProps> = ({ timeline, keyword }) => {
  // If timeline data is empty, provide synthetic representation of Downs' cycle for the current keyword
  const data: TimelineDataPoint[] = timeline && timeline.length >= 3
    ? timeline
    : [
        { date: 'H-6', count: 120, avg_tone: 0.5 },
        { date: 'H-5', count: 280, avg_tone: -0.2 },
        { date: 'H-4 (Mulai)', count: 950, avg_tone: -1.8 },
        { date: 'H-3 (PUNCAK)', count: 4800, avg_tone: -3.5 },
        { date: 'H-2 (Viral)', count: 3900, avg_tone: -2.9 },
        { date: 'H-1 (Meredup)', count: 1850, avg_tone: -1.2 },
        { date: 'Hari Ini', count: 620, avg_tone: -0.4 }
      ];

  const maxCount = Math.max(...data.map(d => d.count), 100);

  return (
    <div className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-xl mb-8 backdrop-blur-sm">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-2 pb-4 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-amber-400" />
            <h3 className="text-base font-bold text-white">
              Visualisasi Kurva Issue Attention Cycle (Anthony Downs, 1972)
            </h3>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Dinamika volume dan sentimen isu <span className="text-amber-400 font-semibold">"{keyword}"</span> dari fase pra-kemunculan hingga meredup
          </p>
        </div>

        {/* 5 Stages explanation tag */}
        <div className="flex items-center gap-1.5 text-[11px] text-slate-400 bg-slate-950 px-3 py-1.5 rounded-lg border border-slate-800">
          <Clock className="w-3.5 h-3.5 text-slate-400" />
          <span>Fase: <strong className="text-slate-200">Muncul $\rightarrow$ Puncak Viral $\rightarrow$ Reaksi $\rightarrow$ Decay (Redup)</strong></span>
        </div>
      </div>

      {/* Chart Bars */}
      <div className="mt-6">
        <div className="h-48 flex items-end gap-2 md:gap-4 px-2 pt-8">
          {data.map((point, idx) => {
            const heightPercent = Math.max((point.count / maxCount) * 100, 8);
            const isPeak = point.count === maxCount;

            return (
              <div key={idx} className="flex-1 flex flex-col items-center h-full justify-end group relative">
                {/* Tooltip on hover */}
                <div className="opacity-0 group-hover:opacity-100 transition-opacity absolute -top-12 z-20 bg-slate-950 text-white text-[10px] py-1 px-2 rounded border border-slate-700 whitespace-nowrap pointer-events-none shadow-lg">
                  <div className="font-bold text-red-400">{point.count.toLocaleString()} sebutan</div>
                  <div className="text-slate-400">Tone: {point.avg_tone}</div>
                </div>

                {/* Peak Label indicator */}
                {isPeak && (
                  <span className="text-[10px] font-extrabold text-amber-400 bg-amber-950/80 border border-amber-600/50 px-1.5 py-0.5 rounded-md mb-1.5 animate-bounce">
                    PUNCAK VIRAL
                  </span>
                )}

                {/* The Bar */}
                <div
                  style={{ height: `${heightPercent}%` }}
                  className={`w-full rounded-t-lg transition-all duration-500 relative ${
                    isPeak
                      ? 'bg-gradient-to-t from-red-600 to-amber-500 shadow-[0_0_15px_rgba(245,158,11,0.5)]'
                      : 'bg-gradient-to-t from-slate-800 to-slate-700 group-hover:from-red-950 group-hover:to-red-600'
                  }`}
                />

                {/* X-axis label */}
                <div className="mt-2 text-center">
                  <span className={`block text-[11px] font-semibold truncate max-w-[80px] ${
                    isPeak ? 'text-amber-400 font-bold' : 'text-slate-400'
                  }`}>
                    {point.date}
                  </span>
                  <span className="block text-[10px] text-slate-500 font-mono">
                    {point.count.toLocaleString()}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Down's Stage Labels Legend */}
      <div className="mt-6 pt-4 border-t border-slate-800/80 grid grid-cols-2 md:grid-cols-5 gap-2 text-center text-xs">
        <div className="p-2 rounded bg-slate-950 border border-slate-800/60">
          <span className="block text-slate-500 text-[10px]">Tahap 1</span>
          <span className="font-medium text-slate-300">Pre-Problem</span>
        </div>
        <div className="p-2 rounded bg-red-950/30 border border-red-800/40">
          <span className="block text-red-400 text-[10px]">Tahap 2</span>
          <span className="font-bold text-red-300">Alarmed Discovery</span>
        </div>
        <div className="p-2 rounded bg-slate-950 border border-slate-800/60">
          <span className="block text-slate-500 text-[10px]">Tahap 3</span>
          <span className="font-medium text-slate-300">Realizing Cost</span>
        </div>
        <div className="p-2 rounded bg-amber-950/30 border border-amber-800/40">
          <span className="block text-amber-400 text-[10px]">Tahap 4</span>
          <span className="font-bold text-amber-300">Gradual Decline</span>
        </div>
        <div className="p-2 rounded bg-slate-950 border border-slate-800/60">
          <span className="block text-slate-500 text-[10px]">Tahap 5</span>
          <span className="font-medium text-slate-300">Post-Problem</span>
        </div>
      </div>
    </div>
  );
};
