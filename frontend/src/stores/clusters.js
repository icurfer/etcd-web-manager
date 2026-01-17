import { defineStore } from 'pinia'
import { clustersApi } from '../api/clusters'

export const useClustersStore = defineStore('clusters', {
  state: () => ({
    clusters: [],
    currentCluster: null,
    loading: false,
    error: null
  }),

  getters: {
    activeClusters: (state) => state.clusters.filter(c => c.is_active)
  },

  actions: {
    async fetchClusters() {
      this.loading = true
      this.error = null
      try {
        const response = await clustersApi.list()
        this.clusters = response.data.results || response.data
      } catch (error) {
        this.error = error.message
        throw error
      } finally {
        this.loading = false
      }
    },

    async fetchCluster(id) {
      this.loading = true
      try {
        const response = await clustersApi.get(id)
        this.currentCluster = response.data
        return response.data
      } catch (error) {
        this.error = error.message
        throw error
      } finally {
        this.loading = false
      }
    },

    async createCluster(data) {
      const response = await clustersApi.create(data)
      this.clusters.push(response.data)
      return response.data
    },

    async updateCluster(id, data) {
      const response = await clustersApi.update(id, data)
      const index = this.clusters.findIndex(c => c.id === id)
      if (index !== -1) {
        this.clusters[index] = response.data
      }
      return response.data
    },

    async deleteCluster(id) {
      await clustersApi.delete(id)
      this.clusters = this.clusters.filter(c => c.id !== id)
    }
  }
})
