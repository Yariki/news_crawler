
export interface SourceItem {
  id: number
  name: string
  base_url: string
  language: string
  source_type: string
  crawler_key: string
  is_enabled: boolean
  scrape_interval_minutes: number
}

export interface KeywordItem {
  id: number
  keyword: string
  is_enabled: boolean
}

export interface JobItem {
  id: number
  source_id: number
  status: string
  started_at: string
  finished_at: string | null
  articles_found: number
  articles_created: number
  error_message: string | null
}

export interface SearchHit {
  article_id: number
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
  source_type: string
  crawler_key: string
  scrape_interval_minutes: number
  is_enabled: boolean
}

export interface ArticleItem {
  id: number
  source_id: number
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