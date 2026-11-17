import React from 'react';

export const Header: React.FC = () => {
  return (
    <header className="sticky top-0 z-40 bg-[#090d16]/95 backdrop-blur-md border-b border-slate-800/80 px-4 sm:px-8 py-3">
      <div className="w-full flex items-center justify-between">
        {/* Brand with JinwooCrawl Custom Logo */}
        <div className="flex items-center gap-3">
          <img
            src="/logo.svg"
            alt="JinwooCrawl Logo"
            className="w-8 h-8 rounded-lg object-contain shrink-0"
          />
          <span className="text-xl font-black tracking-tight text-white font-['Plus_Jakarta_Sans',sans-serif]">
            Jinwoo<span className="text-red-500">Crawl</span>
          </span>
        </div>
      </div>
    </header>
  );
};
