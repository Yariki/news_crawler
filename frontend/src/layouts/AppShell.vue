<template>
    <v-layout class="rounded rounded-md border h-screen">
        <v-app-bar flat color="surface">
            <v-app-bar-title>News Monitor</v-app-bar-title>
            <template #append>
                <v-btn icon="mdi-refresh" variant="text" @click="store.refreshAll" :loading="store.loading"/>
            </template>
        </v-app-bar>

        <v-navigation-drawer location="right" rail="false" permanent width="280">
            <v-list nav density="comfortable">
                <v-list-subheader>Navigation</v-list-subheader>
                <v-list-item
                    v-for="item in navItems"
                    :key="item.to"
                    :to="item.to"
                    rounded="lg"
                    :prepend-icon="item.icon"
                    :title="item.title"
                />
            </v-list>

            <template #append>
                <div class="pa-4">
                    <v-card rounded="xl" variant="tonal">
                        <v-card-title class="text-subtitle-1">Live alerts</v-card-title>
                        <v-list lines="two" density="compact">
                            <v-list-item v-for="(alert, index) in store.alerts.slice(0, 5)" :key="index"
                                         :href="alert.url" target="_blank">
                                <v-list-item-title>{{ alert.title }}</v-list-item-title>
                                <v-list-item-subtitle>{{
                                        (alert.matched_keywords || []).join(', ')
                                    }}
                                </v-list-item-subtitle>
                            </v-list-item>
                            <v-list-item v-if="!store.alerts.length">
                                <v-list-item-title>No alerts yet</v-list-item-title>
                            </v-list-item>
                        </v-list>
                    </v-card>
                </div>
            </template>
        </v-navigation-drawer>

        <v-main class="bg-background">
            <router-view/>
        </v-main>
    </v-layout>
</template>

<script setup lang="ts">
import {onMounted} from 'vue'
import {useAppStore} from '../stores/app'

const store = useAppStore()

const navItems = [
    {title: 'Dashboard', to: '/', icon: 'mdi-view-dashboard-outline'},
    {title: 'Keywords', to: '/keywords', icon: 'mdi-tag-multiple-outline'},
    {title: 'Jobs', to: '/jobs', icon: 'mdi-clock-outline'},
    {title: 'Sources', to: '/sources', icon: 'mdi-web-plus'},
    {title: 'Search', to: '/search', icon: 'mdi-magnify'},
]

onMounted(async () => {
    if (!store.initialized) {
        await store.refreshAll()
        store.connectAlerts()
    }
})
</script>
