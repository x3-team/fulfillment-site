import '../css/admin.css';
import { createApp, h } from 'vue';
import { createInertiaApp } from '@inertiajs/vue3';
import AdminLayout from './Layouts/AdminLayout.vue';

createInertiaApp({
    title: (t) => (t ? `${t} — админка «Товар в деле»` : 'Админка «Товар в деле»'),
    resolve: (name) => {
        const page = import.meta.glob('./Pages/**/*.vue', { eager: true })[`./Pages/${name}.vue`];
        page.default.layout ??= name === 'Login' ? undefined : AdminLayout;
        return page;
    },
    setup({ el, App, props, plugin }) {
        createApp({ render: () => h(App, props) }).use(plugin).mount(el);
    },
    progress: { color: '#1A5CFF' },
});
