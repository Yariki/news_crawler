<template>
    <AuthLayout subtitle="Sign in to continue">
        <v-alert
            v-if="errorMessage"
            type="error"
            variant="tonal"
            class="mb-4"
            role="alert"
            aria-live="polite"
        >
            {{ errorMessage }}
        </v-alert>

        <v-form ref="formRef" @submit.prevent="submit">
            <v-text-field
                v-model="email"
                label="Email"
                type="email"
                autocomplete="email"
                :rules="emailRules"
                :disabled="loading"
                class="mb-2"
            />
            <v-text-field
                v-model="password"
                label="Password"
                :type="showPassword ? 'text' : 'password'"
                autocomplete="current-password"
                :rules="passwordRules"
                :append-inner-icon="showPassword ? 'mdi-eye-off' : 'mdi-eye'"
                :disabled="loading"
                class="mb-2"
                @click:append-inner="showPassword = !showPassword"
            />

            <v-btn
                type="submit"
                color="primary"
                block
                size="large"
                :loading="loading"
                class="mt-2"
            >
                Sign in
            </v-btn>
        </v-form>

        <div class="d-flex justify-space-between mt-4">
            <RouterLink to="/register">Create account</RouterLink>
        </div>
    </AuthLayout>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import axios from 'axios'

import AuthLayout from '../layouts/AuthLayout.vue'
import { useAuthStore } from '../stores/auth'
import { emailRules, passwordRules } from '../utils/validation'

type VuetifyForm = {
    validate: () => Promise<{valid: boolean}>
}

const authStore = useAuthStore();
const route = useRoute();
const router = useRouter();
const formRef = ref<VuetifyForm | null>(null);
const email = ref('');
const password = ref('');
const showPassword = ref(false);
const loading = ref(false);
const errorMessage = ref('');


async function submit() {
    errorMessage.value = '';
    if (!formRef.value) return;

    const { valid } = await formRef.value.validate();
    if (!valid) return;

    loading.value = true;
    try{

        const payload = new URLSearchParams();
        payload.append('username', email.value);
        payload.append('password', password.value);

        await authStore.login(payload);

        const returnUrl = typeof route.query.returnUrl === 'string' ? route.query.returnUrl : '/';
        await router.push(returnUrl);
    }catch(error){
        if (axios.isAxiosError(error)) {
            const status = error.response?.status;

            if (status === 401) {
                errorMessage.value = 'Unable to log in with current credentials';
            } else if(status === 429){
                errorMessage.value = 'Too many attempts.';
            } else {
                errorMessage.value = 'Unable to log in.';
            }
        } else {
            errorMessage.value = 'Unable to sign in with current credentials.';
        }
    }finally {
        loading.value = false;
    }
}

</script>

<style scoped>

</style>