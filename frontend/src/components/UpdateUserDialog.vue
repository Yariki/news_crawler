<template>
    <v-dialog v-model="isOpen" persistent max-width="500px">
        <v-card>
            <v-card-title>
                Update User
            </v-card-title>

            <v-card-text>
                <v-form v-model="isFormValid" @submit.prevent="onUpdate">
                    <v-text-field v-model="formData.email" label="Email" :rules="emailRules" type="email"
                        required></v-text-field>
                    <v-text-field v-model="formData.username" label="Username" :rules="usernameRules"
                        required></v-text-field>
                    <v-switch v-model="formData.is_active" label="Active"></v-switch>
                </v-form>
            </v-card-text>

            <v-card-actions>
                <v-spacer></v-spacer>
                <v-btn color="primary" text @click="onCancel">Cancel</v-btn>
                <v-btn color="primary" text :disabled="!isFormValid" @click="onUpdate">Update</v-btn>
            </v-card-actions>
        </v-card>
    </v-dialog>
</template>

<script lang="ts" setup>
import { ref, computed, watch } from 'vue';
import { emailRules, usernameRules} from "../utils/validation";
import { UpdateUserDialogData } from '../models/types';


const props = defineProps<{
    modelValue: boolean;
    data: UpdateUserDialogData;
}>();

const emit = defineEmits<{
    (e: 'update:modelValue', value: boolean): void;
    (e: 'update-user', data: UpdateUserDialogData): void;
}>();

const isOpen = computed({
    get: () => props.modelValue,
    set: (value: boolean) => emit('update:modelValue', value),
});

const formData = ref<UpdateUserDialogData>({
    id: '',
    email: '',
    username: '',
    is_active: true,
});

watch(() => props.data, (newData) => {
    if (newData) {
        formData.value = { ...newData };
    }
}, { immediate: true });

const isFormValid = ref(false);

function onCancel() {
    isOpen.value = false;
}

async function onUpdate() {
    emit('update-user', formData.value);
    isOpen.value = false;
}

</script>

<style lang="css" scoped></style>
