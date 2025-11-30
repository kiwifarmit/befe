<script setup>
import { ref, watch } from 'vue';
import { useRouter } from 'vue-router';
import { authenticatedFetch, isAuthenticated } from '../utils/auth';

const router = useRouter();
const a = ref(0);
const b = ref(0);
const result = ref(null);
const error = ref('');
const loading = ref(false);
const success = ref(false);

// Clear result when inputs change to avoid stale data
watch([a, b], () => {
  if (result.value !== null) {
    result.value = null;
    success.value = false;
    error.value = '';
  }
});

const credits = ref(null);

// Fetch user info (including credits)
const fetchUserInfo = async () => {
  try {
    const response = await authenticatedFetch('/users/me');
    if (response.ok) {
      const data = await response.json();
      credits.value = data.credits;
    }
  } catch (e) {
    console.error('Failed to fetch user info:', e);
  }
};

// Fetch on mount
fetchUserInfo();

const calculateSum = async () => {
  // Reset states
  error.value = '';
  success.value = false;
  result.value = null;
  
  // Validate inputs - check for NaN, null, undefined, and type
  const numA = Number(a.value);
  const numB = Number(b.value);
  
  if (isNaN(numA) || isNaN(numB)) {
    error.value = 'Please enter valid numbers';
    return;
  }
  
  if (!Number.isInteger(numA) || !Number.isInteger(numB)) {
    error.value = 'Please enter whole numbers (integers)';
    return;
  }
  
  if (numA < 0 || numA > 1023 || numB < 0 || numB > 1023) {
    error.value = 'Both numbers must be between 0 and 1023';
    return;
  }
  
  // Check authentication before making request
  if (!isAuthenticated()) {
    error.value = 'Session expired. Please login again.';
    setTimeout(() => {
      router.push('/login');
    }, 2000);
    return;
  }
  
  loading.value = true;
  
  try {
    const response = await authenticatedFetch('/api/sum', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ a: a.value, b: b.value }),
    });

    if (!response.ok) {
      let errorMessage = `Server error: ${response.status}`;
      try {
        const data = await response.json();
        // Handle Pydantic validation errors (detail is an array)
        if (Array.isArray(data.detail)) {
          const errors = data.detail.map(err => err.msg || err.message || JSON.stringify(err)).join(', ');
          errorMessage = errors;
        } else if (typeof data.detail === 'string') {
          errorMessage = data.detail;
        } else if (data.detail) {
          errorMessage = JSON.stringify(data.detail);
        }
      } catch (jsonError) {
        // Response wasn't JSON, use status text
        errorMessage = response.statusText || errorMessage;
      }
      throw new Error(errorMessage);
    }

    const data = await response.json();
    result.value = data.result;
    success.value = true;
    
    // Refresh credits after successful calculation
    await fetchUserInfo();
    
  } catch (e) {
    if (e.message === 'TOKEN_EXPIRED') {
      error.value = 'Session expired. Please login again.';
      setTimeout(() => {
        router.push('/login');
      }, 2000);
    } else if (e.message.includes('Failed to fetch')) {
      error.value = 'Cannot connect to server. Please check if the backend is running.';
    } else {
      error.value = e.message;
    }
    result.value = null;
  } finally {
    loading.value = false;
  }
};
</script>

<template>
  <div class="bg-white p-8 rounded-lg shadow-md mb-4">
    <h2 class="text-2xl font-semibold mb-4 text-gray-800">Sum Calculator</h2>
    <div class="flex justify-between items-center mb-4">
      <p class="text-gray-600 m-0">Calculate the sum of two integers (0-1023)</p>
      <div v-if="credits !== null" class="bg-indigo-100 text-indigo-800 px-3 py-1 rounded-full font-medium text-sm">
        Credits: {{ credits }}
      </div>
    </div>
    
    <div v-if="error" class="text-red-500 mb-4">
      <strong>Error:</strong> {{ error }}
    </div>
    
    <div v-if="success && result !== null" class="text-green-600 bg-green-100 p-3 rounded mb-4 border-l-4 border-green-600">
      <strong>Success!</strong> Calculation completed.
    </div>
    
    <div class="flex gap-4 mb-4">
      <div class="flex-1">
        <label for="input-a" class="block mb-2 font-medium text-gray-700">Number A</label>
        <input 
          id="input-a"
          v-model.number="a" 
          type="number" 
          placeholder="0-1023"
          min="0"
          max="1023"
          :disabled="loading"
          class="w-full p-2 border border-gray-300 rounded disabled:opacity-60 disabled:cursor-not-allowed"
        />
      </div>
      <div class="flex-1">
        <label for="input-b" class="block mb-2 font-medium text-gray-700">Number B</label>
        <input 
          id="input-b"
          v-model.number="b" 
          type="number" 
          placeholder="0-1023"
          min="0"
          max="1023"
          :disabled="loading"
          class="w-full p-2 border border-gray-300 rounded disabled:opacity-60 disabled:cursor-not-allowed"
        />
      </div>
    </div>
    
    <button 
      @click="calculateSum" 
      :disabled="loading"
      class="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded cursor-pointer border-none w-full disabled:opacity-60 disabled:cursor-not-allowed"
    >
      {{ loading ? 'Calculating...' : 'Calculate Sum' }}
    </button>
    
    <div v-if="result !== null" class="mt-6 p-6 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-lg text-white text-center">
      <h3 class="m-0 mb-2 text-3xl">Result: {{ result }}</h3>
      <p class="m-0 opacity-90 text-lg">{{ a }} + {{ b }} = {{ result }}</p>
    </div>
  </div>
</template>
