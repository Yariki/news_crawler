<template>
    <v-dialog v-model="isOpen" persistent max-width="500px">
        <v-card>
            <v-card-title>{{ isEditMode ? 'Edit Role' : 'Create Role' }}</v-card-title>
            <v-card-text>
                <v-form v-model="isFormValid" @submit.prevent="onCreate">
                    <v-text-field v-model="formData.name" label="Name" :rules="roleNameRules" required />
                    <v-textarea v-model="formData.description" label="Description" rows="2" />
                </v-form>
            </v-card-text>
            <v-card-actions>
                <v-spacer />
                <v-btn text @click="onCancel">Cancel</v-btn>
                <v-btn color="primary" text :disabled="!isFormValid" @click="onCreate">{{ isEditMode ? 'Save' : 'Create' }}</v-btn>
            </v-card-actions>
        </v-card>
    </v-dialog>

</template>

<script setup lang="ts">
import { ref, computed, watch} from 'vue'
import { roleNameRules } from '../utils/validation'
import { RoleCreateUpdate } from '../models/types';

const props = defineProps<{
    modelValue: boolean,
    formData: RoleCreateUpdate
    isEditMode: boolean
}>();

const emits = defineEmits<{
    (e: 'update:modelValue', value: boolean): void
    (e: 'create-role', roleData: RoleCreateUpdate): void
}>();

const isFormValid = ref(false);

const isOpen = computed({
    get: () => props.modelValue,
    set: (value: boolean) => emits('update:modelValue', value),
});

const formData = ref<RoleCreateUpdate>({
    name: '',
    description: '',
    is_system: false,
});

function onCancel() {
    isOpen.value = false;
}

function onCreate() {
    if (isFormValid.value) {
        emits('create-role', formData.value);
        isOpen.value = false;
        formData.value = {
            name: '',
            description: '',
            is_system: false,
        };
    }
}

watch(() => props.formData, (newValue) => {
    formData.value = { ...newValue };
}, { immediate: true });

</script>

<style lang="css" scoped>
</style>