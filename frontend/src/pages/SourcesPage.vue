<template>
    <v-container fluid class="pa-6">
        <div class="text-h4 mb-4">Sources</div>
        <v-row>
            <v-col cols="12" lg="5">
                <v-card rounded="xl">
                    <v-card-title>Add source and bind crawler</v-card-title>
                    <v-card-text>
                        <v-form @submit.prevent="store.createSource">
                            <v-text-field v-model="store.sourceForm.name" label="Display name" :rules="nameRule" class="mb-2"/>
                            <v-text-field v-model="store.sourceForm.base_url" label="Base URL" :rules="urlRule" class="mb-2"/>
                            <v-select v-model="store.sourceForm.language" label="Language" :items="Languages" :rules="languageRule" item-value="value"
                                      item-title="label" class="mb-2"/>
                            <v-select v-model="store.sourceForm.source_type" :items="SourceTypes" :rules="sourceTypeRule" item-value="value"
                                      item-title="label" label="Source type" class="mb-2"/>
                            <!-- now we only depend on SourceType, Later we could get it back -->
                            <v-select
                                v-if="false"
                                v-model="store.sourceForm.crawler_key"
                                :items="store.crawlerTypes"
                                item-title="title"
                                item-value="key"
                                label="Crawler"
                                class="mb-2"
                            />
                            <v-text-field v-model.number="store.sourceForm.scrape_interval_minutes" type="number" :rules="scrapeIntervalRule"
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
                            <v-btn size="x-small" color="primary" icon="mdi-play" @click="runSource(item.id)" />
                        </template>
                    </v-data-table>
                </v-card>
            </v-col>
        </v-row>
    </v-container>
</template>

<script setup lang="ts">
import {useAppStore} from '../stores/app'
import { SourceTypes, Languages } from '../models/types';
import { useMessages } from '../stores/messages';
import { isValidWebUrl } from '../utils/validation';


const store = useAppStore()
const messageStore = useMessages();

const sourceHeaders = [
    {title: 'Name', key: 'name'},
    {title: 'URL', key: 'base_url'},
    {title: 'Interval', key: 'scrape_interval_minutes'},
    {title: 'Enabled', key: 'is_enabled'},
    {title: 'Actions', key: 'actions', sortable: false},
]

async function runSource(id: string) {
  const data = await store.runSource(id);
  switch (data.status) {
    case "ok":
      messageStore.addMessage(data.message);
      break;
    case "error":
      messageStore.onError(data.message);
      break;
  }
}

const nameRule = [
  value => {
    if (value?.length > 0) return true;
    return "The Name must not be empty";
  }
]

const urlRule = [
  value => {
    if (isValidWebUrl(value)) return true;
    return "Url must not be empty or has valid value";

  }
]

const languageRule = [
  value => {
    if (value?.length > 0) return true;
    return "Language must not be empty";
  }
]

const sourceTypeRule = [
  value => {
    const val = +value;
    if (val > 0 && val <= SourceTypes.length) return true;
    return "Source type must not be empty";
  }
]

const scrapeIntervalRule = [
  value => {
    const val = +value;
    if (val > 0) return true;
    return "Scrape interval must not be empty";
  }
]


</script>
