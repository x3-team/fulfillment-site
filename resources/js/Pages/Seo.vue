<script setup>
import { Head, useForm } from '@inertiajs/vue3';
import SaveBar from '../Components/SaveBar.vue';

const props = defineProps({ value: Object, default: Object, changed: Boolean, pages: Object });
const form = useForm({ pages: JSON.parse(JSON.stringify(props.value)) });
const save = () => form.put('/admin/seo', { preserveScroll: true, onSuccess: () => form.defaults() });
const len = (s) => (s || '').length;
</script>

<template>
    <Head title="SEO" />
    <h1 class="text-3xl font-bold">SEO</h1>
    <p class="mt-1 text-ink5">Заголовок и описание страниц для поисковиков и превью ссылок в мессенджерах. Title — до 60–70 знаков, description — до 160.</p>
    <section v-for="(label, path) in pages" :key="path" class="card mt-4">
        <div class="mb-3 flex items-baseline justify-between gap-3">
            <h2 class="text-lg font-semibold">{{ label }}</h2>
            <a :href="`/${path ? path + '/' : ''}`" target="_blank" class="font-mono text-[13px] text-acc">/{{ path ? path + '/' : '' }}</a>
        </div>
        <template v-if="form.pages[path]">
            <label class="lbl">Title <span class="font-mono" :class="len(form.pages[path].title) > 70 ? 'text-bad' : ''">· {{ len(form.pages[path].title) }}</span></label>
            <input v-model="form.pages[path].title" class="inp" />
            <p v-if="form.errors[`pages.${path}.title`]" class="err">{{ form.errors[`pages.${path}.title`] }}</p>
            <label class="lbl mt-3">Description <span class="font-mono" :class="len(form.pages[path].description) > 160 ? 'text-bad' : ''">· {{ len(form.pages[path].description) }}</span></label>
            <textarea v-model="form.pages[path].description" rows="2" class="inp resize-y"></textarea>
            <p v-if="form.errors[`pages.${path}.description`]" class="err">{{ form.errors[`pages.${path}.description`] }}</p>
        </template>
    </section>
    <SaveBar :form="form" section="seo" :changed="changed" @save="save" />
</template>
