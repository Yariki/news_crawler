export { api, authClient } from '../lib/axios'

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
