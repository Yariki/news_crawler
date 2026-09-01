<template>
    <v-layout class="h-screen">
        <v-app-bar flat color="surface">
            <v-btn icon="mdi-home" to="/" variant="text" />
            <v-toolbar-title>Admin Panel</v-toolbar-title>
            <template #append>
                <div v-if="authStore.isAuthenticated">
                    <span>{{ authStore.user?.username }} ({{ authStore.user?.email }})</span>

                    <v-btn
                        
                        icon="mdi-logout"
                        variant="text"
                        :loading="loggingOut"
                        @click="handleLogout"
                    />
                </div>
            </template>
        </v-app-bar>

        <v-navigation-drawer width="260">
            <v-list nav dense>
                <v-list-item 
                    v-for="item in items" 
                    :key="item.route" 
                    :to="item.route"
                    :title="item.title" 
                    :prepend-icon="item.icon" link>
                </v-list-item>
            </v-list>
        </v-navigation-drawer>

        <v-main class="bg-background m-5">
            <router-view />
        </v-main>

    </v-layout>

</template>

<script setup lang="ts">

import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const authStore = useAuthStore()
const loggingOut = ref(false)

const items = [
    { title: 'Overview', icon: 'mdi-view-dashboard', route: '/admin' },
    { title: 'Users', icon: 'mdi-account-group', route: '/admin/users' },
    { title: 'Roles', icon: 'mdi-shield-account', route: '/admin/roles' }    
];

async function handleLogout() {
    if (loggingOut.value) return

    loggingOut.value = true
    try {
        await authStore.logout()
    } catch {
        authStore.clearSession()
    } finally {
        loggingOut.value = false
        await router.replace({ name: 'login' })
    }
}

</script>

<style lang="css" scoped>
</style>
