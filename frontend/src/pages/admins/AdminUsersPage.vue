<template>
    <v-card rounded="xl">
        <v-card-title class="d-flex align-center justify-space-between">
            Users
            <v-btn color="primary" prepend-icon="mdi-plus" size="small">Add User</v-btn>
        </v-card-title>
        <v-table>
            <thead>
                <tr>
                    <th>Username</th>
                    <th>Email</th>
                    <th>Active</th>
                    <th>Created</th>
                    <th></th>
                </tr>
            </thead>
            <tbody>
                <tr v-for="user in store.users" :key="user.id">
                    <td>{{ user.username}}</td>
                    <td>{{ user.email }}</td>
                    <td>
                        <v-icon :color="user.is_active ? 'success' : 'error'">
                            {{ user.is_active ? 'mdi-check-circle' : 'mdi-close-circle' }}
                        </v-icon>
                    </td>
                    <td>{{ new Date(user.created_at).toLocaleDateString() }}</td>
                    <td>
                        <v-btn icon="mdi-pencil" size="small" variant="text" />
                        <v-btn icon="mdi-delete" size="small" variant="text" color="error" />
                    </td>
                </tr>
                <tr v-if="!users.length">
                    <td colspan="6" class="text-center text-medium-emphasis">No users found</td>
                </tr>
            </tbody>
        </v-table>
    </v-card>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useAdminStore } from '../../stores/admin';

const store = useAdminStore();

onMounted(async () => {
    await store.getUsers();
})
</script>