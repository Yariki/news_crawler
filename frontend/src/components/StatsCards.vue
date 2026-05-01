<template>
    <v-row>
        <v-col v-for="item in cards" :key="item.title" cols="12" sm="6" lg="3">
            <v-card rounded="xl">
                <v-card-text>
                    <div class="text-caption text-medium-emphasis">{{ item.title }}</div>
                    <div class="text-h4 mt-2">{{ item.value }}</div>
                    <div v-if="item.hint" class="text-body-2 text-medium-emphasis mt-1">{{ item.hint }}</div>
                </v-card-text>
            </v-card>
        </v-col>
    </v-row>
</template>

<script setup lang="ts">
import {computed} from 'vue'

const props = defineProps<{ stats: any }>()

const cards = computed(() => [
    {title: 'Articles in DB', value: props.stats?.articles_total ?? 0},
    {title: 'Documents in Elasticsearch', value: props.stats?.elasticsearch_document_count ?? 0},
    {
        title: 'Enabled sources',
        value: props.stats?.sources_enabled ?? 0,
        hint: `of ${props.stats?.sources_total ?? 0} total`
    },
    {
        title: 'Alerts',
        value: props.stats?.alerts_total ?? 0,
        hint: `${props.stats?.keywords_total ?? 0} active keywords`
    },
])
</script>
