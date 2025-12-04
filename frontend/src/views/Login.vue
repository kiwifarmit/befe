<script setup>
import { ref } from "vue";
import { useRouter } from "vue-router";
import { login as authLogin } from "../utils/auth";

const email = ref("");
const password = ref("");
const error = ref("");
const router = useRouter();

const login = async () => {
  try {
    error.value = "";
    await authLogin(email.value, password.value);
    router.push("/");
  } catch (e) {
    error.value = e.message || "Invalid credentials";
  }
};
</script>

<template>
  <div class="bg-white p-8 rounded-lg shadow-md mb-4">
    <h2 class="text-2xl font-semibold mb-4 text-gray-800">Login</h2>
    <div v-if="error" class="text-red-500 mb-4">{{ error }}</div>
    <form class="space-y-4" @submit.prevent="login">
      <input
        v-model="email"
        type="email"
        placeholder="Email"
        required
        autocomplete="email"
        name="email"
        class="w-full p-2 border border-gray-300 rounded"
      />
      <input
        v-model="password"
        type="password"
        placeholder="Password"
        required
        autocomplete="current-password"
        name="password"
        class="w-full p-2 border border-gray-300 rounded"
      />
      <button
        type="submit"
        class="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded cursor-pointer border-none w-full"
      >
        Login
      </button>
    </form>
    <p class="mt-4 mb-0 text-center">
      <router-link
        to="/forgot-password"
        class="text-blue-500 hover:text-blue-600 hover:underline text-sm no-underline transition-colors"
      >
        Forgot Password?
      </router-link>
    </p>
  </div>
</template>
