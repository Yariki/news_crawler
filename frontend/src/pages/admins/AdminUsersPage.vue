<template>
    <v-card rounded="xl">
        <v-card-title class="d-flex align-center justify-space-between">
            Users
            <v-btn color="primary" prepend-icon="mdi-plus" size="small" @click="showCreateDialog">Add User</v-btn>
        </v-card-title>
        <v-alert v-if="store.error">{{ store.error }}</v-alert>
        <v-data-table :headers="headers" :items="store.users" :loading="store.loading" item-value="id">

            <template #item.roles="{ item }">
                <v-chip-group>
                    <v-chip v-for="role in (item.roles || [])" :key="role" color="primary" text-color="white" x-small>
                        {{ role }}
                    </v-chip>
                </v-chip-group>
            </template>

            <template #item.is_active="{ item }">
                <v-chip :color="item.is_active ? 'green' : 'red'" text-color="white" x-small>
                    {{ item.is_active ? 'Active' : 'Inactive' }}
                </v-chip>
            </template>

            <template #item.last_login_at="{ item }">
                <span v-if="item.last_login_at">{{ new Date(item.last_login_at).toLocaleString() }}</span>
                <span v-else>Never</span>
            </template>

            <template #item.actions="{ item }">
                <v-btn v-if="!isSelf(item.id)" color="primary" @click="setActivateUser(item.id)">
                    {{ item.is_active ? 'Deactivate' : 'Activate' }}
                </v-btn>
                <v-btn icon="mdi-account-key" color="primary" text @click="showRolesDialog(item)"></v-btn>
                <v-btn icon="mdi-pencil" color="primary" text @click="showEditDialog(item.id)"></v-btn>
                <v-btn v-if="!isSelf(item.id)" icon="mdi-delete" color="red" text @click="deleteUser(item)"></v-btn>

            </template>

        </v-data-table>
    </v-card>

    <EditUserDialog v-model="createUserDialogOpen" @create-user="createUser"></EditUserDialog>

    <UpdateUserDialog v-if="updateUserData" v-model="updateUserDialogOpen" :data="updateUserData"
        @update-user="updateUser">
    </UpdateUserDialog>

    <EditUserRolesDialog v-model="editUserRolesDialogOpen" :user="selectedUser"
        @roles-changed="onUserRolesChanged">
    </EditUserRolesDialog>

</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useAdminStore } from '../../stores/admin';
import { useAuthStore } from "../../stores/auth";
import EditUserDialog from "../../components/EditUserDialog.vue";
import type { CreateUserDialogData, RoleRead, UpdateUserDialogData, UserRead } from "../../models/types"
import UpdateUserDialog from "../../components/UpdateUserDialog.vue";
import EditUserRolesDialog from "../../components/EditUserRolesDialog.vue";
import { useConfirmDialog } from '../../composables/useConfirmDialog';

const store = useAdminStore();
const authStore = useAuthStore();
const { confirm } = useConfirmDialog();

const createUserDialogOpen = ref(false);
const updateUserDialogOpen = ref(false);
const editUserRolesDialogOpen = ref(false);

const updateUserData = ref<UpdateUserDialogData | null>(null);
const selectedUser = ref<UserRead | null>(null);

const headers = [
    { title: 'Username', key: 'username' },
    { title: 'Email', key: 'email' },
    { title: 'Status', key: 'is_active' },
    { title: 'Roles', key: 'roles' },
    { title: 'Last login', key: 'last_login_at' },
    { title: '', key: 'actions', sortable: false }
]

function isSelf(userId: string) {
    return authStore.currentUserId === userId;
}

function showEditDialog(userId: string) {
    const user = store.users.find(u => u.id === userId);
    if (user) {
        const userData: UpdateUserDialogData = {
            id: userId,
            email: user.email,
            username: user.username,
            is_active: user.is_active
        };
        updateUserData.value = userData;
        updateUserDialogOpen.value = true;
    }
}

async function updateUser(data: UpdateUserDialogData) {
    await store.updateUser(data.id, data.email, data.username, data.is_active);
}

function showCreateDialog() {
    createUserDialogOpen.value = true;
}

function showRolesDialog(user: UserRead) {
    selectedUser.value = user;
    editUserRolesDialogOpen.value = true;
}

function onUserRolesChanged(roles: RoleRead[]) {
    if (!selectedUser.value) {
        return;
    }

    const roleNames = roles.map(role => role.name);
    selectedUser.value.roles = roleNames;
    store.users = store.users.map(user => user.id === selectedUser.value?.id
        ? { ...user, roles: roleNames }
        : user);
}

async function createUser(userData: CreateUserDialogData) {
    await store.createUser(userData.email, userData.username, userData.is_active, userData.password);
}

async function deleteUser(user: UserRead) {

    const isConfirm = await confirm({
        message: `Do you want to delete user ${user.email}`,
        color: 'error',
        confirmText: 'Delete'
    });

    if (!isConfirm) {
        return;
    }

    await store.deleteUser(user.id);
}

async function setActivateUser(userId: string) {
    const user = store.users.find(u => u.id === userId);
    if (user) {
        if (user.is_active) {
            await store.deactivate(userId);
        } else {
            await store.activate(userId);
        }
        user.is_active = !user.is_active;
    }
}

async function fecthData() {
    await store.getUsers();
}

onMounted(async () => {
    await fecthData();
});
</script>
