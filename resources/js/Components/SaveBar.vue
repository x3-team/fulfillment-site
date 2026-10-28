<script setup>
import { router, usePage } from '@inertiajs/vue3';
import { ref, watch } from 'vue';

const props = defineProps({ form: Object, section: String, changed: Boolean, preview: { type: String, default: '/' } });
const emit = defineEmits(['save']);
const page = usePage();
const shown = ref(null);
let timer;
watch(() => page.props.flash, (v) => {
    shown.value = v;
    clearTimeout(timer);
    timer = setTimeout(() => (shown.value = null), 4000);
}, { immediate: true });

const reset = () => {
    if (confirm('Вернуть значения, которые сейчас в вёрстке сайта? Ваши правки в этом разделе удалятся.')) {
        router.post(`/admin/reset/${props.section}`, {}, { preserveScroll: true, preserveState: false });
    }
};
</script>

<template>
    <div class="fixed inset-x-0 bottom-0 z-20 border-t border-line bg-white/95 backdrop-blur">
        <div class="mx-auto flex max-w-5xl flex-wrap items-center gap-3 px-4 py-3">
            <button class="btn btn-primary" :disabled="form.processing || !form.isDirty" @click="emit('save')">
                {{ form.processing ? 'Сохраняем…' : 'Сохранить' }}
            </button>
            <a :href="preview" target="_blank" class="btn btn-line">Открыть на сайте ↗</a>
            <span v-if="form.hasErrors" class="text-[14px] text-bad">Проверьте поля, отмеченные красным</span>
            <span v-else-if="shown" class="text-[14px] text-ok">✓ {{ shown }}</span>
            <span v-else-if="form.isDirty" class="text-[14px] text-ink5">Есть несохранённые изменения</span>
            <button v-if="changed" class="btn-ghost ml-auto text-[14px]" @click="reset">Вернуть как в вёрстке</button>
        </div>
    </div>
</template>
