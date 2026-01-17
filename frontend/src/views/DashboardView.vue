<template>
  <div>
    <h1 class="text-h4 mb-6">Dashboard</h1>

    <v-row>
      <v-col cols="12" md="4">
        <v-card>
          <v-card-text class="d-flex align-center">
            <v-avatar color="primary" size="56" class="mr-4">
              <v-icon size="32">mdi-server</v-icon>
            </v-avatar>
            <div>
              <div class="text-h4">{{ clusters.length }}</div>
              <div class="text-subtitle-1 text-medium-emphasis">Total Clusters</div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" md="4">
        <v-card>
          <v-card-text class="d-flex align-center">
            <v-avatar color="success" size="56" class="mr-4">
              <v-icon size="32">mdi-check-circle</v-icon>
            </v-avatar>
            <div>
              <div class="text-h4">{{ activeClusters.length }}</div>
              <div class="text-subtitle-1 text-medium-emphasis">Active Clusters</div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" md="4">
        <v-card>
          <v-card-text class="d-flex align-center">
            <v-avatar color="info" size="56" class="mr-4">
              <v-icon size="32">mdi-database</v-icon>
            </v-avatar>
            <div>
              <div class="text-h4">etcd</div>
              <div class="text-subtitle-1 text-medium-emphasis">Key-Value Store</div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <h2 class="text-h5 mt-8 mb-4">Quick Access</h2>

    <v-row v-if="loading">
      <v-col cols="12" class="text-center">
        <v-progress-circular indeterminate color="primary"></v-progress-circular>
      </v-col>
    </v-row>

    <v-row v-else-if="clusters.length === 0">
      <v-col cols="12">
        <v-card>
          <v-card-text class="text-center pa-8">
            <v-icon size="64" color="grey">mdi-server-off</v-icon>
            <div class="text-h6 mt-4">No clusters configured</div>
            <div class="text-medium-emphasis mb-4">Add your first Kubernetes cluster to get started</div>
            <v-btn color="primary" :to="{ name: 'Clusters' }">
              <v-icon left>mdi-plus</v-icon>
              Add Cluster
            </v-btn>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <v-row v-else>
      <v-col v-for="cluster in activeClusters" :key="cluster.id" cols="12" md="4">
        <v-card :to="{ name: 'EtcdBrowser', params: { id: cluster.id } }" hover>
          <v-card-text>
            <div class="d-flex align-center mb-2">
              <v-icon color="success" class="mr-2">mdi-server</v-icon>
              <span class="text-h6">{{ cluster.name }}</span>
            </div>
            <div class="text-medium-emphasis">{{ cluster.description || 'No description' }}</div>
          </v-card-text>
          <v-card-actions>
            <v-spacer></v-spacer>
            <v-btn variant="text" color="primary">
              Open etcd Browser
              <v-icon right>mdi-arrow-right</v-icon>
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-col>
    </v-row>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useClustersStore } from '../stores/clusters'

const clustersStore = useClustersStore()

const clusters = computed(() => clustersStore.clusters)
const activeClusters = computed(() => clustersStore.activeClusters)
const loading = computed(() => clustersStore.loading)

onMounted(() => {
  clustersStore.fetchClusters()
})
</script>
