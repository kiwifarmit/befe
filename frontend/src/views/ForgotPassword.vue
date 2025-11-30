<script setup>
import { ref } from 'vue';

const email = ref('');
const message = ref('');
const error = ref('');
const loading = ref(false);

const requestReset = async () => {
  // Reset states
  message.value = '';
  error.value = '';
  loading.value = true;

  try {
    const response = await fetch('/auth/forgot-password', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email: email.value }),
    });

    // FastAPI returns 202 for forgot password
    if (response.ok || response.status === 202) {
      message.value = 'If the email exists, a reset link has been sent to your inbox.';
      error.value = '';
    } else {
      const data = await response.json();
      throw new Error(data.detail || 'Request failed');
    }
  } catch (e) {
    console.error('Password reset error:', e);
    error.value = e.message || 'Failed to request reset. Please try again.';
    message.value = '';
  } finally {
    loading.value = false;
  }
};
</script>

<template>
  <div class="bg-white p-8 rounded-lg shadow-md mb-4">
    <h2 class="text-2xl font-semibold mb-4 text-gray-800">Forgot Password</h2>
    <p class="text-gray-600 mb-6">Enter your email address and we'll send you a link to reset your password.</p>
    
    <div v-if="message" class="text-green-600 bg-green-100 p-3 rounded mb-4 border-l-4 border-green-600">
      <strong>✓</strong> {{ message }}
    </div>
    <div v-if="error" class="text-red-500 mb-4">
      <strong>✗</strong> {{ error }}
    </div>
    
    <form @submit.prevent="requestReset" class="space-y-4">
      <input 
        v-model="email" 
        type="email" 
        placeholder="Email" 
        required 
        :disabled="loading"
        autocomplete="email"
        name="email"
        class="w-full p-2 border border-gray-300 rounded disabled:opacity-60 disabled:cursor-not-allowed"
      />
      <button 
        type="submit" 
        :disabled="loading"
        class="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded cursor-pointer border-none w-full disabled:opacity-60 disabled:cursor-not-allowed"
      >
        {{ loading ? 'Sending...' : 'Request Reset' }}
      </button>
    </form>
    
    <p class="mt-4 text-center">
      <router-link to="/login" class="text-blue-500 hover:text-blue-600 hover:underline no-underline transition-colors">
        ← Back to Login
      </router-link>
    </p>
  </div>
</template>
