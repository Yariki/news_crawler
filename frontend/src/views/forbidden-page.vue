<template>
    <AuthLayout subtitle="You do not have permission to access this page.">
        <v-empty-state headline="403" title="Access denied" text="You do not have permission to view this page." />
    </AuthLayout>
</template>
<script setup lang="ts">
import AuthLayout from '../layouts/AuthLayout.vue'
</script>