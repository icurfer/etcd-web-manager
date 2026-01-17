<template>
  <div>
    <div class="d-flex justify-space-between align-center mb-6">
      <h1 class="text-h4">Clusters</h1>
      <v-btn color="primary" @click="openCreateDialog">
        <v-icon left>mdi-plus</v-icon>
        Add Cluster
      </v-btn>
    </div>

    <v-card>
      <v-data-table
        :headers="headers"
        :items="clusters"
        :loading="loading"
        class="elevation-0"
      >
        <template v-slot:item.is_active="{ item }">
          <v-chip :color="item.is_active ? 'success' : 'grey'" size="small">
            {{ item.is_active ? 'Active' : 'Inactive' }}
          </v-chip>
        </template>

        <template v-slot:item.created_at="{ item }">
          {{ formatDate(item.created_at) }}
        </template>

        <template v-slot:item.actions="{ item }">
          <v-btn icon size="small" @click="testConnection(item)" :loading="testing === item.id">
            <v-icon>mdi-connection</v-icon>
            <v-tooltip activator="parent">Test Connection</v-tooltip>
          </v-btn>
          <v-btn icon size="small" :to="{ name: 'EtcdBrowser', params: { id: item.id } }">
            <v-icon>mdi-database</v-icon>
            <v-tooltip activator="parent">Browse etcd</v-tooltip>
          </v-btn>
          <v-btn icon size="small" @click="openEditDialog(item)">
            <v-icon>mdi-pencil</v-icon>
            <v-tooltip activator="parent">Edit</v-tooltip>
          </v-btn>
          <v-btn icon size="small" color="error" @click="confirmDelete(item)">
            <v-icon>mdi-delete</v-icon>
            <v-tooltip activator="parent">Delete</v-tooltip>
          </v-btn>
        </template>
      </v-data-table>
    </v-card>

    <!-- Create/Edit Dialog -->
    <v-dialog v-model="dialog" max-width="600">
      <v-card>
        <v-card-title>
          {{ editingCluster ? 'Edit Cluster' : 'Add Cluster' }}
        </v-card-title>
        <v-card-text>
          <v-form ref="form">
            <v-text-field
              v-model="formData.name"
              label="Cluster Name"
              :rules="[v => !!v || 'Name is required']"
              variant="outlined"
              class="mb-3"
            ></v-text-field>

            <v-textarea
              v-model="formData.description"
              label="Description"
              variant="outlined"
              rows="2"
              class="mb-3"
            ></v-textarea>

            <v-textarea
              v-model="formData.kubeconfig"
              label="Kubeconfig"
              :rules="[v => !!v || 'Kubeconfig is required']"
              variant="outlined"
              rows="10"
              placeholder="Paste your kubeconfig content here..."
              class="mb-3"
            ></v-textarea>

            <v-switch
              v-model="formData.is_active"
              label="Active"
              color="primary"
            ></v-switch>
          </v-form>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn @click="dialog = false">Cancel</v-btn>
          <v-btn color="primary" @click="saveCluster" :loading="saving">
            {{ editingCluster ? 'Update' : 'Create' }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Delete Confirmation -->
    <v-dialog v-model="deleteDialog" max-width="400">
      <v-card>
        <v-card-title>Delete Cluster</v-card-title>
        <v-card-text>
          Are you sure you want to delete "{{ deletingCluster?.name }}"?
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn @click="deleteDialog = false">Cancel</v-btn>
          <v-btn color="error" @click="deleteCluster" :loading="deleting">Delete</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, inject } from 'vue'
import { useClustersStore } from '../stores/clusters'
import { clustersApi } from '../api/clusters'

const clustersStore = useClustersStore()
const showSnackbar = inject('showSnackbar')

const clusters = computed(() => clustersStore.clusters)
const loading = computed(() => clustersStore.loading)

const dialog = ref(false)
const deleteDialog = ref(false)
const form = ref(null)
const editingCluster = ref(null)
const deletingCluster = ref(null)
const saving = ref(false)
const deleting = ref(false)
const testing = ref(null)

const formData = ref({
  name: '',
  description: '',
  kubeconfig: '',
  is_active: true
})

const headers = [
  { title: 'Name', key: 'name' },
  { title: 'Description', key: 'description' },
  { title: 'Status', key: 'is_active' },
  { title: 'Created', key: 'created_at' },
  { title: 'Actions', key: 'actions', sortable: false, width: '180px' }
]

const formatDate = (dateStr) => {
  return new Date(dateStr).toLocaleDateString()
}

const openCreateDialog = () => {
  editingCluster.value = null
  formData.value = { name: '', description: '', kubeconfig: '', is_active: true }
  dialog.value = true
}

const openEditDialog = (cluster) => {
  editingCluster.value = cluster
  formData.value = {
    name: cluster.name,
    description: cluster.description || '',
    kubeconfig: '',
    is_active: cluster.is_active
  }
  dialog.value = true
}

const saveCluster = async () => {
  const { valid } = await form.value.validate()
  if (!valid) return

  saving.value = true
  try {
    if (editingCluster.value) {
      await clustersStore.updateCluster(editingCluster.value.id, formData.value)
      showSnackbar('Cluster updated successfully')
    } else {
      await clustersStore.createCluster(formData.value)
      showSnackbar('Cluster created successfully')
    }
    dialog.value = false
  } catch (error) {
    showSnackbar(error.response?.data?.detail || 'Failed to save cluster', 'error')
  } finally {
    saving.value = false
  }
}

const confirmDelete = (cluster) => {
  deletingCluster.value = cluster
  deleteDialog.value = true
}

const deleteCluster = async () => {
  deleting.value = true
  try {
    await clustersStore.deleteCluster(deletingCluster.value.id)
    showSnackbar('Cluster deleted successfully')
    deleteDialog.value = false
  } catch (error) {
    showSnackbar('Failed to delete cluster', 'error')
  } finally {
    deleting.value = false
  }
}

const testConnection = async (cluster) => {
  testing.value = cluster.id
  try {
    const response = await clustersApi.testConnection(cluster.id)
    showSnackbar(response.data.message, response.data.success ? 'success' : 'error')
  } catch (error) {
    showSnackbar(error.response?.data?.message || 'Connection failed', 'error')
  } finally {
    testing.value = null
  }
}

onMounted(() => {
  clustersStore.fetchClusters()
})
</script>
