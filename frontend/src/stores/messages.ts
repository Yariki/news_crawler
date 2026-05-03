import {defineStore} from "pinia";

interface Message {
    text: string,
    color: string,
}

export const useMessages  = defineStore("messages", {
    state: () => ({
        queue: [] as Message[]
    }),
    actions: {
        addMessage(msg: string) {
            this.queue.push({
                text: msg,
                color: 'primary'
            });
        },
        onError(err: string) {
            this.queue.push({
                text: err,
                color: 'error'
            })
        },
    },
})
