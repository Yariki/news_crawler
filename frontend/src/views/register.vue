<template>

    <AuthLayout subtitle="Create your account">
        <v-alert v-if="errorMessage" type="error" variant="tonal" class="mb-4" role="alert" aria-live="polite">
            {{ errorMessage }}
        </v-alert>

        <v-form ref="formRef" @submit.prevent="submit">
            <v-text-field v-model="email" label="Email" type="email" autocomplete="email" :rules="emailRules"
                :disabled="loading" class="mb-2" />
            <v-text-field v-model="username" label="Username" autocomplete="username" :rules="usernameRules"
                :disabled="loading" class="mb-2" />
            <v-text-field v-model="password" label="Password" :type="showPassword ? 'text' : 'password'"
                autocomplete="new-password" :rules="passwordRules"
                :append-inner-icon="showPassword ? 'mdi-eye-off' : 'mdi-eye'" :disabled="loading" class="mb-2"
                @click:append-inner="showPassword = !showPassword" />
            <v-text-field v-model="confirmPassword" label="Confirm password"
                :type="showConfirmPassword ? 'text' : 'password'" autocomplete="new-password"
                :rules="confirmPasswordRules(password)"
                :append-inner-icon="showConfirmPassword ? 'mdi-eye-off' : 'mdi-eye'" :disabled="loading" class="mb-2"
                @click:append-inner="showConfirmPassword = !showConfirmPassword" />

            <v-btn type="submit" color="primary" block size="large" :loading="loading" class="mt-2">
                Create account
            </v-btn>
        </v-form>

        <div class="text-center mt-4">
            <RouterLink to="/login">Back to sign in</RouterLink>
        </div>
    </AuthLayout>

</template>

<script setup lang="ts">
import axios from 'axios';
import { ref, computed } from 'vue';
import { RouterLink, useRouter } from 'vue-router';

import AuthLayout from '../layouts/AuthLayout.vue';
import {useAuthStore} from "../stores/auth";
import {
    emailRules,
    passwordRules,
    usernameRules,
    confirmPasswordRules
} from '../utils/validation';
import {
    UserCreate,
}  from '../models/types';


const router = useRouter();

type VuetifyForm = {
    validate: () => Promise<boolean>
}

const auth = useAuthStore();

const loading = ref<boolean>(false);
const errorMessage = ref<string|null>(null);

const formRef = ref<VuetifyForm | null>(null);
const email = ref<string | null>(null);
const username = ref<string | null>(null);
const password = ref<string | null>(null);
const confirmPassword = ref<string | null>(null);

const showPassword = ref<boolean>(false);
const showConfirmPassword = ref<boolean>(false);


async function submit() {

    if(!formRef.value) return;

    const isValid = await formRef.value.validate();
    if (!isValid) return;

    const request: UserCreate = {
        email: email.value!,
        username: username.value!,
        password: password.value!,
        is_active: true,
   };

    loading.value = true;
    try{
        await auth.register(request);
        await router.push({ path: '/login', query: { registered: 'true' } });
    }catch(error){
        if (axios.isAxiosError(error)) {
            const status = error.response?.status;

            if (status === 400) {
                errorMessage.value = 'Invalid request. Please check your input.';
            } else if (status === 409) {
                errorMessage.value = 'Email or username already exists.';
            } else {
                errorMessage.value = 'An unexpected error occurred. Please try again later.';
            }
        } else {
            errorMessage.value = 'An unexpected error occurred. Please try again later.';
        }
    }finally {
        loading.value = false;
    }
}

</script>

<style lang="css" scoped></style>