import request from './request'

export function listProviders() {
  return request.get('/provider/list')
}

export function createProvider(data) {
  return request.post('/provider', data)
}

export function updateProvider(id, data) {
  return request.put(`/provider/${id}`, data)
}

export function deleteProvider(id) {
  return request.delete(`/provider/${id}`)
}
