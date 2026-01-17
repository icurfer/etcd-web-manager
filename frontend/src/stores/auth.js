import { defineStore } from 'pinia'
import { authApi } from '../api/auth'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
    isInitialized: false
  }),

  getters: {
    isAuthenticated: (state) => !!state.user
  },

  actions: {
    async checkAuth() {
      try {
        const response = await authApi.me()
        this.user = response.data
      } catch (error) {
        this.user = null
      } finally {
        this.isInitialized = true
      }
    },

    async login(username, password) {
      const response = await authApi.login(username, password)
      this.user = response.data
      return response.data
    },

    async logout() {
      try {
        await authApi.logout()
      } finally {
        this.user = null
      }
    }
  }
})
