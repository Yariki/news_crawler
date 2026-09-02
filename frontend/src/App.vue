<template>
    <v-app>
        <router-view/>
        <GlobalConfirmDialog />
    </v-app>
</template>
<script setup lang="ts">
import GlobalConfirmDialog from './components/GlobalConfirmDialog.vue'
</script>
<style>
html,
body,
#app {
    height: 100%;
    margin: 0;
}
</style>
