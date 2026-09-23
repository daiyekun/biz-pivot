import request from './request'

export function getMenuTree() {
  return request.get('/menu/tree')
}

export function getRoleMenus(roleId) {
  return request.get(`/menu/role/${roleId}`)
}

export function saveRoleMenus(roleId, menuIds) {
  return request.put(`/menu/role/${roleId}`, { menu_ids: menuIds })
}

export function getRoleCategories(roleId) {
  return request.get(`/menu/role/${roleId}/categories`)
}

export function saveRoleCategories(roleId, categoryIds) {
  return request.put(`/menu/role/${roleId}/categories`, { category_ids: categoryIds })
}

export function getMyMenus() {
  return request.get('/menu/mine')
}
