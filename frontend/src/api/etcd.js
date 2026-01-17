import client from './client'

export const etcdApi = {
  getKeys(clusterId, params = {}) {
    return client.get(`/etcd/${clusterId}/keys/`, { params })
  },

  getTree(clusterId, params = {}) {
    return client.get(`/etcd/${clusterId}/tree/`, { params })
  },

  getValue(clusterId, key) {
    return client.get(`/etcd/${clusterId}/kv/`, { params: { key } })
  },

  putValue(clusterId, key, value) {
    return client.post(`/etcd/${clusterId}/kv/`, { key, value })
  },

  deleteKey(clusterId, key, prefix = false) {
    return client.delete(`/etcd/${clusterId}/kv/`, { data: { key, prefix } })
  },

  getHealth(clusterId) {
    return client.get(`/etcd/${clusterId}/health/`)
  }
}
