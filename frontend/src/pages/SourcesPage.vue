<template>
    <v-container fluid class="pa-6">
        <div class="text-h4 mb-4">Sources</div>
        <v-row>
            <v-col cols="12" lg="5">
                <v-card rounded="xl">
                    <v-card-title>Add source and bind crawler</v-card-title>
                    <v-card-text>
                        <v-form @submit.prevent="store.createSource">
                            <v-text-field v-model="store.sourceForm.name" label="Display name" class="mb-2"/>
                            <v-text-field v-model="store.sourceForm.base_url" label="Base URL" class="mb-2"/>
                            <v-text-field v-model="store.sourceForm.language" label="Language" class="mb-2"/>
                            <v-select v-model="store.sourceForm.source_type" :items="SourceTypes" item-value="value"
                                      item-title="label" label="Source type" class="mb-2"/>
                            <v-select
                                v-model="store.sourceForm.crawler_key"
                                :items="store.crawlerTypes"
                                item-title="title"
                                item-value="key"
                                label="Crawler"
                                class="mb-2"
                            />
                            <v-text-field v-model.number="store.sourceForm.scrape_interval_minutes" type="number"
                                          label="Schedule interval, minutes" class="mb-2"/>
                            <v-switch v-model="store.sourceForm.is_enabled" color="primary" label="Enabled" inset/>
                            <v-btn color="primary" type="submit">Save source</v-btn>
                        </v-form>
                    </v-card-text>
                </v-card>
            </v-col>
            <v-col cols="12" lg="7">
                <v-card rounded="xl">
                    <v-card-title>Registered sources</v-card-title>
                    <v-data-table :headers="sourceHeaders" :items="store.sources" density="comfortable">
                        <template #item.is_enabled="{ item }">
                            <v-chip :color="item.is_enabled ? 'success' : 'default'" size="small">
                                {{ item.is_enabled ? 'Enabled' : 'Disabled' }}
                            </v-chip>
                        </template>
                        <template #item.actions="{ item }">
                            <v-btn size="small" color="primary" @click="store.runSource(item.id)">Run now</v-btn>
                        </template>
                    </v-data-table>
                </v-card>
            </v-col>
        </v-row>
    </v-container>
</template>

<script setup lang="ts">
import {useAppStore} from '../stores/app'
import {SourceTypes} from '../models/types';

const store = useAppStore()

const sourceHeaders = [
    {title: 'Name', key: 'name'},
    {title: 'URL', key: 'base_url'},
    {title: 'Crawler', key: 'crawler_key'},
    {title: 'Interval', key: 'scrape_interval_minutes'},
    {title: 'Enabled', key: 'is_enabled'},
    {title: 'Actions', key: 'actions', sortable: false},
]
</script>
