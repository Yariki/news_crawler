<template>
    <v-layout class="h-screen">
        <v-app-bar app color="primary" dark>
            <v-btn icon="mdi-home" to="/" variant="text" />
            <v-toolbar-title>Admin Panel</v-toolbar-title>
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

        <v-main class="bg-background">
            <router-view />
        </v-main>

    </v-layout>

    <GlobalConfirmDialog />

</template>

<script setup lang="ts">

import GlobalConfirmDialog  from '../components/GlobalConfirmDialog.vue'

const items = [
    { title: 'Overview', icon: 'mdi-view-dashboard', route: '/admin' },
    { title: 'Users', icon: 'mdi-account-group', route: '/admin/users' },
    { title: 'Roles', icon: 'mdi-shield-account', route: '/admin/roles' }    
];

</script>

<style lang="css" scoped>
</style>