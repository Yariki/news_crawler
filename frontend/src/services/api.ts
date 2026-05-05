import axios from 'axios'

const configuredApiOrigin = import.meta.env.VITE_API_ORIGIN?.trim()

const apiBaseUrl = configuredApiOrigin
    ? `${configuredApiOrigin.replace(/\/$/, '')}/api`
    : '/api'

export const api = axios.create({
    baseURL: apiBaseUrl,
})

export function getAlertsWebSocketUrl(): string {
    const configuredWsOrigin = import.meta.env.VITE_WS_ORIGIN?.trim()

    if (configuredWsOrigin) {
        return `${configuredWsOrigin.replace(/\/$/, '')}/api/ws/alerts`
    }

    if (typeof window !== 'undefined') {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
        return `${protocol}//${window.location.host}/api/ws/alerts`
    }

    return 'ws://localhost:8000/api/ws/alerts'
}
