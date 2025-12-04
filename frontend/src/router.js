import { createRouter, createWebHistory } from "vue-router";
import Login from "./views/Login.vue";
import Dashboard from "./views/Dashboard.vue";
import ForgotPassword from "./views/ForgotPassword.vue";
import ResetPassword from "./views/ResetPassword.vue";
import Profile from "./views/Profile.vue";
import AdminUsers from "./views/AdminUsers.vue";
import { isAuthenticated } from "./utils/auth";

const routes = [
  {
    path: "/login",
    component: Login,
    meta: { title: "Login", requiresAuth: false },
  },
  {
    path: "/forgot-password",
    component: ForgotPassword,
    meta: { title: "Forgot Password", requiresAuth: false },
  },
  {
    path: "/reset-password",
    component: ResetPassword,
    meta: { title: "Reset Password", requiresAuth: false },
  },
  {
    path: "/",
    redirect: "/profile",
  },
  {
    path: "/dashboard",
    component: Dashboard,
    meta: { title: "Dashboard - Sum Calculator", requiresAuth: true },
  },
  {
    path: "/profile",
    component: Profile,
    meta: { title: "My Profile", requiresAuth: true },
  },
  {
    path: "/admin/users",
    component: AdminUsers,
    meta: { title: "User Management", requiresAuth: true, requiresAdmin: true },
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

router.beforeEach(async (to, from, next) => {
  // Update document title
  document.title = to.meta.title || "Minimalist Web App";

  if (to.meta.requiresAuth && !isAuthenticated()) {
    next("/login");
  } else if (to.meta.requiresAdmin) {
    // Check if user is admin
    const { isAdmin } = await import("./utils/auth");
    const admin = await isAdmin();
    if (!admin) {
      next("/profile");
    } else {
      next();
    }
  } else {
    next();
  }
});

export default router;
