import React, { useState, useEffect, useRef } from 'react';
import { Header } from './components/Header';
import { CrawlCommandBar, ALL_TOOLS } from './components/CrawlCommandBar';
import { CrawlProgressBar, CrawlProgressState } from './components/CrawlProgressBar';
import { DatasetCards } from './components/DatasetCards';
import { ItemDetailModal } from './components/ItemDetailModal';
import { api } from './services/api';
import { DashboardStats, ScrapedItem, SystemHealth } from './types';
import { CheckCircle2, AlertCircle } from 'lucide-react';

export const App: React.FC = () => {
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [items, setItems] = useState<ScrapedItem[]>([]);
  
  // Keyword & Selected Tools State
  const [keyword, setKeyword] = useState<string>('karhutla');
  const [selectedTools, setSelectedTools] = useState<string[]>(ALL_TOOLS.map(t => t.id));
  const [countPerTool, setCountPerTool] = useState<number>(25);
  const [yearRange, setYearRange] = useState<number>(5); // Default 5 tahun terakhir untuk riset Big Data UAS

  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isFetchingItems, setIsFetchingItems] = useState<boolean>(true);
  const [isReloading, setIsReloading] = useState<boolean>(false);
  const [selectedFilterTool, setSelectedFilterTool] = useState<string>('all');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [selectedYear, setSelectedYear] = useState<string>('all');
  
  // Selected Item for Center Popup Modal Detail
  const [selectedItem, setSelectedItem] = useState<ScrapedItem | null>(null);

  const [toastMessage, setToastMessage] = useState<{ text: string; type: 'success' | 'error' } | null>(null);

  // Real-time Crawl Progress Feedback State
  const [crawlProgress, setCrawlProgress] = useState<CrawlProgressState>({
    isActive: false,
    isComplete: false,
    totalTools: 0,
    completedTools: 0,
    currentToolName: '',
    totalCollected: 0,
    percent: 0,
    toolStatuses: {}
  });

  const showToast = (text: string, type: 'success' | 'error' = 'success') => {
    setToastMessage({ text, type });
    setTimeout(() => setToastMessage(null), 4000);
  };

  const fetchSeqRef = useRef(0);

  // Initial metadata load (items are fetched by filter useEffect below to prevent race conditions)
  const loadInitialData = async () => {
    try {
      const [h, s] = await Promise.all([
        api.getHealth().catch(() => null),
        api.getStats().catch(() => null)
      ]);
      if (h) setHealth(h);
      if (s) setStats(s);
    } catch (e) {
      console.error('Error loading initial data:', e);
    }
  };

  useEffect(() => {
    loadInitialData();
  }, []);

  const loadItemsProgressive = async (tool: string, category: string, year: string) => {
    const seq = ++fetchSeqRef.current;
    setIsFetchingItems(true);
    try {
      const fastRes = await api.getItems({
        limit: 200,
        tool_source: tool,
        category,
        year
      });
      if (seq !== fetchSeqRef.current) return;
      setItems(fastRes.items);
      if (fastRes.items.length < 200) {
        setIsFetchingItems(false);
        return;
      }

      const fullRes = await api.getItems({
        limit: 50000,
        tool_source: tool,
        category,
        year
      });
      if (seq !== fetchSeqRef.current) return;
      setItems(fullRes.items);
    } catch (e) {
      console.error('Items load error:', e);
    } finally {
      if (seq === fetchSeqRef.current) {
        setIsFetchingItems(false);
      }
    }
  };

  // Refresh data function
  const refreshData = async () => {
    try {
      const [s, h] = await Promise.all([
        api.getStats(),
        api.getHealth()
      ]);
      setStats(s);
      setHealth(h);
      await loadItemsProgressive(selectedFilterTool, selectedCategory, selectedYear);
    } catch (e) {
      console.error('Refresh error:', e);
    }
  };

  // Manual Reload Handler with BE Sync and Feedback Spinner
  const handleReload = async () => {
    setIsReloading(true);
    try {
      await api.reloadData();
      await refreshData();
      showToast('Data MongoDB berhasil disinkronkan & dimuat ulang!', 'success');
    } catch (err: any) {
      showToast('Gagal menyegarkan data: ' + err.message, 'error');
    } finally {
      setTimeout(() => setIsReloading(false), 500);
    }
  };

  useEffect(() => {
    loadItemsProgressive(selectedFilterTool, selectedCategory, selectedYear);
  }, [selectedFilterTool, selectedCategory, selectedYear]);

  // Crawling execution with real-time feedback & percentage progress
  const handleStartCrawl = async () => {
    if (!keyword.trim() || selectedTools.length === 0) return;
    setIsLoading(true);

    const initialStatuses: Record<string, any> = {};
    selectedTools.forEach(tId => {
      const toolInfo = ALL_TOOLS.find(t => t.id === tId);
      initialStatuses[tId] = {
        status: 'pending',
        count: 0,
        name: toolInfo ? toolInfo.name : tId
      };
    });

    setCrawlProgress({
      isActive: true,
      isComplete: false,
      totalTools: selectedTools.length,
      completedTools: 0,
      currentToolName: 'Menyiapkan crawler...',
      totalCollected: 0,
      percent: 0,
      toolStatuses: initialStatuses
    });

    let runningCollected = 0;
    let completedCount = 0;

    for (const toolId of selectedTools) {
      const toolInfo = ALL_TOOLS.find(t => t.id === toolId);
      const toolName = toolInfo ? toolInfo.name : toolId;

      // Update current tool to 'running'
      setCrawlProgress(prev => ({
        ...prev,
        currentToolName: toolName,
        toolStatuses: {
          ...prev.toolStatuses,
          [toolId]: { ...prev.toolStatuses[toolId], status: 'running' }
        }
      }));

      try {
        const res = await api.runSingleScraper(toolId, keyword, countPerTool, yearRange);
        const count = res.count || 0;
        const toolStatus = res.status === 'error' ? 'error' : (count > 0 ? 'success' : 'empty');
        runningCollected += count;
        completedCount++;

        const currentPercent = Math.round((completedCount / selectedTools.length) * 100);

        setCrawlProgress(prev => ({
          ...prev,
          completedTools: completedCount,
          totalCollected: runningCollected,
          percent: currentPercent,
          toolStatuses: {
            ...prev.toolStatuses,
            [toolId]: { ...prev.toolStatuses[toolId], status: toolStatus, count, message: res.message || '' }
          }
        }));

        // Incremental soft refresh guarded by fetch sequence
        const seq = ++fetchSeqRef.current;
        api.getItems({ limit: 50000, tool_source: selectedFilterTool, category: selectedCategory, year: selectedYear })
          .then(it => {
            if (seq === fetchSeqRef.current) setItems(it.items);
          })
          .catch(() => {});

      } catch (err: any) {
        completedCount++;
        const currentPercent = Math.round((completedCount / selectedTools.length) * 100);

        setCrawlProgress(prev => ({
          ...prev,
          completedTools: completedCount,
          percent: currentPercent,
          toolStatuses: {
            ...prev.toolStatuses,
            [toolId]: { ...prev.toolStatuses[toolId], status: 'error', count: 0, message: err?.message || 'Request error' }
          }
        }));
      }
    }

    // Mark completed
    setCrawlProgress(prev => ({
      ...prev,
      isActive: false,
      isComplete: true,
      percent: 100
    }));

    setIsLoading(false);
    if (runningCollected > 0) {
      showToast(`Crawling selesai! Total ${runningCollected} data berhasil dikumpulkan. Siap diunduh sebagai .CSV atau .JSON.`, 'success');
    } else {
      showToast('Crawling selesai namun 0 data terkumpul (cek status tiap tool atau pesan error API).', 'error');
    }
    await refreshData();
  };

  // Clear dataset
  const handleClearDb = async () => {
    try {
      const res = await api.clearDataset();
      showToast(`Database berhasil dikosongkan (${res.deleted_count} data dihapus).`, 'success');
      await refreshData();
    } catch (err: any) {
      showToast(`Gagal membersihkan database: ${err.message}`, 'error');
    }
  };

  const totalDocuments = stats?.total_documents || items.length;

  return (
    <div className="min-h-screen bg-[#090d16] text-slate-100 flex flex-col font-['Plus_Jakarta_Sans',sans-serif]">
      {/* Toast Alert */}
      {toastMessage && (
        <div className="fixed top-16 right-4 sm:right-6 z-50 animate-fadeIn">
          <div className={`flex items-center gap-2 px-4 py-2.5 rounded-xl shadow-2xl border text-xs font-semibold backdrop-blur-md ${
            toastMessage.type === 'success'
              ? 'bg-emerald-950/95 text-emerald-200 border-emerald-600/50'
              : 'bg-red-950/95 text-red-200 border-red-600/50'
          }`}>
            {toastMessage.type === 'success' ? (
              <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
            ) : (
              <AlertCircle className="w-4 h-4 text-red-400 shrink-0" />
            )}
            <span>{toastMessage.text}</span>
          </div>
        </div>
      )}

      {/* Clean Navbar with Custom JinwooCrawl Logo */}
      <Header />

      {/* Main Workspace (Expansive, Flat, Tanpa 2 Container Penyekap yang Berat) */}
      <main className="flex-1 w-full px-4 sm:px-8 lg:px-12 py-5 sm:py-6">
        {/* Core Crawling Bar (Baris 1: Search + Filter, Baris 2: Target Angka + Rentang Tahun + Crawl) */}
        <CrawlCommandBar
          keyword={keyword}
          onKeywordChange={setKeyword}
          selectedTools={selectedTools}
          onSelectedToolsChange={setSelectedTools}
          countPerTool={countPerTool}
          onCountChange={setCountPerTool}
          yearRange={yearRange}
          onYearRangeChange={setYearRange}
          onStartCrawl={handleStartCrawl}
          onClearDb={handleClearDb}
          isLoading={isLoading}
          totalDocs={totalDocuments}
        />

        {/* Real-time Percentage & Loading Animation Feedback */}
        <CrawlProgressBar
          progress={crawlProgress}
          onClose={() => setCrawlProgress(prev => ({ ...prev, isComplete: false }))}
        />

        {/* Dataset Cards Grid (16:9 Thumbnail, Filter Tahun & Kategori, Klik untuk Modal Rinci Center) */}
        <DatasetCards
          items={items}
          totalCount={totalDocuments}
          onRefresh={handleReload}
          isLoading={isReloading || isLoading}
          isFetching={isFetchingItems}
          selectedTool={selectedFilterTool}
          onSelectTool={setSelectedFilterTool}
          selectedCategory={selectedCategory}
          onSelectCategory={setSelectedCategory}
          selectedYear={selectedYear}
          onSelectYear={setSelectedYear}
          onSelectItem={(item) => setSelectedItem(item)}
        />
      </main>

      {/* Center Modal Popup Dataset Detail */}
      <ItemDetailModal
        item={selectedItem}
        onClose={() => setSelectedItem(null)}
      />

      {/* Minimal Footer */}
      <footer className="border-t border-slate-800/80 bg-slate-950/80 py-3.5 px-4 text-center text-xs text-slate-500 mt-auto">
        <div className="w-full flex flex-col sm:flex-row items-center justify-between gap-2 px-2 sm:px-6">
          <span>
            JinwooCrawl &copy; 2026 • Proyek Akhir Big Data (Mata Kuliah S1 Informatika UNESA)
          </span>
          <div className="flex items-center gap-2 text-slate-400 font-mono text-[11px]">
            <span className="text-emerald-400 font-semibold">Apache Spark (CSV)</span>
            <span>•</span>
            <span className="text-blue-400 font-semibold">Hadoop HDFS (JSON)</span>
          </div>
        </div>
      </footer>
    </div>
  );
};
