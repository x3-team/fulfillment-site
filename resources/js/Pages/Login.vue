<script setup>
import { Head, useForm } from '@inertiajs/vue3';

const form = useForm({ email: '', password: '' });
const submit = () => form.post('/admin/login', { onFinish: () => form.reset('password') });
</script>

<template>
    <Head title="Вход" />
    <div class="flex min-h-screen items-center justify-center px-4">
        <form class="card w-full max-w-sm" @submit.prevent="submit">
            <div class="mb-6 flex items-center gap-2 text-lg font-bold">
                <img src="/favicon.svg" alt="" class="h-8 w-8" /> Товар в деле
            </div>
            <h1 class="mb-5 text-2xl font-bold">Вход в админку</h1>
            <label class="lbl" for="email">Почта</label>
            <input id="email" v-model="form.email" type="email" class="inp" autocomplete="username" autofocus />
            <p v-if="form.errors.email" class="err">{{ form.errors.email }}</p>
            <label class="lbl mt-4" for="password">Пароль</label>
            <input id="password" v-model="form.password" type="password" class="inp" autocomplete="current-password" />
            <button class="btn btn-primary mt-6 w-full" :disabled="form.processing">Войти</button>
        </form>
    </div>
</template>
