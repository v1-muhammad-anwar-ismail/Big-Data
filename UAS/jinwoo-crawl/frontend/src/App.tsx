import React, { useState, useEffect } from 'react';
import { Header } from './components/Header';
import { MetricsBar } from './components/MetricsBar';
import { ScraperControls } from './components/ScraperControls';
import { ScrapersGrid } from './components/ScrapersGrid';
import { IssueTimelineChart } from './components/IssueTimelineChart';
import { DataTable } from './components/DataTable';
import { DeploymentModal } from './components/DeploymentModal';
import { api } from './services/api';
import { DashboardStats, ScrapedItem, ScraperTool, SystemHealth } from './types';
import { CheckCircle2, AlertCircle } from 'lucide-react';

export const App: React.FC = () => {
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [tools, setTools] = useState<ScraperTool[]>([]);
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [items, setItems] = useState<ScrapedItem[]>([]);
  const [keyword, setKeyword] = useState<string>('karhutla');
  const [countPerTool, setCountPerTool] = useState<number>(8);
  
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [loadingTool, setLoadingTool] = useState<string | null>(null);
  const [selectedTool, setSelectedTool] = useState<string>('all');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  
  const [isConfigOpen, setIsConfigOpen] = useState<boolean>(false);
  const [toastMessage, setToastMessage] = useState<{ text: string; type: 'success' | 'error' } | null>(null);

  const showToast = (text: string, type: 'success' | 'error' = 'success') => {
    setToastMessage({ text, type });
    setTimeout(() => setToastMessage(null), 4000);
  };

  // Initial load
  const loadInitialData = async () => {
    try {
      const [h, t, s, it] = await Promise.all([
        api.getHealth().catch(() => null),
        api.getTools().catch(() => ({ total_tools: 0, tools: [] })),
        api.getStats().catch(() => null),
        api.getItems({ limit: 100 }).catch(() => ({ count: 0, items: [] }))
      ]);

      if (h) setHealth(h);
      if (t) setTools(t.tools);
      if (s) setStats(s);
      if (it) setItems(it.items);
    } catch (e) {
      console.error('Error loading initial data:', e);
    }
  };

  useEffect(() => {
    loadInitialData();
  }, []);

  // Reload items & stats
  const refreshData = async () => {
    try {
      const [s, it, h] = await Promise.all([
        api.getStats(),
        api.getItems({
          limit: 100,
          tool_source: selectedTool,
          category: selectedCategory
        }),
        api.getHealth()
      ]);
      setStats(s);
      setItems(it.items);
      setHealth(h);
    } catch (e) {
      console.error('Refresh error:', e);
    }
  };

  useEffect(() => {
    api.getItems({
      limit: 100,
      tool_source: selectedTool,
      category: selectedCategory
    }).then(res => setItems(res.items)).catch(console.error);
  }, [selectedTool, selectedCategory]);

  // Run all 8 scrapers
  const handleRunAll = async () => {
    if (!keyword.trim()) return;
    setIsLoading(true);
    try {
      const res = await api.runAllScrapers(keyword, countPerTool);
      showToast(`Crawl Multikanal Sukses! Berhasil mengumpulkan ${res.total_items} data (${res.total_saved_to_db} tersimpan ke MongoDB).`, 'success');
      await refreshData();
    } catch (err: any) {
      showToast(`Gagal mengeksekusi crawl: ${err.message}`, 'error');
    } finally {
      setIsLoading(false);
    }
  };

  // Run single scraper
  const handleRunSingle = async (toolId: string) => {
    if (!keyword.trim()) return;
    setLoadingTool(toolId);
    try {
      const res = await api.runSingleScraper(toolId, keyword, countPerTool);
      if (res.status === 'success') {
        showToast(`Tool [${toolId}] sukses mengambil ${res.count} data baru!`, 'success');
      } else {
        showToast(`Tool [${toolId}] info: ${res.message || 'Selesai'}`, 'success');
      }
      await refreshData();
    } catch (err: any) {
      showToast(`Error menjalankan tool ${toolId}: ${err.message}`, 'error');
    } finally {
      setLoadingTool(null);
    }
  };

  // Clear MongoDB dataset
  const handleClear = async () => {
    try {
      const res = await api.clearDataset();
      showToast(`Database berhasil dikosongkan (${res.deleted_count} dokumen dihapus).`, 'success');
      await refreshData();
    } catch (err: any) {
      showToast(`Gagal membersihkan database: ${err.message}`, 'error');
    }
  };

  return (
    <div className="min-h-screen bg-[#090d16] text-slate-100 flex flex-col font-['Plus_Jakarta_Sans',sans-serif]">
      {/* Toast Notification */}
      {toastMessage && (
        <div className="fixed top-16 right-6 z-50 animate-slideDown">
          <div className={`flex items-center gap-2.5 px-4 py-3 rounded-xl shadow-2xl border text-xs font-semibold backdrop-blur-md ${
            toastMessage.type === 'success'
              ? 'bg-emerald-950/90 text-emerald-200 border-emerald-600/50'
              : 'bg-red-950/90 text-red-200 border-red-600/50'
          }`}>
            {toastMessage.type === 'success' ? (
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            ) : (
              <AlertCircle className="w-4 h-4 text-red-400" />
            )}
            <span>{toastMessage.text}</span>
          </div>
        </div>
      )}

      {/* Header */}
      <Header
        health={health}
        onOpenConfig={() => setIsConfigOpen(true)}
      />

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 lg:px-8 py-8">
        {/* Metric Counters */}
        <MetricsBar stats={stats} />

        {/* Command Center & Search */}
        <ScraperControls
          keyword={keyword}
          onKeywordChange={setKeyword}
          countPerTool={countPerTool}
          onCountChange={setCountPerTool}
          onRunAll={handleRunAll}
          onClear={handleClear}
          isLoading={isLoading}
        />

        {/* 8 Scrapers Grid Showcase */}
        <ScrapersGrid
          tools={tools}
          onRunSingle={handleRunSingle}
          loadingTool={loadingTool}
          keyword={keyword}
        />

        {/* Issue Attention Cycle Timeline */}
        <IssueTimelineChart
          timeline={stats?.timeline || []}
          keyword={keyword}
        />

        {/* Database Explorer Table */}
        <DataTable
          items={items}
          totalCount={stats?.total_documents || items.length}
          onRefresh={refreshData}
          isLoading={isLoading || Boolean(loadingTool)}
          selectedTool={selectedTool}
          onSelectTool={setSelectedTool}
          selectedCategory={selectedCategory}
          onSelectCategory={setSelectedCategory}
        />
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800/80 bg-slate-950/60 py-6 px-4 text-center text-xs text-slate-500">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-2">
          <span>
            JinwooCrawl &copy; 2026 • Proyek Akhir Mata Kuliah Big Data • S1 Informatika UNESA
          </span>
          <div className="flex items-center gap-4 text-slate-400 font-mono text-[11px]">
            <span>FE: :5001</span>
            <span>BE: :5002</span>
            <span>Hadoop HDFS & Spark MLlib Ready</span>
          </div>
        </div>
      </footer>

      {/* Deployment & .env Guide Modal */}
      <DeploymentModal
        isOpen={isConfigOpen}
        onClose={() => setIsConfigOpen(false)}
      />
    </div>
  );
};
