<template>
    <v-dialog v-model="isOpen" persistent max-width="560px" scrollable>
        <v-card rounded="xl">
            <v-card-title class="d-flex align-center justify-space-between">
                <span>Roles — {{ user?.username }}</span>
                <v-btn icon="mdi-close" variant="text" size="small" :disabled="loading || saving" @click="onClose" />
            </v-card-title>

            <v-divider />

            <v-card-text>
                <v-alert v-if="errorMessage" type="error" variant="tonal" density="compact" class="mb-3" closable
                    @click:close="errorMessage = null">
                    {{ errorMessage }}
                </v-alert>

                <v-skeleton-loader v-if="loading" type="list-item-three-line, list-item-three-line" />

                <v-list v-else density="comfortable">
                    <v-list-item v-if="availableRoles.length === 0">
                        <v-list-item-title class="text-medium-emphasis">No roles available.</v-list-item-title>
                    </v-list-item>

                    <v-list-item v-for="role in availableRoles" :key="role.id ?? role.name"
                        :title="role.name" :subtitle="role.description">
                        <template #prepend>
                            <v-checkbox-btn :model-value="isSelected(role.id)"
                                :disabled="!role.id || isRoleSaving(role.id)" :loading="isRoleSaving(role.id)"
                                @update:model-value="checked => onRoleToggle(role, checked)" />
                        </template>

                        <template #append>
                            <v-chip v-if="role.is_system" size="small" color="grey" variant="tonal">System</v-chip>
                        </template>
                    </v-list-item>
                </v-list>
            </v-card-text>

            <v-divider />

            <v-card-actions>
                <span class="text-caption text-medium-emphasis ml-2">
                    {{ selectedRoleIds.length }} selected
                </span>
                <v-spacer />
                <v-btn variant="text" :disabled="loading || saving" @click="onClose">Close</v-btn>
            </v-card-actions>
        </v-card>
    </v-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useAdminStore } from '../stores/admin'
import type { RoleRead, UserRead } from '../models/types'

const props = defineProps<{
    modelValue: boolean
    user: UserRead | null
}>()

const emit = defineEmits<{
    (e: 'update:modelValue', value: boolean): void
    (e: 'roles-changed', roles: RoleRead[]): void
}>()

const store = useAdminStore()

const loading = ref(false)
const savingRoleIds = ref<string[]>([])
const errorMessage = ref<string | null>(null)
const selectedRoleIds = ref<string[]>([])

const isOpen = computed({
    get: () => props.modelValue,
    set: (value: boolean) => emit('update:modelValue', value),
})

const saving = computed(() => savingRoleIds.value.length > 0)
const availableRoles = computed(() => store.roles.filter(role => Boolean(role.id)))

function isSelected(roleId: string | null): boolean {
    return Boolean(roleId && selectedRoleIds.value.includes(roleId))
}

function isRoleSaving(roleId: string | null): boolean {
    return Boolean(roleId && savingRoleIds.value.includes(roleId))
}

function setRoleSaving(roleId: string, value: boolean) {
    savingRoleIds.value = value
        ? [...savingRoleIds.value, roleId]
        : savingRoleIds.value.filter(id => id !== roleId)
}

function emitChanged() {
    const selectedRoles = availableRoles.value.filter(role => role.id && selectedRoleIds.value.includes(role.id))
    emit('roles-changed', selectedRoles)
}

async function onRoleToggle(role: RoleRead, checked: boolean | null) {
    if (!props.user || !role.id) return

    errorMessage.value = null
    setRoleSaving(role.id, true)
    try {
        const nextRoleIds = checked
            ? Array.from(new Set([...selectedRoleIds.value, role.id]))
            : selectedRoleIds.value.filter(id => id !== role.id)
        const ok = checked
            ? await store.assignRolesToUser(props.user.id, nextRoleIds)
            : await store.removeRoleFromUser(props.user.id, role.id)

        if (!ok) {
            errorMessage.value = store.error ?? `Failed to ${checked ? 'assign' : 'remove'} role "${role.name}".`
            return
        }

        selectedRoleIds.value = nextRoleIds
        emitChanged()
    } finally {
        setRoleSaving(role.id, false)
    }
}

async function loadRoles(user: UserRead) {
    loading.value = true
    errorMessage.value = null
    selectedRoleIds.value = []
    try {
        if (store.roles.length === 0) {
            await store.getRoles()
        }

        const roles = await store.getUserRoles(user.id)
        if (!roles) {
            errorMessage.value = store.error ?? 'Failed to load user roles.'
            return
        }
        selectedRoleIds.value = roles.map(role => role.id).filter(Boolean) as string[]
    } finally {
        loading.value = false
    }
}

function onClose() {
    isOpen.value = false
}

watch(
    () => [props.modelValue, props.user?.id] as const,
    ([open]) => {
        if (open && props.user) {
            loadRoles(props.user)
        } else if (!open) {
            selectedRoleIds.value = []
            savingRoleIds.value = []
            errorMessage.value = null
        }
    },
    { immediate: true },
)


</script>

<style lang="css" scoped>
</style>
