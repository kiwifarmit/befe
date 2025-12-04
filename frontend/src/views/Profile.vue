<script setup>
import { ref, onMounted } from "vue";
import { authenticatedFetch } from "../utils/auth";

const user = ref(null);
const loading = ref(true);
const error = ref("");
const currentPassword = ref("");
const newPassword = ref("");
const confirmPassword = ref("");
const passwordError = ref("");
const passwordSuccess = ref("");
const updatingPassword = ref(false);

const fetchProfile = async () => {
  try {
    loading.value = true;
    error.value = "";
    const response = await authenticatedFetch("/users/me");

    if (!response.ok) {
      throw new Error("Failed to fetch profile");
    }

    user.value = await response.json();
  } catch (e) {
    error.value = e.message || "Failed to load profile";
  } finally {
    loading.value = false;
  }
};

const updatePassword = async () => {
  passwordError.value = "";
  passwordSuccess.value = "";

  // Validation
  if (!currentPassword.value) {
    passwordError.value = "Current password is required";
    return;
  }

  if (!newPassword.value) {
    passwordError.value = "New password is required";
    return;
  }

  if (newPassword.value.length < 8) {
    passwordError.value = "Password must be at least 8 characters long";
    return;
  }

  if (!/\d/.test(newPassword.value)) {
    passwordError.value = "Password must contain at least one number";
    return;
  }

  if (!/[A-Z]/.test(newPassword.value)) {
    passwordError.value = "Password must contain at least one uppercase letter";
    return;
  }

  if (!/[a-z]/.test(newPassword.value)) {
    passwordError.value = "Password must contain at least one lowercase letter";
    return;
  }

  if (newPassword.value !== confirmPassword.value) {
    passwordError.value = "Passwords do not match";
    return;
  }

  updatingPassword.value = true;

  try {
    const response = await authenticatedFetch("/users/me/password", {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        current_password: currentPassword.value,
        password: newPassword.value,
      }),
    });

    if (!response.ok) {
      let errorMessage = "Failed to update password";
      try {
        const contentType = response.headers.get("content-type");
        if (contentType && contentType.includes("application/json")) {
          const data = await response.json();
          errorMessage = data.detail || data.message || errorMessage;
        }
      } catch (parseError) {
        // Response is not JSON, use status text
        errorMessage = `${response.status} ${response.statusText}`;
      }
      passwordError.value = errorMessage;
      return;
    }

    passwordSuccess.value = "Password updated successfully";
    currentPassword.value = "";
    newPassword.value = "";
    confirmPassword.value = "";

    // Clear success message after 3 seconds
    setTimeout(() => {
      passwordSuccess.value = "";
    }, 3000);
  } catch (e) {
    passwordError.value = e.message || "Failed to update password";
  } finally {
    updatingPassword.value = false;
  }
};

onMounted(() => {
  fetchProfile();
});
</script>

<template>
  <div class="bg-white p-8 rounded-lg shadow-md mb-4">
    <h2 class="text-2xl font-semibold mb-4 text-gray-800">My Profile</h2>

    <div v-if="error" class="text-red-500 mb-4">
      <strong>Error:</strong> {{ error }}
    </div>

    <div v-if="loading" class="text-gray-600">Loading profile...</div>

    <div v-if="user && !loading" class="space-y-4">
      <div class="border-b border-gray-200 pb-4">
        <label class="block text-sm font-medium text-gray-700 mb-1"
          >Email</label
        >
        <p class="text-gray-900">{{ user.email }}</p>
      </div>

      <div class="border-b border-gray-200 pb-4">
        <label class="block text-sm font-medium text-gray-700 mb-1"
          >Credits</label
        >
        <p class="text-gray-900 text-2xl font-semibold">{{ user.credits }}</p>
      </div>

      <div class="border-b border-gray-200 pb-4">
        <label class="block text-sm font-medium text-gray-700 mb-1"
          >Status</label
        >
        <div class="flex gap-4">
          <span
            :class="user.is_active ? 'text-green-600' : 'text-red-600'"
            class="font-medium"
          >
            {{ user.is_active ? "Active" : "Inactive" }}
          </span>
          <span
            :class="user.is_verified ? 'text-green-600' : 'text-yellow-600'"
            class="font-medium"
          >
            {{ user.is_verified ? "Verified" : "Not Verified" }}
          </span>
          <span v-if="user.is_superuser" class="text-purple-600 font-medium">
            Superuser
          </span>
        </div>
      </div>

      <div>
        <label class="block text-sm font-medium text-gray-700 mb-1"
          >User ID</label
        >
        <p class="text-gray-500 text-sm font-mono">{{ user.id }}</p>
      </div>

      <!-- Password Change Section -->
      <div class="border-t border-gray-200 pt-6 mt-6">
        <h3 class="text-lg font-semibold mb-4 text-gray-800">
          Change Password
        </h3>

        <div v-if="passwordError" class="text-red-500 mb-4 text-sm">
          <strong>Error:</strong> {{ passwordError }}
        </div>

        <div v-if="passwordSuccess" class="text-green-500 mb-4 text-sm">
          <strong>Success:</strong> {{ passwordSuccess }}
        </div>

        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1"
              >Current Password</label
            >
            <input
              v-model="currentPassword"
              type="password"
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Enter current password"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1"
              >New Password</label
            >
            <input
              v-model="newPassword"
              type="password"
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Enter new password"
            />
            <p class="text-xs text-gray-500 mt-1">
              Must be at least 8 characters with uppercase, lowercase, and a
              number
            </p>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1"
              >Confirm New Password</label
            >
            <input
              v-model="confirmPassword"
              type="password"
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Confirm new password"
            />
          </div>

          <div>
            <button
              :disabled="updatingPassword"
              class="bg-blue-500 hover:bg-blue-600 disabled:bg-gray-400 text-white px-4 py-2 rounded cursor-pointer border-none"
              @click="updatePassword"
            >
              {{ updatingPassword ? "Updating..." : "Update Password" }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
