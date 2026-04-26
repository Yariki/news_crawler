import { defineStore } from 'pinia'
import { api } from '../services/api'
import {ArticleItem, JobItem, KeywordItem, SearchHit, SourceItem} from "../models/types";

export const useDashboardStore = defineStore('dashboard', {
  state: () => ({
    stats: null as any,
    sources: [] as SourceItem[],
    keywords: [] as KeywordItem[],
    jobs: [] as JobItem[],
    recentArticles: [] as ArticleItem[],
    searchHits: [] as SearchHit[],
    alerts: [] as any[],
    searchQuery: '',
    newKeyword: '',
    loading: false,
  }),
  actions: {
    async loadAll() {
      this.loading = true
      try {
        const [stats, sources, keywords, jobs, recentArticles] = await Promise.all([
          api.get('/dashboard/stats'),
          api.get('/sources'),
          api.get('/keywords'),
          api.get('/dashboard/jobs'),
          api.get('/articles/recent?limit=20'),
        ])
        this.stats = stats.data
        this.sources = sources.data
        this.keywords = keywords.data
        this.jobs = jobs.data
        this.recentArticles = recentArticles.data
      } finally {
        this.loading = false
      }
    },
    async runSource(sourceId: number) {
      await api.post(`/sources/${sourceId}/run`)
      await this.loadAll()
    },
    async addKeyword() {
      if (!this.newKeyword.trim()) return
      await api.post('/keywords', { keyword: this.newKeyword.trim() })
      this.newKeyword = ''
      await this.loadAll()
    },
    async deleteKeyword(keywordId: string) {
      await api.delete(`/keywords/${keywordId}`)
      await this.loadAll()
    },
    async search() {
      if (!this.searchQuery.trim()) {
        this.searchHits = []
        return
      }
      const response = await api.get('/search', { params: { q: this.searchQuery } })
      this.searchHits = response.data
    },
    connectAlerts() {
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
    },
  },
})
