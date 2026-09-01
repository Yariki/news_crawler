<template>
    <v-dialog v-model="isOpen" max-width="400px" persistent>
        <v-card>
            <v-card-title v-if="options.title" class="text-h6">
                {{ options.title }}
            </v-card-title>

            <v-card-text>
                {{ options.message }}
            </v-card-text>

            <v-card-actions>
                <v-spacer />
                <v-btn variant="text" @click="handleCancel">
                    {{ options.cancelText }}
                </v-btn>
                <v-btn :color="options.color" variant="flat" @click="handleConfirm">
                    {{ options.confirmText }}
                </v-btn>
            </v-card-actions>
        </v-card>
    </v-dialog>
</template>

<script setup lang="ts">

import {storeToRefs} from 'pinia'
import { useConfirmDialog } from '../composables/useConfirmDialog';

const store = useConfirmDialog();

const { isOpen, options } = storeToRefs(store);
const { handleCancel, handleConfirm } = store;


</script>