<script setup>
import { Head, useForm } from '@inertiajs/vue3';
import SaveBar from '../Components/SaveBar.vue';

const props = defineProps({ value: Object, default: Object, changed: Boolean, labels: Object, faq: Array, faqDefault: Array, faqChanged: Boolean });
const form = useForm({ texts: JSON.parse(JSON.stringify(props.value)), faq: JSON.parse(JSON.stringify(props.faq)) });
const rows = (s) => Math.min(6, Math.max(1, Math.ceil((s || '').length / 70)));
const addQ = () => form.faq.push({ q: '', a: '' });
const removeQ = (i) => confirm('Удалить вопрос?') && form.faq.splice(i, 1);
const move = (i, d) => { const j = i + d; if (j < 0 || j >= form.faq.length) return; [form.faq[i], form.faq[j]] = [form.faq[j], form.faq[i]]; };
const save = () => form.put('/admin/texts', { preserveScroll: true, onSuccess: () => form.defaults() });
</script>

<template>
    <Head title="Тексты и вопросы" />
    <h1 class="text-3xl font-bold">Тексты и вопросы</h1>
    <p class="mt-1 text-ink5">Заголовки и подводки блоков на главной и раздел «Частые вопросы». Перенос строки — <code class="font-mono text-[13px]">&lt;br&gt;</code>.</p>

    <section class="card mt-6 space-y-4">
        <h2 class="text-lg font-semibold">Заголовки блоков</h2>
        <div v-for="(label, k) in labels" :key="k">
            <label class="lbl" :for="k">{{ label }} <span v-if="form.texts[k] !== props.default[k]" class="text-acc">· изменено</span></label>
            <textarea :id="k" v-model="form.texts[k]" :rows="rows(form.texts[k])" class="inp resize-y"></textarea>
            <p v-if="form.errors[`texts.${k}`]" class="err">{{ form.errors[`texts.${k}`] }}</p>
        </div>
    </section>

    <section class="card mt-4">
        <div class="mb-4 flex items-baseline justify-between">
            <h2 class="text-lg font-semibold">Частые вопросы</h2>
            <button class="btn btn-line !py-1.5 text-[14px]" @click="addQ">+ Вопрос</button>
        </div>
        <div v-for="(f, i) in form.faq" :key="i" class="border-t border-line py-4 first-of-type:border-t-0 first-of-type:pt-0">
            <div class="flex items-center gap-2">
                <span class="font-mono text-[13px] text-ink5">{{ String(i + 1).padStart(2, '0') }}</span>
                <input v-model="f.q" class="inp font-semibold" placeholder="Вопрос" />
                <button class="btn btn-ghost !px-2" :disabled="i === 0" @click="move(i, -1)">↑</button>
                <button class="btn btn-ghost !px-2" :disabled="i === form.faq.length - 1" @click="move(i, 1)">↓</button>
                <button class="btn btn-ghost !px-2 hover:!text-bad" @click="removeQ(i)">✕</button>
            </div>
            <p v-if="form.errors[`faq.${i}.q`]" class="err">{{ form.errors[`faq.${i}.q`] }}</p>
            <textarea v-model="f.a" :rows="rows(f.a)" class="inp mt-2 resize-y" placeholder="Ответ"></textarea>
            <p v-if="form.errors[`faq.${i}.a`]" class="err">{{ form.errors[`faq.${i}.a`] }}</p>
        </div>
    </section>

    <SaveBar :form="form" section="texts" :changed="changed || faqChanged" @save="save" />
</template>
