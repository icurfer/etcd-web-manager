<template>
  <div>
    <div class="d-flex justify-space-between align-center mb-4">
      <div class="d-flex align-center">
        <v-btn icon variant="text" :to="{ name: 'Clusters' }">
          <v-icon>mdi-arrow-left</v-icon>
        </v-btn>
        <h1 class="text-h4 ml-2">{{ cluster?.name || 'Loading...' }}</h1>
      </div>
      <div class="d-flex gap-2">
        <v-btn variant="outlined" @click="refreshTree" :loading="loadingTree">
          <v-icon left>mdi-refresh</v-icon>
          Refresh
        </v-btn>
        <v-btn color="primary" @click="openCreateDialog">
          <v-icon left>mdi-plus</v-icon>
          New Key
        </v-btn>
      </div>
    </div>

    <!-- Health Status -->
    <v-card class="mb-4" v-if="health">
      <v-card-text class="d-flex align-center">
        <v-chip :color="health.success ? 'success' : 'error'" class="mr-4">
          <v-icon left>{{ health.success ? 'mdi-check-circle' : 'mdi-alert-circle' }}</v-icon>
          {{ health.success ? 'Healthy' : 'Unhealthy' }}
        </v-chip>
        <span class="text-medium-emphasis" v-if="health.members">
          Members: {{ health.members?.members?.length || 0 }}
        </span>
      </v-card-text>
    </v-card>

    <v-row>
      <!-- Tree View -->
      <v-col cols="12" md="4">
        <v-card>
          <v-card-title class="d-flex align-center">
            <v-icon class="mr-2">mdi-file-tree</v-icon>
            Keys
          </v-card-title>
          <v-divider></v-divider>
          <v-card-text style="max-height: 600px; overflow-y: auto;">
            <v-text-field
              v-model="search"
              placeholder="Search keys..."
              prepend-inner-icon="mdi-magnify"
              variant="outlined"
              density="compact"
              hide-details
              class="mb-3"
            ></v-text-field>

            <v-progress-linear v-if="loadingTree" indeterminate></v-progress-linear>

            <v-treeview
              v-else
              :items="filteredTree"
              item-title="name"
              item-value="key"
              activatable
              open-on-click
              :active="selectedKey ? [selectedKey] : []"
              @update:activated="onKeySelect"
              density="compact"
            >
              <template v-slot:prepend="{ item, isOpen }">
                <v-icon v-if="item.children?.length">
                  {{ isOpen ? 'mdi-folder-open' : 'mdi-folder' }}
                </v-icon>
                <v-icon v-else>mdi-key</v-icon>
              </template>
            </v-treeview>

            <div v-if="!loadingTree && tree.length === 0" class="text-center text-medium-emphasis pa-4">
              No keys found
            </div>
          </v-card-text>
        </v-card>
      </v-col>

      <!-- Value Editor -->
      <v-col cols="12" md="8">
        <v-card>
          <v-card-title class="d-flex align-center">
            <v-icon class="mr-2">mdi-code-json</v-icon>
            Value
            <v-spacer></v-spacer>
            <v-btn
              v-if="selectedKey"
              icon
              size="small"
              color="error"
              @click="confirmDelete"
            >
              <v-icon>mdi-delete</v-icon>
              <v-tooltip activator="parent">Delete Key</v-tooltip>
            </v-btn>
          </v-card-title>
          <v-divider></v-divider>
          <v-card-text>
            <div v-if="!selectedKey" class="text-center text-medium-emphasis pa-8">
              <v-icon size="64" color="grey">mdi-cursor-default-click</v-icon>
              <div class="mt-4">Select a key to view its value</div>
            </div>

            <div v-else>
              <v-text-field
                v-model="selectedKey"
                label="Key"
                variant="outlined"
                readonly
                class="mb-3"
              ></v-text-field>

              <v-textarea
                v-model="keyValue"
                label="Value"
                variant="outlined"
                rows="15"
                :loading="loadingValue"
              ></v-textarea>

              <div class="d-flex justify-end mt-3">
                <v-btn
                  color="primary"
                  @click="saveValue"
                  :loading="savingValue"
                  :disabled="!selectedKey"
                >
                  <v-icon left>mdi-content-save</v-icon>
                  Save
                </v-btn>
              </div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Create Key Dialog -->
    <v-dialog v-model="createDialog" max-width="600">
      <v-card>
        <v-card-title>Create New Key</v-card-title>
        <v-card-text>
          <v-text-field
            v-model="newKey"
            label="Key"
            variant="outlined"
            placeholder="/path/to/key"
            class="mb-3"
          ></v-text-field>
          <v-textarea
            v-model="newValue"
            label="Value"
            variant="outlined"
            rows="8"
          ></v-textarea>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn @click="createDialog = false">Cancel</v-btn>
          <v-btn color="primary" @click="createKey" :loading="creatingKey">Create</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Delete Confirmation -->
    <v-dialog v-model="deleteDialog" max-width="400">
      <v-card>
        <v-card-title>Delete Key</v-card-title>
        <v-card-text>
          Are you sure you want to delete "{{ selectedKey }}"?
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn @click="deleteDialog = false">Cancel</v-btn>
          <v-btn color="error" @click="deleteKey" :loading="deletingKey">Delete</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, inject } from 'vue'
