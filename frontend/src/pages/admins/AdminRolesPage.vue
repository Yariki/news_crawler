<template>
    <v-card rounded="xl">
        <v-card-title class="d-flex align-center justify-space-between">
            Roles
            <v-btn color="primary" prepend-icon="mdi-plus" size="small">Add Role</v-btn>
        </v-card-title>
        <v-table>
            <thead>
                <tr>
                    <th>Name</th>
                    <th>Description</th>
                    <th>Permissions</th>
                    <th></th>
                </tr>
            </thead>
            <tbody>
                <tr v-for="role in store.roles" :key="role.id">
                    <td>{{ role.name }}</td>
                    <td>{{ role.description }}</td>
                    <td>{{ role.permissions?.map(r => r.name).join(', ') }}</td>
                    <td>
                        <v-btn icon="mdi-pencil" size="small" variant="text" />
                        <v-btn icon="mdi-delete" size="small" variant="text" color="error" />
                    </td>
                </tr>
                <tr v-if="!store.roles.length">
                    <td colspan="5" class="text-center text-medium-emphasis">No roles found</td>
                </tr>
            </tbody>
        </v-table>
    </v-card>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import {useAdminStore} from '../../stores/admin'

const store = useAdminStore();

onMounted(async () => {
    await store.getRoles();
})
</script>