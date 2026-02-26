const BASE = ''

async function request(method, path, token, body) {
  const headers = { 'Content-Type': 'application/json' }
  if (token) headers['Authorization'] = `Bearer ${token}`
  const res = await fetch(`${BASE}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || 'Request failed')
  }
  return res.json()
}

export default {
  get: (path, token) => request('GET', path, token),
  post: (path, body, token) => request('POST', path, token, body),
  put: (path, body, token) => request('PUT', path, token, body),
  delete: (path, token) => request('DELETE', path, token),
}
