<template>
    <div>
        <v-card-title class="d-flex align-center justify-space-between">
            Roles
            <v-btn color="primary" prepend-icon="mdi-plus" size="small" @click="addRole()">Add Role</v-btn>
        </v-card-title>
        <v-data-table :headers="headers" :items="store.roles" :loading="store.loading" item-value="id">
            <template #item.name="{ item }">
                {{ item.name }}
                <v-chip v-if="item.is_system" size="small" color="grey" class="ml-2"
                    :prepend-icon="item.is_system ? 'mdi-checkbox-marked-outline' : 'mdi-checkbox-blank-outline'"
                />
            </template>
            <template #item.permissions="{ item }">
                <v-chip v-for="p in item.permissions" :key="p.id" size="x-small" class="ma-1">{{ p.name }}</v-chip>
            </template>
            <template #item.actions="{ item }">
                <v-btn icon="mdi-pencil" size="small" color="primary" variant="text" @click="editRole(item)" />
                <v-btn icon="mdi-account-badge" size="small" color="primary" variant="text" @click="editPermissions(item)" />
                <v-btn icon="mdi-delete" size="small" variant="text" color="error" :disabled="item.is_system"
                    @click="deleteRole(item)" />
            </template>
        </v-data-table>
    </div>

    <EditRoleDialog v-model="isRoleEditDialogOpen" :form-data="roleData" :is-edit-mode="isEditMode"
        @update:modelValue="isRoleEditDialogOpen = $event" @create-role="onSaveRole" />

    <EditPermissionsDialog v-model="isPermissionsEditDialogOpen" :role="selectedRole"
        @update:modelValue="isPermissionsEditDialogOpen = $event"
        @permissions-changed="onPermissionsChanged" />

</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useAdminStore } from '../../stores/admin'
import { useConfirmDialog } from '../../composables/useConfirmDialog'
import { RoleCreateUpdate, RoleRead, PermissionRead } from '../../models/types'
import EditRoleDialog from '../../components/EditRoleDialog.vue'
import EditPermissionsDialog from '../../components/EditPermissionsDialog.vue'

const store = useAdminStore();
const { confirm } = useConfirmDialog();
const isRoleEditDialogOpen = ref(false);
const isEditMode = ref(false);
const isPermissionsEditDialogOpen = ref(false);
const selectedRole = ref<RoleRead | null>(null);
const roleData = ref<RoleCreateUpdate>({
    name: '',
    description: '',
    is_system: false,
});

const headers = [
    { title: 'Name', key: 'name', width: '100px' },
    { title: 'Description', key: 'description', width: '200px' },
    { title: 'Permissions', key: 'permissions', width: '300px' },
    { title: '', key: 'actions', sortable: false, width: '150px' },
]

function editRole(role: RoleRead, editMode: boolean = true) {
    isEditMode.value = editMode;
    selectedRole.value = role
    roleData.value = {
        name: role.name,
        description: role.description,
        is_system: role.is_system,
    }
    isRoleEditDialogOpen.value = true
}

function addRole() {
    editRole({ id: null, name: '', description: '', is_system: false, created_at: '', updated_at: null, permissions: [] }, false);
}

function editPermissions(role: RoleRead) {
    selectedRole.value = role;
    isPermissionsEditDialogOpen.value = true;
}

function deleteRole(role: RoleRead) {
    confirm({
        message: `Are you sure you want to delete the role "${role.name}"? This action cannot be undone.`,
        confirmText: 'Delete',
        cancelText: 'Cancel',
        color: 'error',
    })
        .then(async (confirmed) => {
            if (confirmed) {
                await store.deleteRole(role.id as string)
            }
        })
}

async function onSaveRole(roleData: RoleCreateUpdate) {
    if (isEditMode.value && selectedRole.value?.id) {
        await store.updateRole(selectedRole.value.id, roleData.name, roleData.description, roleData.is_system);
    } else {
        await store.createRole(roleData.name, roleData.description, roleData.is_system);
    }
    isRoleEditDialogOpen.value = false;
}

async function onPermissionsChanged(permissions: PermissionRead[]) {
    if(!selectedRole.value) {
        return;
    }
    selectedRole.value.permissions = permissions;
}

onMounted(async () => {
    await store.getRoles();
})
</script>