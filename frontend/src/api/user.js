import request from './request'

export function listUsers(params) {
  return request.get('/user', { params })
}

export function createUser(data) {
  return request.post('/user', data)
}

export function updateUser(id, data) {
  return request.put(`/user/${id}`, data)
}

export function deleteUser(id) {
  return request.delete(`/user/${id}`)
}

export function resetPassword(id, password) {
  return request.put(`/user/${id}/password`, { password })
}

export function setUserState(id, state) {
  return request.put(`/user/${id}/state`, { state })
}
