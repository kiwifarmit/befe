<script setup>
import { useRouter, useRoute } from 'vue-router';
import { ref, computed, onMounted } from 'vue';
import { isAuthenticated, logout as authLogout } from './utils/auth';

const router = useRouter();
const route = useRoute();
const isLoggedIn = ref(false);

const checkAuth = () => {
  isLoggedIn.value = isAuthenticated();
};

onMounted(() => {
  checkAuth();
  // Check auth status whenever route changes
  router.afterEach(() => {
    checkAuth();
  });
});

const logout = () => {
  authLogout();
  isLoggedIn.value = false;
  router.push('/login');
};

const pageTitle = computed(() => {
  return route.meta.title || 'App';
});
</script>

<template>
  <div class="max-w-3xl mx-auto p-8 min-h-screen">
    <header v-if="isLoggedIn" class="mb-8 pb-4 border-b-2 border-gray-200">
      <div class="flex justify-between items-center">
        <h1 class="m-0 text-2xl text-gray-800">{{ pageTitle }}</h1>
        <button @click="logout" class="bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded cursor-pointer border-none">
          Logout
        </button>
      </div>
    </header>
    <router-view></router-view>
  </div>
</template>
