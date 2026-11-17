import { DashboardStats, ScrapedItem, ScraperTool, SystemHealth } from '../types';

// Dynamic API Base URL resolution:
// - Local dev (localhost/127.0.0.1) -> http://localhost:5002
// - STB LAN IP (mis. 192.168.100.37:5001) -> http://192.168.100.37:5002
// - Production domain (crawl.jinwoostream.lol) -> baca VITE_API_BASE_URL dari frontend/.env
export const getApiBaseUrl = (): string => {
  const envApiUrl = (import.meta.env.VITE_API_BASE_URL || '').trim().replace(/\/+$/, '');
  if (typeof window !== 'undefined') {
    const host = window.location.hostname;
    if (host === 'localhost' || host === '127.0.0.1') {
      return 'http://localhost:5002';
    }
    if (/^\d{1,3}(\.\d{1,3}){3}$/.test(host)) {
      return `${window.location.protocol}//${host}:5002`;
    }
  }
  return envApiUrl || 'https://scrape.jinwoostream.lol';
};

const BASE_URL = getApiBaseUrl();

async function extractErrorDetail(res: Response, fallback: string): Promise<string> {
  try {
    const body = await res.json();
    if (typeof body?.detail === 'string') return body.detail;
    if (Array.isArray(body?.detail) && body.detail[0]?.msg) {
      return `${body.detail[0].loc?.join('.') || 'input'}: ${body.detail[0].msg}`;
    }
  } catch {
    // ignore non-JSON body
  }
  return `${fallback} (${res.status} ${res.statusText})`;
}

export const api = {
  async getHealth(): Promise<SystemHealth> {
    const res = await fetch(`${BASE_URL}/api/health`);
    if (!res.ok) throw new Error(await extractErrorDetail(res, 'Health check failed'));
    return res.json();
  },

  async getTools(): Promise<{ total_tools: number; tools: ScraperTool[] }> {
    const res = await fetch(`${BASE_URL}/api/scrape/tools`);
    if (!res.ok) throw new Error(await extractErrorDetail(res, 'Failed to load scrapers'));
    return res.json();
  },

  async runSingleScraper(tool: string, keyword: string, count: number = 10, year_range: number = 5): Promise<any> {
    const startRes = await fetch(`${BASE_URL}/api/scrape/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ tool, keyword, count, year_range, save_to_db: true })
    });
    if (!startRes.ok) throw new Error(await extractErrorDetail(startRes, 'Scraper start failed'));
    const { job_id } = await startRes.json();

    let pollErrors = 0;
    while (true) {
      await new Promise(resolve => setTimeout(resolve, 2000));
      try {
        const pollRes = await fetch(`${BASE_URL}/api/scrape/job/${encodeURIComponent(job_id)}`);
        if (!pollRes.ok) {
          if (pollRes.status === 404) {
            throw new Error(await extractErrorDetail(pollRes, 'Scraper job lost'));
          }
          pollErrors++;
          if (pollErrors >= 5) {
            throw new Error(await extractErrorDetail(pollRes, 'Scraper polling failed'));
          }
          continue;
        }
        pollErrors = 0;
        const jobData = await pollRes.json();
        if (jobData.status === 'done') {
          return jobData.result;
        }
      } catch (err: any) {
        if (err?.message?.includes('job lost')) throw err;
        pollErrors++;
        if (pollErrors >= 5) throw err;
      }
    }
  },

  async runSelectedScrapers(tools: string[], keyword: string, count_per_tool: number = 10, year_range: number = 5): Promise<any> {
    const res = await fetch(`${BASE_URL}/api/scrape/selected`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ tools, keyword, count_per_tool, year_range, save_to_db: true })
    });
    if (!res.ok) throw new Error(await extractErrorDetail(res, 'Selected crawl failed'));
    return res.json();
  },

  async runAllScrapers(keyword: string, count_per_tool: number = 8, year_range: number = 5): Promise<any> {
    const res = await fetch(`${BASE_URL}/api/scrape/all`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ keyword, count_per_tool, year_range, save_to_db: true })
    });
    if (!res.ok) throw new Error(await extractErrorDetail(res, 'Unified crawl failed'));
    return res.json();
  },

  async getItems(params: {
    limit?: number;
    skip?: number;
    tool_source?: string;
    keyword?: string;
    category?: string;
    year?: string;
  } = {}): Promise<{ count: number; items: ScrapedItem[] }> {
    const q = new URLSearchParams();
    if (params.limit) q.set('limit', params.limit.toString());
    if (params.skip) q.set('skip', params.skip.toString());
    if (params.tool_source && params.tool_source !== 'all') q.set('tool_source', params.tool_source);
    if (params.keyword) q.set('keyword', params.keyword);
    if (params.category && params.category !== 'all') q.set('category', params.category);
    if (params.year && params.year !== 'all') q.set('year', params.year);

    const res = await fetch(`${BASE_URL}/api/data/items?${q.toString()}`);
    if (!res.ok) throw new Error(`Failed to fetch items: ${res.statusText}`);
    return res.json();
  },

  async getStats(): Promise<DashboardStats> {
    const res = await fetch(`${BASE_URL}/api/data/stats`);
    if (!res.ok) throw new Error(`Failed to fetch stats: ${res.statusText}`);
    return res.json();
  },

  async reloadData(): Promise<any> {
    const res = await fetch(`${BASE_URL}/api/data/reload`, { method: 'POST' });
    if (!res.ok) throw new Error(`Failed to reload data: ${res.statusText}`);
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
