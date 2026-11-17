import { DashboardStats, ScrapedItem, ScraperTool, SystemHealth } from '../types';

// Dynamic API Base URL resolution:
// If accessed via production domain 'crawl.jinwoostream.lol', point to 'https://scrape.jinwoostream.lol'
// If local, point to 'http://localhost:5002'
export const getApiBaseUrl = (): string => {
  if (typeof window !== 'undefined') {
    const host = window.location.hostname;
    if (host.includes('jinwoostream.lol')) {
      return 'https://scrape.jinwoostream.lol';
    }
  }
  return 'http://localhost:5002';
};

const BASE_URL = getApiBaseUrl();

export const api = {
  async getHealth(): Promise<SystemHealth> {
    const res = await fetch(`${BASE_URL}/api/health`);
    if (!res.ok) throw new Error(`Health check failed: ${res.statusText}`);
    return res.json();
  },

  async getTools(): Promise<{ total_tools: number; tools: ScraperTool[] }> {
    const res = await fetch(`${BASE_URL}/api/scrape/tools`);
    if (!res.ok) throw new Error(`Failed to load scrapers: ${res.statusText}`);
    return res.json();
  },

  async runSingleScraper(tool: string, keyword: string, count: number = 10): Promise<any> {
    const res = await fetch(`${BASE_URL}/api/scrape/single`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ tool, keyword, count, save_to_db: true })
    });
    if (!res.ok) throw new Error(`Scraper execution failed: ${res.statusText}`);
    return res.json();
  },

  async runAllScrapers(keyword: string, count_per_tool: number = 8): Promise<any> {
    const res = await fetch(`${BASE_URL}/api/scrape/all`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ keyword, count_per_tool, save_to_db: true })
    });
    if (!res.ok) throw new Error(`Unified crawl failed: ${res.statusText}`);
    return res.json();
  },

  async getItems(params: {
    limit?: number;
    skip?: number;
    tool_source?: string;
    keyword?: string;
    category?: string;
  } = {}): Promise<{ count: number; items: ScrapedItem[] }> {
    const q = new URLSearchParams();
    if (params.limit) q.set('limit', params.limit.toString());
    if (params.skip) q.set('skip', params.skip.toString());
    if (params.tool_source && params.tool_source !== 'all') q.set('tool_source', params.tool_source);
    if (params.keyword) q.set('keyword', params.keyword);
    if (params.category && params.category !== 'all') q.set('category', params.category);

    const res = await fetch(`${BASE_URL}/api/data/items?${q.toString()}`);
    if (!res.ok) throw new Error(`Failed to fetch items: ${res.statusText}`);
    return res.json();
  },

  async getStats(): Promise<DashboardStats> {
    const res = await fetch(`${BASE_URL}/api/data/stats`);
    if (!res.ok) throw new Error(`Failed to fetch stats: ${res.statusText}`);
    return res.json();
  },

  async clearDataset(): Promise<{ deleted_count: number }> {
    const res = await fetch(`${BASE_URL}/api/data/clear`, {
      method: 'DELETE'
    });
    if (!res.ok) throw new Error(`Failed to clear dataset: ${res.statusText}`);
    return res.json();
  },

  getExportJsonUrl(): string {
    return `${BASE_URL}/api/data/export/json`;
  },

  getExportCsvUrl(): string {
    return `${BASE_URL}/api/data/export/csv`;
  }
};
