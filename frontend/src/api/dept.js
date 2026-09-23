import request from './request'

export function getDeptTree() {
  return request.get('/dept/tree')
}

export function createDept(data) {
  return request.post('/dept', data)
}

export function updateDept(id, data) {
  return request.put(`/dept/${id}`, data)
}

export function deleteDept(id) {
  return request.delete(`/dept/${id}`)
}
