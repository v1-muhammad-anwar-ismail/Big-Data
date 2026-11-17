export interface ScraperTool {
  id: string;
  name: string;
  platform: string;
  type: string;
  auth_required: boolean;
  auth_status: string;
  description: string;
}

export interface ScrapedMetrics {
  views: number;
  likes: number;
  comments: number;
  shares: number;
  sentiment_tone: number;
}

export interface ScrapedItem {
  id: string;
  _id?: string;
  tool_source: string;
  platform: string;
  keyword: string;
  category: string;
  title: string;
  content: string;
  url: string;
  thumbnail_url?: string;
  author_or_source: string;
  published_at: string;
  published_date: string;
  metrics: ScrapedMetrics;
  collected_at?: string;
}

export interface TimelineDataPoint {
  date: string;
  count: number;
  avg_tone: number;
}

export interface DashboardStats {
  total_documents: number;
  tools: Record<string, number>;
  platforms: Record<string, number>;
  categories: Record<string, number>;
  timeline: TimelineDataPoint[];
}

export interface SystemHealth {
  app: string;
  environment: string;
  backend_port: number;
  frontend_port: number;
  backend_domain: string;
  frontend_domain: string;
  database: {
    status: string;
    database: string;
    collection: string;
    total_documents: number;
    message?: string;
  };
}
