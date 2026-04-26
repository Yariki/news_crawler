import { defineStore } from 'pinia'
import { api } from '../services/api'
import {
  CrawlerTypeItem,
  CreateSourcePayload,
  DashboardStats,
  JobItem,
  KeywordItem,
  SearchHit,
  SourceItem
} from "../models/types";


export const useAppStore = defineStore('app', {
  state: () => ({
    initialized: false,
    loading: false,
    stats: null as DashboardStats | null,
    sources: [] as SourceItem[],
    keywords: [] as KeywordItem[],
    jobs: [] as JobItem[],
    searchHits: [] as SearchHit[],
    crawlerTypes: [] as CrawlerTypeItem[],
    alerts: [] as any[],
    searchQuery: '',
    newKeyword: '',
    sourceForm: {
      name: '',
      base_url: '',
      language: 'ru',
      source_type: 1,
      crawler_key: 'themoscowtimes_ru',
      scrape_interval_minutes: 1440,
      is_enabled: true,
    } as CreateSourcePayload,
    ws: null as WebSocket | null,
  }),
  getters: {
    jobsWithSource(state) {
      return state.jobs.map((job) => ({
        ...job,
        source_name: state.sources.find((source) => source.id === job.source_id)?.name || `#${job.source_id}`,
      }))
    },
  },
  actions: {
    async refreshAll() {
      this.loading = true
      try {
        const [stats, sources, keywords, jobs, crawlerTypes] = await Promise.all([
          api.get('/dashboard/stats'),
          api.get('/sources'),
          api.get('/keywords'),
          api.get('/dashboard/jobs'),
          api.get('/crawler-types'),
        ])
        this.stats = stats.data
        this.sources = sources.data
        this.keywords = keywords.data
        this.jobs = jobs.data
        this.crawlerTypes = crawlerTypes.data
        this.initialized = true
      } finally {
        this.loading = false
      }
    },
    async runSource(sourceId: number) {
      await api.post(`/sources/${sourceId}/run`)
      await this.refreshAll()
    },
    async addKeyword() {
      if (!this.newKeyword.trim()) return
      await api.post('/keywords', { keyword: this.newKeyword.trim() })
      this.newKeyword = ''
      await this.refreshAll()
    },
    async deleteKeyword(keywordId: string) {
      await api.delete(`/keywords/${keywordId}`)
      await this.refreshAll()
    },
    async search() {
      if (!this.searchQuery.trim()) {
        this.searchHits = []
        return
      }
      const response = await api.get('/search', { params: { q: this.searchQuery } })
      this.searchHits = response.data
    },
    async createSource() {
      await api.post('/sources', this.sourceForm)
      this.sourceForm = {
        name: '',
        base_url: '',
        language: 'ru',
        source_type: 1,
        crawler_key: this.crawlerTypes[0]?.key || 'themoscowtimes_ru',
        scrape_interval_minutes: 1440,
        is_enabled: true,
      }
      await this.refreshAll()
    },
    connectAlerts() {
      if (this.ws) return
      const ws = new WebSocket('ws://localhost:8000/api/ws/alerts')
      ws.onopen = () => {
        ws.send('ping')
        setInterval(() => ws.readyState === WebSocket.OPEN && ws.send('ping'), 15000)
      }
      ws.onmessage = (event) => {
        const message = JSON.parse(event.data)
        this.alerts.unshift(message.payload)
        this.alerts = this.alerts.slice(0, 20)
      }
      this.ws = ws
    },
  },
})
