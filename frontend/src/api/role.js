import request from './request'

export function listRoles(params) {
  return request.get('/role', { params })
}

export function listAllRoles() {
  return request.get('/role/all')
}

export function createRole(data) {
  return request.post('/role', data)
}

export function updateRole(id, data) {
  return request.put(`/role/${id}`, data)
}

export function deleteRole(id) {
  return request.delete(`/role/${id}`)
}
