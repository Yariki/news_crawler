<template>
    <div class="mt-5 ml-5" >
        <v-row>
            <v-col cols="12" sm="6" lg="3">
                <v-card rounded="xl">
                    <v-card-text>
                        <div class="text-caption text-medium-emphasis">Total Users</div>
                        <div class="text-h4 mt-2">{{ store.state?.total_users ?? 0 }}</div>
                    </v-card-text>
                </v-card>
            </v-col>
            <v-col cols="12" sm="6" lg="3">
                <v-card rounded="xl">
                    <v-card-text>
                        <div class="text-caption text-medium-emphasis">Active Users</div>
                        <div class="text-h4 mt-2">{{ store.state?.active_users ?? 0 }}</div>
                    </v-card-text>
                </v-card>
            </v-col>
            <v-col cols="12" sm="6" lg="3">
                <v-card rounded="xl">
                    <v-card-text>
                        <div class="text-caption text-medium-emphasis">New Registrations (7d)</div>
                        <div class="text-h4 mt-2">{{ store.state?.recent_registrations ?? 0 }}</div>
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
                            <tr v-for="r in store.state?.role_distribution" :key="r.role_name">
                                <td>{{ r.role_name }}</td>
                                <td>{{ r.user_count }}</td>
                            </tr>
                        </tbody>
                    </v-table>
                </v-card>
            </v-col>
        </v-row>
    </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useAdminStore } from '../../stores/admin';


const store = useAdminStore();

onMounted(async () => {
    await store.getStats();
});


</script>

<style lang="css" scoped>
</style>