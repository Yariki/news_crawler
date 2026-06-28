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
    Status,
} from "../models/types";

const sortJobsByStartedAtDesc = (jobs: JobItem[]): JobItem[] => {
    return [...jobs].sort((a, b) => {
        const aTime = Date.parse(a.started_at)
        const bTime = Date.parse(b.started_at)
        return bTime - aTime
    })
}


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
            scrape_interval_minutes: 60,
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
          const response = await api.post(`/sources/${sourceId}/run`)
          await this.refreshAll();
          return response.data;
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
                const message = JSON.parse(event.data)
                const message_type = message.type
                if (message_type === 'KEYWORDS_MATCH') {
                    this.processAlertMessage(message.payload)
                } else if (message_type === 'JOB_UPDATE') {
                    this.processJobUpdateMessage(message.payload)
                }
            }
            this.ws = ws
        },
        processAlertMessage(message: KeywordsMatchMessage) {
            this.alerts.unshift(message)
            this.alerts = this.alerts.slice(0, 20)
        },
        processJobUpdateMessage(message: JobUpdateMessage) {
            let job = this.jobs.find((job) => job.id === message.job_id)
            if (!job) {
                this.jobs.push({
                    id: message.job_id,
                    source_id: message.source_id,
                    status: message.status,
                    articles_created: message.articles_created,
                    articles_found: message.articles_found,
                    error_message: message.status === Status.Failed ? message.error_message : null,
                    started_at: message.started_at,
                    finished_at: message.finished_at,
                })
              this.jobs = sortJobsByStartedAtDesc(this.jobs)
              return;
            }

            job.status = message.status;
            job.articles_created = message.articles_created;
            job.articles_found = message.articles_found;
            job.error_message = message.status === Status.Failed ? message.error_message : null;
            job.started_at = message.started_at;
            job.finished_at = message.finished_at;


        },
        async refreshJobs() {
            this.loading = true;
            try{
                const jobs = await api.get('/dashboard/jobs');
                this.jobs = jobs && jobs.data ? jobs.data : [];
            }catch(e){
                console.error(e);
            }finally {
                this.loading = false;
            }
        },
    },
})
