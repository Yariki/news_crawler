<template>
    <v-dialog v-model="isOpen" persistent max-width="1000px" scrollable>
        <v-card rounded="xl">
            <v-card-title class="d-flex align-center justify-space-between">
                <span>Permissions — {{ role?.name }}</span>
                <v-btn color="primary" size="small" variant="tonal" prepend-icon="mdi-plus"
                    :disabled="store.loading || saving" @click="addRow" >
                </v-btn>
            </v-card-title>

            <v-divider />

            <v-card-text>
                <v-alert v-if="errorMessage" type="error" variant="tonal" density="compact" class="mb-3" closable
                    @click:close="errorMessage = null">
                    {{ errorMessage }}
                </v-alert>

                <v-form ref="formRef" v-model="isFormValid">
                    <v-data-table :headers="headers" :items="rows" item-value="key" :loading="store.loading"
                        density="comfortable" hide-default-footer :items-per-page="-1"
                        no-data-text="No permissions assigned to this role yet.">

                        <template #item.resource="{ item }">
                            <v-select v-if="isDraft(item)" v-model="item.resource" :items="store.resources"
                                :rules="permissionResourceRules" density="compact" variant="outlined" hide-details="auto"
                                class="my-2" placeholder="resource" />
                            <span v-else>{{ item.resource }}</span>
                        </template>

                        <template #item.action="{ item }">
                            <v-select v-if="isDraft(item)" v-model="item.action" :items="store.actions"
                                :rules="permissionActionRules" density="compact" variant="outlined" hide-details="auto"
                                class="my-2" placeholder="action" />
                            <span v-else>{{ item.action }}</span>
                        </template>

                        <template #item.scope="{ item }">
                            <v-select v-if="isDraft(item)" v-model="item.scope" :items="store.scopes"
                                :rules="permissionScopeRules" density="compact" variant="outlined" hide-details="auto"
                                class="my-2" placeholder="scope" />
                            <span v-else>{{ item.scope ?? '—' }}</span>
                        </template>

                        <template #item.description="{ item }">
                            <v-text-field v-if="isDraft(item)" v-model="item.description" :rules="descriptionRules"
                                density="compact" variant="outlined" hide-details="auto" class="my-2"
                                placeholder="optional" />
                            <span v-else class="text-medium-emphasis">{{ item.description || '—' }}</span>
                        </template>

                        <template #item.actions="{ item }">
                            <v-tooltip v-if="item.error" :text="item.error" location="top">
                                <template #activator="{ props: tip }">
                                    <v-icon v-bind="tip" color="error" icon="mdi-alert-circle-outline" class="mr-1" />
                                </template>
                            </v-tooltip>
                            <v-btn v-if="isDraft(item)" size="small" color="warning" variant="text"
                                icon="mdi-content-save" @click="() => onSave(item)" :loading="saving"
                                :disabled="saving || !isFormValid">
                                unsaved
                            </v-btn>
                            <v-btn icon="mdi-delete" size="small" variant="text" color="error" :disabled="saving"
                                @click="removeRow(item)" />
                        </template>
                    </v-data-table>
                </v-form>
            </v-card-text>

            <v-divider />

            <v-card-actions>
                <span v-if="draftRows.length" class="text-caption text-medium-emphasis ml-2">
                    {{ draftRows.length }} unsaved {{ draftRows.length === 1 ? 'row' : 'rows' }}
                </span>
                <v-spacer />
                <v-btn variant="text" :disabled="saving" @click="onClose">Close</v-btn>
            </v-card-actions>
        </v-card>
    </v-dialog>
</template>

<script lang="ts" setup>
import { ref, computed, watch } from 'vue'
import { VForm } from 'vuetify/components'
import { useAdminStore } from '../stores/admin'
import { useConfirmDialog } from '../composables/useConfirmDialog'
import {
    PermissionAction, PermissionRead, PermissionResource, PermissionRow, PermissionScope, RoleRead,
} from '../models/types'
import { permissionActionRules, permissionResourceRules, permissionScopeRules } from '../utils/validation'

const props = defineProps<{
    modelValue: boolean
    role: RoleRead | null
}>()

const emit = defineEmits<{
    (e: 'update:modelValue', value: boolean): void
    (e: 'permissions-changed', permissions: PermissionRead[]): void
}>()

const store = useAdminStore()
const { confirm } = useConfirmDialog()

const formRef = ref<InstanceType<typeof VForm> | null>(null)
const isFormValid = ref(false)
const saving = ref(false)
const errorMessage = ref<string | null>(null)
const rows = ref<PermissionRow[]>([])

