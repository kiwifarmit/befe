<script setup>
import { ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';

const password = ref('');
const error = ref('');
const route = useRoute();
const router = useRouter();
const token = route.query.token;

const resetPassword = async () => {
  try {
    const response = await fetch('/auth/reset-password', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ token, password: password.value }),
    });

    if (!response.ok) {
      throw new Error('Reset failed');
    }

    router.push('/login');
  } catch (e) {
    error.value = 'Failed to reset password';
  }
};
</script>

<template>
  <div class="bg-white p-8 rounded-lg shadow-md mb-4">
    <h2 class="text-2xl font-semibold mb-4 text-gray-800">Reset Password</h2>
    <div v-if="error" class="text-red-500 mb-4">{{ error }}</div>
    <form @submit.prevent="resetPassword" class="space-y-4">
      <input 
        v-model="password" 
        type="password" 
        placeholder="New Password" 
        required 
        class="w-full p-2 border border-gray-300 rounded"
      />
      <button type="submit" class="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded cursor-pointer border-none w-full">
        Reset Password
      </button>
    </form>
  </div>
</template>
