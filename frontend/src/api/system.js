import request from './request'

export function getHealth() {
  return request.get('/system/health')
}

export function getSystemInfo() {
  return request.get('/system/info')
}

export function getPublicConstants() {
  return request.get('/system/constants')
}