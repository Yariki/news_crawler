
export const SourceTypes = [
  { value: 1, label: 'News Site' },
  { value: 2, label: 'Blog' },
  { value: 3, label: 'Forum' },
  { value: 4, label: 'Social Media' },
  { value: 5, label: 'Telegram Channel' },
  { value: 6, label: 'Whatsapp Channel' },
  { value: 7, label: 'Other' },
];

export const Statuses = [
  { value: 1, label: 'Running' },
  { value: 2, label: 'Completed' },
  { value: 3, label: 'Failed' },
  { value: 4, label: 'Waiting' },
  { value: 5, label: 'Cancelled' },
];

export enum SourseType {
  Unknown = 0,
  NewsSite = 1,
  Blog = 2,
  Forum = 3,
  SocialMedia = 4,
  TelegramChannel = 5,
  WhatsappChannel = 6,
  Other = 7
}

export enum  Status {
  Running = 1,
  Completed = 2,
  Failed = 3,
  Waiting = 4,
  Cancelled = 5,
}

export interface SourceItem {
  id: string
  name: string
  base_url: string
  language: string
  source_type: SourseType
  crawler_key: string
  is_enabled: boolean
  scrape_interval_minutes: number
}

// Monitored keywords
export interface KeywordItem { 
  id: string
  keyword: string
  is_enabled: boolean
}

export interface JobItem {
  id: string
  source_id: string
  status: Status
  started_at: string
  finished_at: string | null
  articles_found: number
  articles_created: number
  error_message: string | null
}

export interface SearchHit {
  article_id: string
  title: string
  url: string
  published_at: string | null
  source_name: string
  excerpt: string | null
  score: number | null
  is_alert: boolean
}

export interface CrawlerTypeItem {
  key: string
  title: string
  description: string
}

export interface DashboardStats {
  sources_total: number
  sources_enabled: number
  articles_total: number
  alerts_total: number
  jobs_total: number
  keywords_total: number
  elasticsearch_document_count: number
}

export interface CreateSourcePayload {
  name: string
  base_url: string
  language: string
  source_type: SourseType
  crawler_key: string
  scrape_interval_minutes: number
  is_enabled: boolean
}

export interface ArticleItem {
  id: string
  source_id: string
  url: string
  title: string
  author: string | null
  published_at: string | null
  fetched_at: string
  content_text: string
  summary: string | null
  language: string
  is_alert: boolean
  matched_keywords_csv: string | null
}