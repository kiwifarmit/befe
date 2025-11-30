<script setup>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { authenticatedFetch, getCurrentUser } from '../utils/auth';

const router = useRouter();
const user = ref(null);
const loading = ref(true);
const error = ref('');
const success = ref('');

// Password update form
const currentPassword = ref('');
const newPassword = ref('');
const confirmPassword = ref('');
const updatingPassword = ref(false);
const passwordError = ref('');
const passwordSuccess = ref('');

// Fetch user data
const fetchUser = async () => {
  try {
    loading.value = true;
    error.value = '';
    const userData = await getCurrentUser();
    if (userData) {
      user.value = userData;
    } else {
      error.value = 'Failed to load user data';
      router.push('/login');
    }
  } catch (e) {
    error.value = e.message || 'Failed to load user data';
    if (e.message === 'TOKEN_EXPIRED') {
      router.push('/login');
    }
  } finally {
    loading.value = false;
  }
};

// Update password
const updatePassword = async () => {
  passwordError.value = '';
  passwordSuccess.value = '';
  
  // Validation
  if (!newPassword.value) {
    passwordError.value = 'New password is required';
    return;
  }
  
  if (newPassword.value.length < 8) {
    passwordError.value = 'Password must be at least 8 characters long';
    return;
  }
  
  if (newPassword.value !== confirmPassword.value) {
    passwordError.value = 'Passwords do not match';
    return;
  }
  
  updatingPassword.value = true;
  
  try {
    const response = await authenticatedFetch('/users/me', {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        password: newPassword.value
      }),
    });
    
    if (!response.ok) {
      const data = await response.json();
      passwordError.value = data.detail || 'Failed to update password';
      return;
    }
    
    passwordSuccess.value = 'Password updated successfully';
    currentPassword.value = '';
    newPassword.value = '';
    confirmPassword.value = '';
    
    // Refresh user data
    await fetchUser();
  } catch (e) {
    if (e.message === 'TOKEN_EXPIRED') {
      router.push('/login');
    } else {
      passwordError.value = e.message || 'Failed to update password';
    }
  } finally {
    updatingPassword.value = false;
  }
};

onMounted(() => {
  fetchUser();
});
</script>

<template>
  <div class="bg-white p-8 rounded-lg shadow-md mb-4">
    <h2 class="text-2xl font-semibold mb-4 text-gray-800">Profile</h2>
    
    <div v-if="loading" class="text-gray-600">Loading...</div>
    
    <div v-else-if="error" class="text-red-500 mb-4">{{ error }}</div>
    
    <div v-else-if="user" class="space-y-6">
      <!-- User Information -->
      <div>
        <h3 class="text-lg font-medium text-gray-700 mb-3">User Information</h3>
        <div class="space-y-2">
          <div class="flex justify-between py-2 border-b border-gray-200">
            <span class="font-medium text-gray-600">Email:</span>
            <span class="text-gray-800">{{ user.email }}</span>
          </div>
          <div class="flex justify-between py-2 border-b border-gray-200">
            <span class="font-medium text-gray-600">Credits:</span>
            <span class="text-gray-800 font-semibold">{{ user.credits }}</span>
          </div>
          <div class="flex justify-between py-2 border-b border-gray-200">
            <span class="font-medium text-gray-600">Status:</span>
            <span class="text-gray-800">
              <span v-if="user.is_active" class="text-green-600">Active</span>
              <span v-else class="text-red-600">Inactive</span>
            </span>
          </div>
          <div class="flex justify-between py-2 border-b border-gray-200">
            <span class="font-medium text-gray-600">Verified:</span>
            <span class="text-gray-800">
              <span v-if="user.is_verified" class="text-green-600">Yes</span>
              <span v-else class="text-yellow-600">No</span>
            </span>
          </div>
        </div>
      </div>
      
      <!-- Password Update Form -->
      <div>
        <h3 class="text-lg font-medium text-gray-700 mb-3">Change Password</h3>
        
        <div v-if="passwordError" class="text-red-500 mb-4 bg-red-50 p-3 rounded">
          {{ passwordError }}
        </div>
        
        <div v-if="passwordSuccess" class="text-green-600 mb-4 bg-green-50 p-3 rounded">
          {{ passwordSuccess }}
        </div>
        
        <form @submit.prevent="updatePassword" class="space-y-4">
          <div>
            <label for="new-password" class="block mb-2 font-medium text-gray-700">New Password</label>
            <input 
              id="new-password"
              v-model="newPassword" 
              type="password" 
              placeholder="Enter new password"
              required
              minlength="8"
              class="w-full p-2 border border-gray-300 rounded"
            />
            <p class="text-sm text-gray-500 mt-1">
              Must be at least 8 characters with uppercase, lowercase, and a number
            </p>
          </div>
          
          <div>
            <label for="confirm-password" class="block mb-2 font-medium text-gray-700">Confirm Password</label>
            <input 
              id="confirm-password"
              v-model="confirmPassword" 
              type="password" 
              placeholder="Confirm new password"
              required
              minlength="8"
              class="w-full p-2 border border-gray-300 rounded"
            />
          </div>
          
          <button 
            type="submit" 
            :disabled="updatingPassword"
            class="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded cursor-pointer border-none disabled:opacity-60 disabled:cursor-not-allowed"
          >
            {{ updatingPassword ? 'Updating...' : 'Update Password' }}
          </button>
        </form>
      </div>
    </div>
  </div>
</template>

