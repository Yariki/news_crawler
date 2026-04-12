<template>
  <v-container fluid class="pa-6">
    <div class="text-h4 mb-4">Jobs</div>
    <v-card rounded="xl">
      <v-card-title>Scheduled and recent crawler jobs</v-card-title>
      <v-data-table :headers="jobHeaders" :items="store.jobsWithSource" density="comfortable">
        <template #item.status="{ item }">
          <v-chip :color="statusColor(item.status)" size="small">{{ item.status }}</v-chip>
        </template>
        <template #item.actions="{ item }">
          <v-btn size="small" color="primary" variant="flat" @click="store.runSource(item.source_id)">Run source</v-btn>
        </template>
      </v-data-table>
    </v-card>
  </v-container>
</template>

<script setup lang="ts">
import { useAppStore } from '../stores/app'

const store = useAppStore()

const jobHeaders = [
  { title: 'Job', key: 'id' },
  { title: 'Source', key: 'source_name' },
  { title: 'Status', key: 'status' },
  { title: 'Started', key: 'started_at' },
  { title: 'Finished', key: 'finished_at' },
  { title: 'Found', key: 'articles_found' },
  { title: 'Created', key: 'articles_created' },
  { title: 'Actions', key: 'actions', sortable: false },
]

const statusColor = (status: string) => ({ completed: 'success', failed: 'error', running: 'info' }[status] || 'default')
</script>
