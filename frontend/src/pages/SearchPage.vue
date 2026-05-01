<template>
    <v-container fluid class="pa-6">
        <div class="text-h4 mb-4">Search</div>
        <v-card rounded="xl">
            <v-card-title>Search indexed articles</v-card-title>
            <v-card-text>
                <div class="d-flex ga-3">
                    <v-text-field v-model="store.searchQuery" hide-details label="Search articles in Elasticsearch"/>
                    <v-btn color="primary" @click="store.search">Search</v-btn>
                </div>
            </v-card-text>
            <v-data-table :headers="searchHeaders" :items="store.searchHits" density="comfortable">
                <template #item.title="{ item }">
                    <a :href="item.url" target="_blank" class="text-decoration-none">{{ item.title }}</a>
                </template>
                <template #item.is_alert="{ item }">
                    <v-chip :color="item.is_alert ? 'error' : 'default'" size="small">
                        {{ item.is_alert ? 'Alert' : 'Normal' }}
                    </v-chip>
                </template>
            </v-data-table>
        </v-card>
    </v-container>
</template>

<script setup lang="ts">
import {useAppStore} from '../stores/app'

const store = useAppStore()

const searchHeaders = [
    {title: 'Title', key: 'title'},
    {title: 'Source', key: 'source_name'},
    {title: 'Published', key: 'published_at'},
    {title: 'Excerpt', key: 'excerpt'},
    {title: 'Alert', key: 'is_alert'},
]
</script>
