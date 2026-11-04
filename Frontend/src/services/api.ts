const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL || '/api/v1').replace(/\/+$/, '')
const apiOrigin = apiBaseUrl.replace(/\/api\/v1$/, '')
const SESSION_STORAGE_KEY = 'life-purpose-auth-session'

export type ServiceHealth = {
  status: string
}

export type UserProfile = {
  id: number
  email: string
  full_name: string | null
  is_active: boolean
  created_at: string
}

export type ItemRecord = {
  id: number
  title: string
  description: string | null
  owner_id: number | null
  created_at: string
}

export type AuthSession = {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number | null
  expires_at: number | null
  user: {
    id: string
    email: string | null
    app_metadata: Record<string, unknown>
  }
}

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

function readSession(): AuthSession | null {
  try {
    const raw = sessionStorage.getItem(SESSION_STORAGE_KEY)
    if (!raw) return null
    const value: unknown = JSON.parse(raw)
    if (
      typeof value === 'object'
      && value !== null
      && 'access_token' in value
      && 'refresh_token' in value
      && typeof value.access_token === 'string'
      && typeof value.refresh_token === 'string'
    ) {
      return value as AuthSession
    }
  } catch {
    sessionStorage.removeItem(SESSION_STORAGE_KEY)
  }
  return null
}

let session: AuthSession | null = readSession()
let refreshInFlight: Promise<AuthSession> | null = null

export function getAuthSession(): AuthSession | null {
  return session
}

function saveAuthSession(value: AuthSession | null): void {
  session = value
  if (value) {
    sessionStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(value))
  } else {
    sessionStorage.removeItem(SESSION_STORAGE_KEY)
  }
}

async function request<T>(
  path: string,
  init: RequestInit = {},
  authenticated = false,
): Promise<T> {
  const firstResponse = await sendRequest(
    path,
    init,
    authenticated ? session?.access_token : undefined,
  )
  if (firstResponse.status === 401 && authenticated && session?.refresh_token) {
    const refreshed = await refreshAuthSession()
    return parseResponse<T>(
      await sendRequest(path, init, refreshed.access_token),
    )
  }
  return parseResponse<T>(firstResponse)
}

async function sendRequest(
  path: string,
  init: RequestInit,
  accessToken?: string,
): Promise<Response> {
  const headers = new Headers(init.headers)
  headers.set('Accept', 'application/json')
  if (init.body && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json')
  }
  if (accessToken) headers.set('Authorization', `Bearer ${accessToken}`)

  const controller = new AbortController()
  const timeoutId = window.setTimeout(() => controller.abort(), 10000)
  try {
    return await fetch(`${apiBaseUrl}${path}`, {
      ...init,
      headers,
      signal: controller.signal,
    })
  } catch (error) {
    if (controller.signal.aborted) {
      throw new ApiError('Backend request timed out.', 0)
    }
    throw new ApiError('Backend is unreachable. Check that the API server is running.', 0)
  } finally {
    window.clearTimeout(timeoutId)
  }
}

async function parseResponse<T>(response: Response): Promise<T> {
  if (response.status === 204) return undefined as T
  let body: unknown
  try {
    body = await response.json()
  } catch {
    body = null
  }
  if (!response.ok) {
    let message = `Backend returned HTTP ${response.status}.`
    if (typeof body === 'object' && body !== null && 'detail' in body) {
      const detail = body.detail
      if (typeof detail === 'string') message = detail
      else if (Array.isArray(detail)) {
        message = detail.map(entry => {
          if (typeof entry === 'object' && entry !== null && 'msg' in entry) {
            return String(entry.msg)
          }
          return 'Invalid request.'
        }).join(' ')
      }
    }
    throw new ApiError(message, response.status)
  }
  return body as T
}

async function refreshAuthSession(): Promise<AuthSession> {
  if (refreshInFlight) return refreshInFlight
  const current = session
  if (!current) throw new ApiError('Your sign-in session has expired.', 401)

  refreshInFlight = (async () => {
    try {
      const refreshed = await request<AuthSession>(
        '/auth/refresh',
        {
          method: 'POST',
          body: JSON.stringify({ refresh_token: current.refresh_token }),
        },
      )
      saveAuthSession(refreshed)
      return refreshed
    } catch (error) {
      if (error instanceof ApiError && (error.status === 400 || error.status === 401)) {
        saveAuthSession(null)
      }
      throw error
    } finally {
      refreshInFlight = null
    }
  })()
  return refreshInFlight
}

async function getStatus(path: string): Promise<ServiceHealth> {
  const controller = new AbortController()
  const timeoutId = window.setTimeout(() => controller.abort(), 8000)
  let response: Response
  try {
    response = await fetch(`${apiOrigin}${path}`, {
      headers: { Accept: 'application/json' },
      signal: controller.signal,
    })
  } catch {
    if (controller.signal.aborted) {
      throw new ApiError('Backend request timed out.', 0)
    }
    throw new ApiError('Backend is unreachable. Check that the API server is running.', 0)
  } finally {
    window.clearTimeout(timeoutId)
  }
  return parseResponse<ServiceHealth>(response)
}

export const getApiHealth = () => getStatus('/health')
export const getApiReadiness = () => getStatus('/ready')

export async function login(email: string, password: string): Promise<AuthSession> {
  const result = await request<AuthSession>(
    '/auth/login',
    { method: 'POST', body: JSON.stringify({ email, password }) },
  )
  saveAuthSession(result)
  return result
}

export async function logout(): Promise<void> {
  try {
    await request<void>('/auth/logout', { method: 'POST' }, true)
  } finally {
    saveAuthSession(null)
  }
}

export const getCurrentUser = () => request<UserProfile>('/auth/me', {}, true)
export const updateCurrentUser = (changes: { full_name: string | null }) =>
  request<UserProfile>('/auth/me', { method: 'PATCH', body: JSON.stringify(changes) }, true)

export const getUsers = (skip = 0, limit = 100) =>
  request<UserProfile[]>(`/users/?skip=${skip}&limit=${limit}`, {}, true)
export const getUser = (id: number) => request<UserProfile>(`/users/${id}`, {}, true)
export const updateUser = (id: number, changes: { full_name?: string | null; is_active?: boolean }) =>
  request<UserProfile>(`/users/${id}`, { method: 'PATCH', body: JSON.stringify(changes) }, true)

export const getItems = (skip = 0, limit = 100) =>
  request<ItemRecord[]>(`/items/?skip=${skip}&limit=${limit}`, {}, true)
export const createItem = (item: { title: string; description: string | null }) =>
  request<ItemRecord>('/items/', { method: 'POST', body: JSON.stringify(item) }, true)
export const updateItem = (id: number, changes: { title?: string; description?: string | null }) =>
  request<ItemRecord>(`/items/${id}`, { method: 'PATCH', body: JSON.stringify(changes) }, true)
export const deleteItem = (id: number) =>
  request<void>(`/items/${id}`, { method: 'DELETE' }, true)

export const apiRoutes = {
  health: `${apiOrigin}/health`,
  readiness: `${apiOrigin}/ready`,
  users: `${apiBaseUrl}/users/`,
  items: `${apiBaseUrl}/items/`,
  internal: `${apiBaseUrl}/internal/*`,
} as const