const headers = [
    { title: 'Resource', key: 'resource', width: '20%' },
    { title: 'Action', key: 'action', width: '20%' },
    { title: 'Scope', key: 'scope', width: '15%' },
    { title: 'Description', key: 'description' },
    { title: '', key: 'actions', sortable: false, align: 'end' as const, width: '120px' },
]

// description is optional server-side; the shared rule requires a value, so keep a local one
const descriptionRules = [
    (value: string) => !value || value.length <= 255 || 'Description must be 255 characters or fewer',
]

const isOpen = computed({
    get: () => props.modelValue,
    set: (value: boolean) => emit('update:modelValue', value),
})

const draftRows = computed(() => rows.value.filter(isDraft))

function isDraft(row: PermissionRow): boolean {
    return row.id === null
}

/** Permissions are named `resource:action:scope` by the backend; PermissionRead has no scope field. */
function toRow(permission: PermissionRead): PermissionRow {
    const [resource, action, scope] = permission.name.split(':')
    return {
        key: permission.id,
        id: permission.id,
        resource: (permission.resource ?? resource ?? null) as PermissionResource | null,
        action: (permission.action ?? action ?? null) as PermissionAction | null,
        scope: (scope ?? null) as PermissionScope | null,
        description: permission.description ?? '',
        error: null,
    }
}

function addRow() {
    rows.value = [
        ...rows.value,
        {
            key: `draft-${crypto.randomUUID()}`,
            id: null,
            resource: null,
            action: null,
            scope: null,
            description: '',
            error: null,
        },
    ]
}

async function removeRow(row: PermissionRow) {
    if (isDraft(row)) {
        rows.value = rows.value.filter(r => r.key !== row.key)
        return
    }

    const confirmed = await confirm({
        message: `Remove permission "${row.resource}:${row.action}:${row.scope}" from role "${props.role?.name}"?`,
        confirmText: 'Remove',
        cancelText: 'Cancel',
        color: 'error',
    })
    if (!confirmed || !props.role) return

    const ok = await store.deletePermission(props.role.id, row.id!)
    if (!ok) {
        errorMessage.value = store.error ?? 'Failed to remove the permission.'
        return
    }
    rows.value = rows.value.filter(r => r.key !== row.key)
    emitChanged()
}

function isDuplicate(row: PermissionRow): boolean {
    return rows.value.some(other =>
        other.key !== row.key &&
        other.resource === row.resource &&
        other.action === row.action &&
        other.scope === row.scope)
}

async function onSave(item: PermissionRow | null = null) {

    if (!item) {
        return
    }

    const validation = await formRef.value?.validate()
    if (!validation?.valid || !props.role) return

    saving.value = true
    errorMessage.value = null
    try {
        // no bulk endpoint: POST one at a time, keep failed rows in place so the user can retry
        item.error = null

        if (isDuplicate(item)) {
            item.error = 'This permission is already in the list.'
            return
        }

        const created = await store.createPermission(
            props.role.id,
            '',
            item.description,
            item.resource as PermissionResource,
            item.action as PermissionAction,
            item.scope as PermissionScope,
        )

        if (!created) {
            item.error = store.error ?? 'Failed to save this permission.'
            return;
        }

        const saved = toRow(created)
        rows.value = rows.value.map(r => (r.key === item.key ? saved : r))

        const failed = rows.value.filter(r => r.error)
        errorMessage.value = failed.length ? `${failed.length} permission(s) could not be saved.` : null
        emitChanged()
    } finally {
        saving.value = false
    }
}

function emitChanged() {
    emit('permissions-changed', rows.value.filter(r => !isDraft(r)).map(r => ({
        id: r.id!,
        name: `${r.resource}:${r.action}:${r.scope}`,
        description: r.description,
        resource: r.resource,
        action: r.action,
        created_at: '',
        updated_at: null,
    })))
}

async function onClose() {
    if (draftRows.value.length) {
        const confirmed = await confirm({
            message: 'You have unsaved permissions. Discard them?',
            confirmText: 'Discard',
            cancelText: 'Keep editing',
            color: 'warning',
        })
        if (!confirmed) return
    }
    isOpen.value = false
}

async function loadPermissions(role: RoleRead) {
    errorMessage.value = null
    rows.value = (role.permissions ?? []).map(toRow)

    const fresh = await store.getPermissions(role.id)
    if (fresh) {
        rows.value = fresh.map(toRow)
    } else {
        errorMessage.value = store.error ?? 'Failed to load permissions.'
    }
}

watch(
    () => [props.modelValue, props.role?.id] as const,
    ([open]) => {
        if (open && props.role) {
            loadPermissions(props.role)
        } else if (!open) {
            rows.value = []
            errorMessage.value = null
        }
    },
    { immediate: true },
)

</script>


<style lang="css" scoped>
</style>



