<template>
    <v-main class="auth-layout bg-background">
        <v-container class="fill-height d-flex align-center justify-center">
            <v-card rounded="xl" width="100%" max-width="480" elevation="8">
                <v-card-text class="pa-8">
                    <div class="text-center mb-8">
                        <div class="text-h4 font-weight-bold">News Monitor</div>
                        <div v-if="subtitle" class="text-medium-emphasis mt-2">{{ subtitle }}</div>
                    </div>
                    <slot />
                </v-card-text>
            </v-card>
        </v-container>
    </v-main>
</template>


<script setup lang="ts">
    defineProps<{
        subtitle?: string
    }>();
</script>

<style scoped>
.auth-layout {
    min-height: 100vh;
}
</style>