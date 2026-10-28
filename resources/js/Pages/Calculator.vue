<script setup>
import { Head, useForm } from '@inertiajs/vue3';
import SaveBar from '../Components/SaveBar.vue';

const props = defineProps({ value: Object, default: Object, changed: Boolean });
const form = useForm(JSON.parse(JSON.stringify(props.value)));

const groups = [
    { key: 'unload', title: 'Разгрузка', hint: 'Посетитель выбирает один вариант и указывает количество.', qty: true },
    { key: 'work', title: 'Работы с товаром', hint: 'Можно отметить несколько. Количество по умолчанию равно размеру партии.' },
    { key: 'fbs', title: 'FBS под ключ', hint: 'Можно выбрать только один вариант.' },
    { key: 'fbo', title: 'FBO', hint: '' },
];
const add = (g) => form[g.key].push({ id: 'op' + Date.now().toString(36), name: '', sub: '', label: '', price: 0, per: 'за ед.', on: false, ...(g.qty ? { qty: 1 } : {}) });
const remove = (g, i) => confirm(`Удалить «${form[g.key][i].name || 'без названия'}»?`) && form[g.key].splice(i, 1);
const move = (g, i, d) => { const a = form[g.key]; const j = i + d; if (j < 0 || j >= a.length) return; [a[i], a[j]] = [a[j], a[i]]; };
const err = (k) => form.errors[k];
const save = () => form.put('/admin/calculator', { preserveScroll: true, onSuccess: () => form.defaults() });
</script>

<template>
    <Head title="Калькулятор" />
    <h1 class="text-3xl font-bold">Калькулятор</h1>
    <p class="mt-1 text-ink5">Цены и операции в калькуляторе на главной. После сохранения сайт сразу считает по новым ценам.</p>

    <section class="card mt-6">
        <h2 class="mb-4 text-lg font-semibold">Общие параметры</h2>
        <div class="grid gap-4 sm:grid-cols-4">
            <div>
                <label class="lbl">Приёмка, ₽ за ед.</label>
                <input v-model.number="form.accept" type="number" min="0" step="0.5" class="inp num" />
                <p v-if="err('accept')" class="err">{{ err('accept') }}</p>
            </div>
            <div>
                <label class="lbl">Скидка на первую партию, %</label>
                <input v-model.number="form.discount" type="number" min="0" max="100" class="inp num" />
                <p v-if="err('discount')" class="err">{{ err('discount') }}</p>
            </div>
            <div>
                <label class="lbl">Хранение, ₽ за литр в сутки</label>
                <input v-model.number="form.storage.rate" type="number" min="0" step="0.01" class="inp num" />
                <p v-if="err('storage.rate')" class="err">{{ err('storage.rate') }}</p>
            </div>
            <div>
                <label class="lbl">Бесплатных дней хранения</label>
                <input v-model.number="form.storage.free_days" type="number" min="0" class="inp num" />
                <p v-if="err('storage.free_days')" class="err">{{ err('storage.free_days') }}</p>
            </div>
        </div>
    </section>

    <section v-for="g in groups" :key="g.key" class="card mt-4">
        <div class="mb-4 flex items-baseline justify-between gap-4">
            <div>
                <h2 class="text-lg font-semibold">{{ g.title }}</h2>
                <p v-if="g.hint" class="text-[14px] text-ink5">{{ g.hint }}</p>
            </div>
            <button class="btn btn-line shrink-0 !py-1.5 text-[14px]" @click="add(g)">+ Добавить</button>
        </div>
        <p v-if="!form[g.key].length" class="rounded-lg bg-paper px-4 py-3 text-[14px] text-ink5">Пока пусто, блок на сайте будет без вариантов.</p>
        <div v-for="(it, i) in form[g.key]" :key="it.id" class="border-t border-line py-4 first-of-type:border-t-0 first-of-type:pt-0">
            <div class="grid gap-3 sm:grid-cols-12">
                <div class="sm:col-span-5">
                    <label class="lbl">Название</label>
                    <input v-model="it.name" class="inp" />
                    <p v-if="err(`${g.key}.${i}.name`)" class="err">{{ err(`${g.key}.${i}.name`) }}</p>
                </div>
                <div class="sm:col-span-2">
                    <label class="lbl">Цена, ₽</label>
                    <input v-model.number="it.price" type="number" min="0" step="0.5" class="inp num" />
                    <p v-if="err(`${g.key}.${i}.price`)" class="err">{{ err(`${g.key}.${i}.price`) }}</p>
                </div>
                <div class="sm:col-span-2">
                    <label class="lbl">Единица</label>
                    <input v-model="it.per" class="inp" placeholder="за ед." />
                </div>
                <div v-if="g.qty" class="sm:col-span-2">
                    <label class="lbl">Кол-во по умолч.</label>
                    <input v-model.number="it.qty" type="number" min="1" class="inp num" />
                </div>
                <div class="flex items-end gap-1 sm:col-span-1" :class="g.qty ? '' : 'sm:col-span-3 sm:justify-end'">
                    <button class="btn btn-ghost !px-2" title="Выше" :disabled="i === 0" @click="move(g, i, -1)">↑</button>
                    <button class="btn btn-ghost !px-2" title="Ниже" :disabled="i === form[g.key].length - 1" @click="move(g, i, 1)">↓</button>
                    <button class="btn btn-ghost !px-2 hover:!text-bad" title="Удалить" @click="remove(g, i)">✕</button>
                </div>
                <div class="sm:col-span-7">
                    <label class="lbl">Пояснение под названием</label>
                    <input v-model="it.sub" class="inp" />
                </div>
                <div class="sm:col-span-5">
                    <label class="lbl">Строка в расчёте <span class="font-normal">(если пусто — название)</span></label>
                    <input v-model="it.label" class="inp" :placeholder="it.name" />
                </div>
            </div>
            <label class="mt-3 inline-flex cursor-pointer items-center gap-2 text-[14px]">
                <input v-model="it.on" type="checkbox" class="h-4 w-4 accent-acc" /> Отмечено по умолчанию
            </label>
        </div>
        <p v-if="err(g.key)" class="err">{{ err(g.key) }}</p>
    </section>

    <SaveBar :form="form" section="calculator" :changed="changed" preview="/#calc" @save="save" />
</template>
