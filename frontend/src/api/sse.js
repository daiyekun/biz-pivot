import { useUserStore } from '@/stores/user'

/**
 * 基于 fetch 的 SSE 流式请求封装（后端 core/sse_generator.py 协议）
 *
 * 事件格式：
 *   event: <type>
 *   data: <json>
 *
 * @param {string} url        相对路径，如 '/chat/stream'
 * @param {object} options    { method, body, signal, onEvent }
 *   onEvent(event, data) 每收到一条事件回调
 */
export async function fetchSSE(url, { method = 'POST', body, signal, onEvent } = {}) {
  const userStore = useUserStore()
  const resp = await fetch(`/api/v1${url}`, {
    method,
    headers: {
      'Content-Type': 'application/json',
      Authorization: userStore.token ? `Bearer ${userStore.token}` : '',
    },
    body: body ? JSON.stringify(body) : undefined,
    signal,
  })

  if (!resp.ok) {
    const err = new Error(`请求失败：${resp.status}`)
    err.status = resp.status
    throw err
  }

  const reader = resp.body.getReader()
  const decoder = new TextDecoder('utf-8')
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })

    let idx
    while ((idx = buffer.indexOf('\n\n')) !== -1) {
      const chunk = buffer.slice(0, idx)
      buffer = buffer.slice(idx + 2)

      let event = 'message'
      let data = ''
      for (const line of chunk.split('\n')) {
        if (line.startsWith('event:')) event = line.slice(6).trim()
        else if (line.startsWith('data:')) data += line.slice(5).trim()
      }
      if (!data) continue

      let parsed
      try {
        parsed = JSON.parse(data)
      } catch {
        parsed = data
      }
      if (onEvent) onEvent(event, parsed)
    }
  }
}