<template>
    <div>
        <v-row>
            <v-col cols="12" sm="6" lg="3">
                <v-card rounded="xl">
                    <v-card-text>
                        <div class="text-caption text-medium-emphasis">Total Users</div>
                        <div class="text-h4 mt-2">{{ store.stats?.total_users ?? 0 }}</div>
                    </v-card-text>
                </v-card>
            </v-col>
            <v-col cols="12" sm="6" lg="3">
                <v-card rounded="xl">
                    <v-card-text>
                        <div class="text-caption text-medium-emphasis">Active Users</div>
                        <div class="text-h4 mt-2">{{ store.stats?.active_users ?? 0 }}</div>
                    </v-card-text>
                </v-card>
            </v-col>
            <v-col cols="12" sm="6" lg="3">
                <v-card rounded="xl">
                    <v-card-text>
                        <div class="text-caption text-medium-emphasis">New Registrations (7d)</div>
                        <div class="text-h4 mt-2">{{ store.stats?.recent_registrations_7d ?? 0 }}</div>
                    </v-card-text>
                </v-card>
            </v-col>
        </v-row>

        <v-row class="mt-2">
            <v-col cols="12" md="6">
                <v-card rounded="xl">
                    <v-card-title>Role Distribution</v-card-title>
                    <v-table>
                        <thead>
                            <tr><th>Role</th><th>Count</th></tr>
                        </thead>
                        <tbody>
                            <tr v-for="r in store.stats?.role_distribution" :key="r.role">
                                <td>{{ r.role }}</td>
                                <td>{{ r.count }}</td>
                            </tr>
                        </tbody>
                    </v-table>
                </v-card>
            </v-col>
        </v-row>
    </div>
</template>

<script setup lan="ts">
import { onMounted } from 'vue'
import { useAdminStore } from '../../stores/admin';


const store = useAdminStore();

onMounted(async () => {
    await store.getStats();
});


</script>

<style lang="css" scoped>
</style>