import client from './client'

export const authApi = {
  async getCsrf() {
    return client.get('/auth/csrf/')
  },

  async login(username, password) {
    await this.getCsrf()
    return client.post('/auth/login/', { username, password })
  },

  async logout() {
    return client.post('/auth/logout/')
  },

  async me() {
    return client.get('/auth/me/')
  }
}
