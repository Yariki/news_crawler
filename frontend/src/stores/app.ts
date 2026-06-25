import {defineStore} from 'pinia'
import {api, getAlertsWebSocketUrl} from '../services/api'
import {
    CrawlerTypeItem,
    CreateSourcePayload,
    DashboardStats,
    JobItem,
    KeywordItem,
    SearchHit,
    SourceItem,
    JobUpdateMessage,
    KeywordsMatchMessage,
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
            crawler_key: '',
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
                const [stats, sources, keywords, jobs] = await Promise.all([
                    api.get('/dashboard/stats'),
                    api.get('/sources'),
                    api.get('/keywords'),
                    api.get('/dashboard/jobs'),
                    //api.get('/crawler-types'),
                ])
                this.stats = stats.data
                this.sources = sources.data
                this.keywords = keywords.data
                this.jobs = jobs.data
                this.initialized = true
            } finally {
                this.loading = false
            }
        },
        async runSource(sourceId: string) {
            await api.post(`/sources/${sourceId}/run`)
            await this.refreshAll()
        },
        async addKeyword() {
            if (!this.newKeyword.trim()) return
            await api.post('/keywords', {keyword: this.newKeyword.trim()})
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
            const response = await api.get('/articles/search', {params: {q: this.searchQuery}})
            this.searchHits = response.data
        },
        async createSource() {
            await api.post('/sources', this.sourceForm)
            this.sourceForm = {
                name: '',
                base_url: '',
                language: 'ru',
                source_type: 1,
                crawler_key: this.crawlerTypes[0]?.key || '',
                scrape_interval_minutes: 1440,
                is_enabled: true,
            }
            await this.refreshAll()
        },
        connectAlerts() {
            if (this.ws) return
            const ws = new WebSocket(getAlertsWebSocketUrl())
            ws.onopen = () => {
                ws.send('ping')
                setInterval(() => ws.readyState === WebSocket.OPEN && ws.send('ping'), 15000)
            }
            ws.onmessage = (event) => {
                //TODO: implement processing messages  from the server.
                // There are two types of messages: "alert" and "job_update". For now, we only process "alert" messages.
                const message_type = JSON.parse(event.data).message_type
                if (message_type === 'KEYWORDS_MATCH') {
                    this.processAlertMessage(JSON.parse(event.data))
                } else if (message_type === 'JOB_UPDATE') {
                    this.processJobUpdateMessage(JSON.parse(event.data))
                }
            }
            this.ws = ws
        },
        processAlertMessage(message: KeywordsMatchMessage) {
            this.alerts.unshift(message)
            this.alerts = this.alerts.slice(0, 20)
        },
        processJobUpdateMessage(message: JobUpdateMessage) { 
            const job = this.jobs.find((job) => job.id === message.job_id)
            if (!job) {
                return;
            }
            job.status = message.status;
            job.articles_created = message.articles_created;
            job.articles_found = message.articles_found;
            job.error_message = message.status === 'FAILED' ? message.error_message : null;
            job.started_at = message.started_at;
            job.finished_at = message.finished_at;
        },
        async refreshJobs() {
            this.loading = true;
            try{
                const jobs = await api.get('/dashboard/jobs');
            }catch(e){
                console.error(e);
            }finally {
                this.loading = false;
            }
        },
    },
})
