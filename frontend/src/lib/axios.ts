import axios, {
    AxiosError,
    type AxiosInstance,
    type InternalAxiosRequestConfig,
} from 'axios'

const configuredApiOrigin = import.meta.env.VITE_API_ORIGIN?.trim()

const baseURL = configuredApiOrigin
    ? `${configuredApiOrigin.replace(/\/$/, '')}/api`
    : '/api'

/**
 * Bare client without interceptors. The auth store uses it for /auth/* so a
 * failing refresh cannot re-enter the 401 handler and recurse.
 */
export const authClient: AxiosInstance = axios.create({ baseURL })

/** Application client: attaches the access token and refreshes it on 401. */
export const api: AxiosInstance = axios.create({ baseURL })

interface RetriableConfig extends InternalAxiosRequestConfig {
    _retry?: boolean
}

const AUTH_ENDPOINTS = ['/auth/refresh', '/auth/login', '/auth/logout']

/**
 * Imported lazily inside the interceptors: the active Pinia instance does not
 * exist until createPinia() runs in main.ts, and a module-scope import would
 * close the cycle lib/axios -> stores/auth -> services/api -> lib/axios.
 */
async function authStore() {
    const { useAuthStore } = await import('../stores/auth')
    return useAuthStore()
}

let refreshPromise: Promise<void> | null = null

/**
 * Single-flight refresh. The backend rotates refresh tokens and rejects reuse,
 * so parallel refreshes with the same token would fail all but the first one.
 * Concurrent callers join the in-flight request instead of starting a new one.
 */
function runRefresh(): Promise<void> {
    refreshPromise ??= authStore()
        .then((store) => store.refresh())
        .finally(() => {
            refreshPromise = null
        })

    return refreshPromise
}

async function forceLogout(): Promise<void> {
    const store = await authStore()
    store.clearSession()

    // Clearing the session is what matters; a failed redirect must not mask the
    // original error that triggered the logout.
    try {
        const { default: router } = await import('../router')
        if (router.currentRoute.value.name !== 'login') {
            await router.push({
                name: 'login',
                query: { returnUrl: router.currentRoute.value.fullPath },
            })
        }
    } catch {
        /* navigation is best-effort */
    }
}

api.interceptors.request.use(async (config) => {
    const store = await authStore()

    if (store.access_token) {
        config.headers.set('Authorization', `Bearer ${store.access_token}`)
    }

    return config
})

api.interceptors.response.use(
    (response) => response,
    async (error: AxiosError) => {
        const original = error.config as RetriableConfig | undefined
        const status = error.response?.status

        if (status === 403) {
            const { useMessages } = await import('../stores/messages')
            useMessages().onError("You don't have permission to perform this action")
            return Promise.reject(error)
        }

        if (status !== 401 || !original) {
            return Promise.reject(error)
        }

        const isAuthEndpoint = AUTH_ENDPOINTS.some((path) => original.url?.includes(path))

        // A 401 on the retried request means the fresh access token was rejected
        // too, so the session is dead rather than merely expired.
        if (isAuthEndpoint || original._retry) {
            await forceLogout()
            return Promise.reject(error)
        }

        original._retry = true

        try {
            await runRefresh()
            return await api(original)
        } catch (refreshError) {
            await forceLogout()
            return Promise.reject(refreshError)
        }
    },
)
