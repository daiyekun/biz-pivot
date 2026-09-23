import request from './request'

export function getCategoryTree() {
  return request.get('/category/tree')
}
