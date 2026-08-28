import { defineStore } from 'pinia';
import { ref } from 'vue';

export interface ConfirmDialogOptions {
    title?: string;
    message: string;

    confirmText?: string;
    cancelText?: string;
    color?: string;
}

export const useConfirmDialog = defineStore('confirmDialog', () => {
    const isOpen = ref<boolean>(false);
    const options = ref<ConfirmDialogOptions>({ message: '' });
    let resolvePromise: (value: boolean) => void;

    const confirm = (opts: ConfirmDialogOptions) => {
        options.value = {
            title: 'Confirm Action',
            confirmText: 'Confirm',
            cancelText: 'Cancel',
            color: 'primary',
            ...opts
        };
        isOpen.value = true;

        return new Promise((resolve) => {
            resolvePromise = resolve;
        });
    };

    const handleConfirm = () => {
        isOpen.value = false;
        resolvePromise(true);
    };

    const handleCancel = () => {
        isOpen.value = false;
        resolvePromise(false);
    }

    return {
        isOpen,
        options,
        confirm,
        handleConfirm,
        handleCancel
    };
});
