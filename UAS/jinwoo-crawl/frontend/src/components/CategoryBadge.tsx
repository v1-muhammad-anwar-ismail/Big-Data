import React from 'react';

interface CategoryBadgeProps {
  category: string;
}

export const CategoryBadge: React.FC<CategoryBadgeProps> = ({ category }) => {
  const cat = (category || 'General').toLowerCase();

  let badgeStyle = 'bg-slate-800/80 text-slate-300 border-slate-700';
  let dotColor = 'bg-slate-400';
  let label = category || 'General';

  if (cat.includes('disaster') || cat.includes('bencana') || cat.includes('hutan')) {
    badgeStyle = 'bg-amber-950/40 text-amber-300 border-amber-600/40';
    dotColor = 'bg-amber-500 shadow-[0_0_8px_#f59e0b]';
    label = 'Bencana / Karhutla';
  } else if (cat.includes('politic') || cat.includes('politik')) {
    badgeStyle = 'bg-blue-950/40 text-blue-300 border-blue-600/40';
    dotColor = 'bg-blue-500 shadow-[0_0_8px_#3b82f6]';
    label = 'Politik / Nasional';
  } else if (cat.includes('econom') || cat.includes('ekonomi')) {
    badgeStyle = 'bg-emerald-950/40 text-emerald-300 border-emerald-600/40';
    dotColor = 'bg-emerald-500 shadow-[0_0_8px_#10b981]';
    label = 'Ekonomi / Bisnis';
  } else if (cat.includes('tech') || cat.includes('teknologi')) {
    badgeStyle = 'bg-purple-950/40 text-purple-300 border-purple-600/40';
    dotColor = 'bg-purple-500 shadow-[0_0_8px_#8b5cf6]';
    label = 'Teknologi / Data';
  } else if (cat.includes('social') || cat.includes('sosial')) {
    badgeStyle = 'bg-cyan-950/40 text-cyan-300 border-cyan-600/40';
    dotColor = 'bg-cyan-500 shadow-[0_0_8px_#06b6d4]';
    label = 'Sosial & Budaya';
  } else if (cat.includes('news') || cat.includes('berita')) {
    badgeStyle = 'bg-rose-950/40 text-rose-300 border-rose-600/40';
    dotColor = 'bg-rose-500 shadow-[0_0_8px_#ef4444]';
    label = 'Berita Utama';
  }

  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold tracking-wide border ${badgeStyle}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${dotColor}`} />
      {label}
    </span>
  );
};
