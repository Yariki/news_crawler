<template>
    <v-dialog v-model="isOpen" persistent max-width="500px">
        <v-card>
            <v-card-title>
                Create User
            </v-card-title>

            <v-card-text>
                <v-form v-model="isFormValid" @submit.prevent="onCreate">
                    <v-text-field v-model="formData.email" label="Email" :rules="emailRules" type="email"
                        required></v-text-field>
                    <v-text-field v-model="formData.username" label="Username" :rules="usernameRules"
                        required></v-text-field>
                    <v-switch v-model="formData.is_active" label="Active"></v-switch>
                    <v-text-field v-model="formData.password" label="Password" :rules="passwordRules" type="password"
                        required></v-text-field>
                    <v-text-field v-model="formData.confirm_password" label="Confirm Password"
                        :rules="[...confirmPasswordRules(formData.password)]" type="password" required></v-text-field>
                </v-form>
            </v-card-text>

            <v-card-actions>
                <v-spacer></v-spacer>
                <v-btn color="primary" text @click="onCancel">Cancel</v-btn>
                <v-btn color="primary" text :disabled="!isFormValid" @click="onCreate">Create</v-btn>
            </v-card-actions>
        </v-card>
    </v-dialog>
</template>

<script lang="ts" setup>
import { ref, computed } from 'vue';
import { emailRules, usernameRules, passwordRules, confirmPasswordRules } from "../utils/validation";
import { CreateUserDialogData } from '../models/types';

const props = defineProps<{
    modelValue: boolean;
}>();

const emit = defineEmits<{
    (e: 'update:modelValue', value: boolean): void;
    (e: 'create-user', data: CreateUserDialogData): void;
}>();

const isOpen = computed({
    get: () => props.modelValue,
    set: (value: boolean) => emit('update:modelValue', value),
});

const formData = ref<CreateUserDialogData>({
    email: '',
    username: '',
    is_active: true,
    password: '',
    confirm_password: '',
});

const isFormValid = ref(false);

function onCancel() {
    isOpen.value = false;
}

async function onCreate() {
    emit('create-user', formData.value);
    isOpen.value = false;
}

</script>

<style lang="css" scoped></style>
