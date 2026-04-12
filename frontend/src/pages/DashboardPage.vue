<template>
  <v-container fluid class="pa-6">
    <div class="text-h4 mb-4">Dashboard</div>
    <StatsCards :stats="store.stats" />

    <v-row class="mt-2">
      <v-col cols="12" lg="7">
        <v-card rounded="xl">
          <v-card-title>Sources overview</v-card-title>
          <v-data-table :headers="sourceHeaders" :items="store.sources" density="comfortable">
            <template #item.is_enabled="{ item }">
              <v-chip :color="item.is_enabled ? 'success' : 'default'" size="small">{{ item.is_enabled ? 'Enabled' : 'Disabled' }}</v-chip>
            </template>
          </v-data-table>
        </v-card>
      </v-col>
      <v-col cols="12" lg="5">
        <v-card rounded="xl" class="mb-4">
          <v-card-title>Scheduled jobs</v-card-title>
          <v-list lines="two">
            <v-list-item v-for="job in store.jobsWithSource.slice(0, 5)" :key="job.id">
              <v-list-item-title>#{{ job.id }} · {{ job.source_name }}</v-list-item-title>
              <v-list-item-subtitle>{{ job.status }} · created {{ job.articles_created }} article(s)</v-list-item-subtitle>
            </v-list-item>
          </v-list>
        </v-card>
        <v-card rounded="xl">
          <v-card-title>Keywords</v-card-title>
          <v-card-text class="d-flex flex-wrap ga-2">
            <v-chip v-for="keyword in store.keywords.slice(0, 15)" :key="keyword.id">{{ keyword.keyword }}</v-chip>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
import StatsCards from '../components/StatsCards.vue'
import { useAppStore } from '../stores/app'

const store = useAppStore()

const sourceHeaders = [
  { title: 'Name', key: 'name' },
  { title: 'Crawler', key: 'crawler_key' },
  { title: 'Interval (min)', key: 'scrape_interval_minutes' },
  { title: 'Enabled', key: 'is_enabled' },
]
</script>
