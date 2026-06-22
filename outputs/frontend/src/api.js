import { reactive } from 'vue'
export const session = reactive({ token: localStorage.getItem('token') || '', user: JSON.parse(localStorage.getItem('user') || 'null') })
export const canEdit = () => ['engineer', 'executive'].includes(session.user?.role)
export const isExecutive = () => session.user?.role === 'executive'
export const canManagePurpose = () => ['executive', 'server_admin'].includes(session.user?.role)
export async function api(path, options = {}) {
  const headers = options.body instanceof FormData ? {} : { 'Content-Type': 'application/json' }
  if (session.token) headers.Authorization = `Bearer ${session.token}`
  const res = await fetch(`/api${path}`, { ...options, headers: { ...headers, ...options.headers } })
  if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || '요청을 처리하지 못했습니다.')
  if (res.status === 204) return null
  return res.json()
}
export async function apiBlob(path) {
  const target = path.startsWith('/api/') ? path : `/api${path}`
  const res = await fetch(target, { headers: { Authorization: `Bearer ${session.token}` } })
  if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || '파일을 불러오지 못했습니다.')
  return res.blob()
}
export async function signIn(username, password) {
  const data = await api('/auth/login', { method: 'POST', body: JSON.stringify({ username, password }) })
  session.token = data.access_token; session.user = data.user
  localStorage.setItem('token', data.access_token); localStorage.setItem('user', JSON.stringify(data.user))
}
export function signOut() { session.token = ''; session.user = null; localStorage.clear() }