import { useRoute } from 'vue-router'
import { useClustersStore } from '../stores/clusters'
import { etcdApi } from '../api/etcd'

const route = useRoute()
const clustersStore = useClustersStore()
const showSnackbar = inject('showSnackbar')

const clusterId = computed(() => parseInt(route.params.id))
const cluster = computed(() => clustersStore.currentCluster)

const tree = ref([])
const search = ref('')
const selectedKey = ref(null)
const keyValue = ref('')
const health = ref(null)

const loadingTree = ref(false)
const loadingValue = ref(false)
const savingValue = ref(false)

const createDialog = ref(false)
const deleteDialog = ref(false)
const newKey = ref('')
const newValue = ref('')
const creatingKey = ref(false)
const deletingKey = ref(false)

const filteredTree = computed(() => {
  if (!search.value) return tree.value
  return filterTree(tree.value, search.value.toLowerCase())
})

const filterTree = (nodes, query) => {
  return nodes
    .map(node => {
      if (node.name.toLowerCase().includes(query)) {
        return node
      }
      if (node.children) {
        const filteredChildren = filterTree(node.children, query)
        if (filteredChildren.length > 0) {
          return { ...node, children: filteredChildren }
        }
      }
      return null
    })
    .filter(Boolean)
}

const fetchTree = async () => {
  loadingTree.value = true
  try {
    const response = await etcdApi.getTree(clusterId.value)
    if (response.data.success) {
      tree.value = response.data.tree
    } else {
      showSnackbar(response.data.error || 'Failed to load keys', 'error')
    }
  } catch (error) {
    showSnackbar(error.message || 'Failed to load keys', 'error')
  } finally {
    loadingTree.value = false
  }
}

const fetchHealth = async () => {
  try {
    const response = await etcdApi.getHealth(clusterId.value)
    health.value = response.data
  } catch (error) {
    console.error('Failed to fetch health:', error)
  }
}

const refreshTree = () => {
  fetchTree()
  fetchHealth()
}

const onKeySelect = async (keys) => {
  const key = keys[0]
  if (!key || key === selectedKey.value) return

  selectedKey.value = key
  loadingValue.value = true

  try {
    const response = await etcdApi.getValue(clusterId.value, key)
    if (response.data.success) {
      keyValue.value = response.data.value || ''
    } else {
      showSnackbar(response.data.error || 'Failed to load value', 'error')
    }
  } catch (error) {
    showSnackbar(error.message || 'Failed to load value', 'error')
  } finally {
    loadingValue.value = false
  }
}

const saveValue = async () => {
  if (!selectedKey.value) return

  savingValue.value = true
  try {
    const response = await etcdApi.putValue(clusterId.value, selectedKey.value, keyValue.value)
    if (response.data.success) {
      showSnackbar('Value saved successfully')
    } else {
      showSnackbar(response.data.error || 'Failed to save value', 'error')
    }
  } catch (error) {
    showSnackbar(error.message || 'Failed to save value', 'error')
  } finally {
    savingValue.value = false
  }
}

const openCreateDialog = () => {
  newKey.value = ''
  newValue.value = ''
  createDialog.value = true
}

const createKey = async () => {
  if (!newKey.value) {
    showSnackbar('Key is required', 'error')
    return
  }

  creatingKey.value = true
  try {
    const response = await etcdApi.putValue(clusterId.value, newKey.value, newValue.value)
    if (response.data.success) {
      showSnackbar('Key created successfully')
      createDialog.value = false
      fetchTree()
    } else {
      showSnackbar(response.data.error || 'Failed to create key', 'error')
    }
  } catch (error) {
    showSnackbar(error.message || 'Failed to create key', 'error')
  } finally {
    creatingKey.value = false
  }
}

const confirmDelete = () => {
  deleteDialog.value = true
}

const deleteKey = async () => {
  if (!selectedKey.value) return

  deletingKey.value = true
  try {
    const response = await etcdApi.deleteKey(clusterId.value, selectedKey.value)
    if (response.data.success) {
      showSnackbar('Key deleted successfully')
      deleteDialog.value = false
      selectedKey.value = null
      keyValue.value = ''
      fetchTree()
    } else {
      showSnackbar(response.data.error || 'Failed to delete key', 'error')
    }
  } catch (error) {
    showSnackbar(error.message || 'Failed to delete key', 'error')
  } finally {
    deletingKey.value = false
  }
}

onMounted(async () => {
  await clustersStore.fetchCluster(clusterId.value)
  fetchTree()
  fetchHealth()
})
</script>
