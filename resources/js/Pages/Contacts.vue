<script setup>
import { Head, useForm } from '@inertiajs/vue3';
import SaveBar from '../Components/SaveBar.vue';

const props = defineProps({ value: Object, default: Object, changed: Boolean, fields: Object });
const form = useForm(JSON.parse(JSON.stringify(props.value)));
const save = () => form.put('/admin/contacts', { preserveScroll: true, onSuccess: () => form.defaults() });
</script>

<template>
    <Head title="Контакты" />
    <h1 class="text-3xl font-bold">Контакты</h1>
    <p class="mt-1 text-ink5">Меняются на всех страницах фулфилмента: в шапке, подвале, на «Контактах», в документах и в разметке для поисковиков.</p>
    <section class="card mt-6 space-y-5">
        <div v-for="(f, k) in fields" :key="k">
            <label class="lbl" :for="k">{{ f.label }}</label>
            <input :id="k" v-model="form[k]" class="inp" />
            <p v-if="form.errors[k]" class="err">{{ form.errors[k] }}</p>
            <p v-else class="mt-1 text-[13px] text-ink5">{{ f.hint }} <span v-if="form[k] !== f.default">В вёрстке: {{ f.default }}</span></p>
        </div>
        <p class="rounded-lg bg-paper px-4 py-3 text-[14px] text-ink5">Точку на Яндекс.Карте адрес не двигает. Если склад переедет, напишите разработчику, он поменяет координаты.</p>
    </section>
    <SaveBar :form="form" section="contacts" :changed="changed" preview="/kontakty/" @save="save" />
</template>
