import request from './request'

export function listChatRoles() {
  return request.get('/chat-role/list')
}

export function createChatRole(data) {
  return request.post('/chat-role', data)
}

export function updateChatRole(id, data) {
  return request.put(`/chat-role/${id}`, data)
}

export function deleteChatRole(id) {
  return request.delete(`/chat-role/${id}`)
}
