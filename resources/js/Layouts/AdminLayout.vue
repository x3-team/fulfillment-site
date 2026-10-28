<script setup>
import { Link, router, usePage } from '@inertiajs/vue3';
import { computed } from 'vue';

const page = usePage();
const nav = [
    { href: '/admin/calculator', label: 'Калькулятор' },
    { href: '/admin/contacts', label: 'Контакты' },
    { href: '/admin/texts', label: 'Тексты и вопросы' },
    { href: '/admin/seo', label: 'SEO' },
];
const active = computed(() => page.url.split('?')[0]);
</script>

<template>
    <div class="min-h-screen">
        <header class="sticky top-0 z-20 border-b border-line bg-white/90 backdrop-blur">
            <div class="mx-auto flex max-w-5xl flex-wrap items-center gap-x-6 gap-y-2 px-4 py-3">
                <a href="/" target="_blank" class="flex items-center gap-2 font-bold">
                    <img src="/favicon.svg" alt="" class="h-7 w-7" />
                    <span>Товар в деле</span>
                    <span class="font-mono text-[11px] font-medium uppercase tracking-wider text-ink5">админка</span>
                </a>
                <nav class="order-3 -mx-1 flex w-full gap-1 overflow-x-auto sm:order-none sm:w-auto">
                    <Link v-for="n in nav" :key="n.href" :href="n.href"
                        class="whitespace-nowrap rounded-lg px-3 py-1.5 text-[15px] font-medium"
                        :class="active === n.href ? 'bg-acc1 text-acc' : 'text-ink5 hover:text-ink'">{{ n.label }}</Link>
                </nav>
                <div class="ml-auto flex items-center gap-3 text-[14px] text-ink5">
                    <span class="hidden md:inline">{{ page.props.user?.email }}</span>
                    <button class="btn-ghost" @click="router.post('/admin/logout')">Выйти</button>
                </div>
            </div>
        </header>
        <main class="mx-auto max-w-5xl px-4 pb-32 pt-6">
            <slot />
        </main>
    </div>
</template>
