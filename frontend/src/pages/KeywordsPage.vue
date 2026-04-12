<template>
  <v-container fluid class="pa-6">
    <div class="text-h4 mb-4">Keywords</div>
    <v-card rounded="xl">
      <v-card-title>Global monitored keywords</v-card-title>
      <v-card-text>
        <div class="d-flex ga-3 mb-4">
          <v-text-field v-model="store.newKeyword" hide-details label="Add keyword" density="comfortable" />
          <v-btn color="primary" @click="store.addKeyword">Add</v-btn>
        </div>
        <div class="d-flex flex-wrap ga-2">
          <v-chip
            v-for="keyword in store.keywords"
            :key="keyword.id"
            closable
            @click:close="store.deleteKeyword(keyword.id)"
          >
            {{ keyword.keyword }}
          </v-chip>
        </div>
      </v-card-text>
    </v-card>
  </v-container>
</template>

<script setup lang="ts">
import { useAppStore } from '../stores/app'
const store = useAppStore()
</script>
