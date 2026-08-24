<template>
    <AuthLayout subtitle="The requested page could not be found.">
        <v-empty-state headline="404" title="Page not found" text="The requested page does not exist." />
    </AuthLayout>
</template>
<script setup lang="ts">
import AuthLayout from '../layouts/AuthLayout.vue'
</script>