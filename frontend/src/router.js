import { createRouter, createWebHistory } from 'vue-router';
import Login from './views/Login.vue';
import Dashboard from './views/Dashboard.vue';
import ForgotPassword from './views/ForgotPassword.vue';
import ResetPassword from './views/ResetPassword.vue';
import { isAuthenticated } from './utils/auth';

const routes = [
    {
        path: '/login',
        component: Login,
        meta: { title: 'Login', requiresAuth: false }
    },
    {
        path: '/forgot-password',
        component: ForgotPassword,
        meta: { title: 'Forgot Password', requiresAuth: false }
    },
    {
        path: '/reset-password',
        component: ResetPassword,
        meta: { title: 'Reset Password', requiresAuth: false }
    },
    {
        path: '/',
        component: Dashboard,
        meta: { title: 'Dashboard - Sum Calculator', requiresAuth: true }
    },
];

const router = createRouter({
    history: createWebHistory(),
    routes,
});

router.beforeEach((to, from, next) => {
    // Update document title
    document.title = to.meta.title || 'Minimalist Web App';

    if (to.meta.requiresAuth && !isAuthenticated()) {
        next('/login');
    } else {
        next();
    }
});

export default router;
