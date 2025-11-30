<script setup>
import { useRouter, useRoute } from 'vue-router';
import { ref, computed, onMounted, watch } from 'vue';
import { isAuthenticated, logout as authLogout, getCurrentUser, isAdmin } from './utils/auth';

const router = useRouter();
const route = useRoute();
const isLoggedIn = ref(false);
const currentUser = ref(null);
const userIsAdmin = ref(false);

const checkAuth = async () => {
  isLoggedIn.value = isAuthenticated();
  if (isLoggedIn.value) {
    currentUser.value = await getCurrentUser();
    userIsAdmin.value = await isAdmin();
  } else {
    currentUser.value = null;
    userIsAdmin.value = false;
  }
};

onMounted(() => {
  checkAuth();
  // Check auth status whenever route changes
  router.afterEach(() => {
    checkAuth();
  });
});

// Watch route changes to refresh user data
watch(() => route.path, () => {
  if (isLoggedIn.value) {
    checkAuth();
  }
});

const logout = () => {
  authLogout();
  isLoggedIn.value = false;
  currentUser.value = null;
  userIsAdmin.value = false;
  router.push('/login');
};

const pageTitle = computed(() => {
  return route.meta.title || 'App';
});

const isActiveRoute = (path) => {
  return route.path === path;
};
</script>

<template>
  <div class="max-w-3xl mx-auto p-8 min-h-screen">
    <header v-if="isLoggedIn" class="mb-8 pb-4 border-b-2 border-gray-200">
      <div class="flex justify-between items-center mb-4">
        <h1 class="m-0 text-2xl text-gray-800">{{ pageTitle }}</h1>
        <button @click="logout" class="bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded cursor-pointer border-none">
          Logout
        </button>
      </div>
      
      <!-- Navigation Menu -->
      <nav class="flex gap-4 border-b border-gray-200">
        <router-link 
          to="/profile"
          :class="[
            'px-4 py-2 text-sm font-medium transition-colors',
            isActiveRoute('/profile')
              ? 'text-blue-600 border-b-2 border-blue-600'
              : 'text-gray-600 hover:text-gray-900'
          ]"
        >
          Profile
        </router-link>
        <router-link 
          to="/sum"
          :class="[
            'px-4 py-2 text-sm font-medium transition-colors',
            isActiveRoute('/sum')
              ? 'text-blue-600 border-b-2 border-blue-600'
              : 'text-gray-600 hover:text-gray-900'
          ]"
        >
          Sum
        </router-link>
        <router-link 
          v-if="userIsAdmin"
          to="/admin/users"
          :class="[
            'px-4 py-2 text-sm font-medium transition-colors',
            isActiveRoute('/admin/users')
              ? 'text-blue-600 border-b-2 border-blue-600'
              : 'text-gray-600 hover:text-gray-900'
          ]"
        >
          Admin Users
        </router-link>
      </nav>
    </header>
    <router-view></router-view>
  </div>
</template>
