import client from './client'

export const clustersApi = {
  list() {
    return client.get('/clusters/')
  },

  get(id) {
    return client.get(`/clusters/${id}/`)
  },

  create(data) {
    return client.post('/clusters/', data)
  },

  update(id, data) {
    return client.patch(`/clusters/${id}/`, data)
  },

  delete(id) {
    return client.delete(`/clusters/${id}/`)
  },

  getStatus(id) {
    return client.get(`/clusters/${id}/status/`)
  },

  testConnection(id) {
    return client.post(`/clusters/${id}/test_connection/`)
  },

  validateKubeconfig(kubeconfig) {
    return client.post('/clusters/validate_kubeconfig/', { kubeconfig })
  }
}
