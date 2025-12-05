<script setup>
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import { authenticatedFetch, getCurrentUser } from "../utils/auth";

const router = useRouter();
const users = ref([]);
const loading = ref(true);
const error = ref("");
const success = ref("");
const editingUser = ref(null);
const creatingUser = ref(false);
const isAdmin = ref(false);
const editForm = ref({
  email: "",
  is_active: false,
  is_superuser: false,
  is_verified: false,
  credits: 0,
});
const newUserForm = ref({
  email: "",
  password: "",
  is_active: true,
  is_superuser: false,
  is_verified: true,
  credits: 10,
});

const fetchUsers = async () => {
  try {
    loading.value = true;
    error.value = "";
    const response = await authenticatedFetch("/users");

    if (!response.ok) {
      // Try to parse JSON error, fallback to status text
      let errorMessage = `Failed to fetch users: ${response.status} ${response.statusText}`;
      try {
        const contentType = response.headers.get("content-type");
        if (contentType && contentType.includes("application/json")) {
          const data = await response.json();
          errorMessage = data.detail || data.message || errorMessage;
        }
      } catch (parseError) {
        // Response is not JSON, use status text
      }
      throw new Error(errorMessage);
    }

    users.value = await response.json();
  } catch (e) {
    error.value = e.message || "Failed to load users";
  } finally {
    loading.value = false;
  }
};

const startEdit = (user) => {
  editingUser.value = user.id;
  editForm.value = {
    email: user.email,
    is_active: user.is_active,
    is_superuser: user.is_superuser,
    is_verified: user.is_verified,
    credits: user.credits || 0,
  };
};

const cancelEdit = () => {
  editingUser.value = null;
};

const startCreate = () => {
  creatingUser.value = true;
  newUserForm.value = {
    email: "",
    password: "",
    is_active: true,
    is_superuser: false,
    is_verified: true,
    credits: 10,
  };
};

const cancelCreate = () => {
  creatingUser.value = false;
};

const createUser = async () => {
  try {
    error.value = "";

    // First create the user via register endpoint
    const response = await authenticatedFetch("/auth/register", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        email: newUserForm.value.email,
        password: newUserForm.value.password,
      }),
    });

    if (!response.ok) {
      // Try to parse JSON error, fallback to status text
      let errorMessage = `Failed to create user: ${response.status} ${response.statusText}`;
      try {
        const contentType = response.headers.get("content-type");
        if (contentType && contentType.includes("application/json")) {
          const data = await response.json();
          errorMessage = data.detail || data.message || errorMessage;
        }
      } catch (parseError) {
        // Response is not JSON, use status text
      }
      throw new Error(errorMessage);
    }

    const newUser = await response.json();
    const userId = newUser.id;

    // Update user properties (is_active, is_superuser, is_verified)
    await authenticatedFetch(`/users/${userId}`, {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        is_active: newUserForm.value.is_active,
        is_superuser: newUserForm.value.is_superuser,
        is_verified: newUserForm.value.is_verified,
      }),
    });

    // Set credits
    await updateCredits(userId, newUserForm.value.credits);

    creatingUser.value = false;
    await fetchUsers();
  } catch (e) {
    error.value = e.message || "Failed to create user";
  }
};

const saveUser = async (userId) => {
  try {
    error.value = "";
    const response = await authenticatedFetch(`/users/${userId}`, {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        email: editForm.value.email,
        is_active: editForm.value.is_active,
        is_superuser: editForm.value.is_superuser,
        is_verified: editForm.value.is_verified,
      }),
    });

    if (!response.ok) {
      // Try to parse JSON error, fallback to status text
      let errorMessage = `Failed to update user: ${response.status} ${response.statusText}`;
      try {
        const contentType = response.headers.get("content-type");
        if (contentType && contentType.includes("application/json")) {
          const data = await response.json();
          errorMessage = data.detail || data.message || errorMessage;
        }
      } catch (parseError) {
        // Response is not JSON, use status text
      }
      throw new Error(errorMessage);
    }

    // Update credits separately if changed
    if (
      editForm.value.credits !==
      users.value.find((u) => u.id === userId)?.credits
    ) {
      await updateCredits(userId, editForm.value.credits);
    }

    editingUser.value = null;
    await fetchUsers();
  } catch (e) {
    error.value = e.message || "Failed to update user";
  }
};

const updateCredits = async (userId, credits) => {
  try {
    const response = await authenticatedFetch(`/api/users/${userId}/credits`, {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ credits: parseInt(credits) }),
    });

    if (!response.ok) {
      // Try to parse JSON error, fallback to status text
      let errorMessage = `Failed to update credits: ${response.status} ${response.statusText}`;
      try {
        const contentType = response.headers.get("content-type");
        if (contentType && contentType.includes("application/json")) {
          const data = await response.json();
          errorMessage = data.detail || data.message || errorMessage;
        }
      } catch (parseError) {
        // Response is not JSON, use status text
      }
      throw new Error(errorMessage);
    }
  } catch (e) {
    throw new Error("Failed to update credits: " + e.message);
  }
};

const deleteUser = async (userId) => {
  if (!confirm("Are you sure you want to delete this user?")) {
    return;
  }

  try {
    error.value = "";
    success.value = "";
    const response = await authenticatedFetch(`/users/${userId}`, {
      method: "DELETE",
    });

    if (!response.ok) {
      // Try to parse JSON error, fallback to status text
      let errorMessage = `Failed to delete user: ${response.status} ${response.statusText}`;
      try {
        const contentType = response.headers.get("content-type");
        if (contentType && contentType.includes("application/json")) {
          const data = await response.json();
          errorMessage = data.detail || data.message || errorMessage;
        }
      } catch (parseError) {
        // Response is not JSON, use status text
      }
      throw new Error(errorMessage);
    }

    // Show success message
    const deletedUser = users.value.find((u) => u.id === userId);
    success.value = `User ${deletedUser?.email || "deleted"} has been successfully deleted.`;

    // Refresh the user list
    await fetchUsers();

    // Clear success message after 3 seconds
    setTimeout(() => {
      success.value = "";
    }, 3000);
  } catch (e) {
    error.value = e.message || "Failed to delete user";
    success.value = "";
  }
};

const checkAdminStatus = async () => {
  try {
    loading.value = true;
    const user = await getCurrentUser();
    isAdmin.value = user ? user.is_superuser === true : false;

    // If not admin, show error and don't fetch users
    if (!isAdmin.value) {
      error.value = "Access Denied: Only administrators can access this page.";
      loading.value = false;
      // Redirect after a short delay to show the message
      setTimeout(() => {
        router.push("/profile");
      }, 2000);
      return;
    }

    // Only fetch users if admin
    await fetchUsers();
  } catch (e) {
    error.value =
      "Failed to verify admin status: " + (e.message || "Unknown error");
    isAdmin.value = false;
    loading.value = false;
  }
};

onMounted(() => {
  checkAdminStatus();
});
</script>

<template>
  <div v-if="isAdmin" class="bg-white p-8 rounded-lg shadow-md mb-4">
    <div class="flex justify-between items-center mb-4">
      <h2 class="text-2xl font-semibold text-gray-800">User Management</h2>
      <button
        v-if="isAdmin && !creatingUser"
        class="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded cursor-pointer border-none"
        @click="startCreate"
      >
        New User
      </button>
    </div>

    <div
      v-if="error"
      class="text-red-500 mb-4 p-3 bg-red-50 border border-red-200 rounded"
    >
      <strong>Error:</strong> {{ error }}
    </div>
    <div
      v-if="success"
      class="text-green-600 mb-4 p-3 bg-green-50 border border-green-200 rounded"
    >
      <strong>Success:</strong> {{ success }}
    </div>

    <!-- New User Form -->
    <div
      v-if="isAdmin && creatingUser"
      class="mb-6 p-4 border-2 border-blue-300 rounded-lg bg-blue-50"
    >
      <h3 class="text-lg font-semibold mb-4 text-gray-800">Create New User</h3>
      <div class="grid grid-cols-2 gap-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1"
            >Email *</label
          >
          <input
            v-model="newUserForm.email"
            type="email"
            required
            class="w-full px-2 py-1 border border-gray-300 rounded text-sm"
            placeholder="user@example.com"
          />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1"
            >Password *</label
          >
          <input
            v-model="newUserForm.password"
            type="password"
            required
            class="w-full px-2 py-1 border border-gray-300 rounded text-sm"
            placeholder="Password"
          />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1"
            >Initial Credits</label
          >
          <input
            v-model.number="newUserForm.credits"
            type="number"
            min="0"
            class="w-full px-2 py-1 border border-gray-300 rounded text-sm"
          />
        </div>
        <div class="space-y-2">
          <label class="flex items-center text-sm">
            <input
              v-model="newUserForm.is_active"
              type="checkbox"
              class="mr-2"
            />
            Active
          </label>
          <label class="flex items-center text-sm">
            <input
              v-model="newUserForm.is_verified"
              type="checkbox"
              class="mr-2"
            />
            Verified
          </label>
          <label class="flex items-center text-sm">
            <input
              v-model="newUserForm.is_superuser"
              type="checkbox"
              class="mr-2"
            />
            Superuser
          </label>
        </div>
      </div>
      <div class="flex gap-2 mt-4">
        <button
          class="bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded cursor-pointer border-none"
          @click="createUser"
        >
          Create User
        </button>
        <button
          class="bg-gray-500 hover:bg-gray-600 text-white px-4 py-2 rounded cursor-pointer border-none"
          @click="cancelCreate"
        >
          Cancel
        </button>
      </div>
    </div>

    <div v-if="!isAdmin" class="text-red-500 mb-4">
      <strong>Access Denied:</strong> Only administrators can access this page.
    </div>

    <div v-if="isAdmin && loading" class="text-gray-600">Loading users...</div>

    <div v-if="isAdmin && !loading && users.length === 0" class="text-gray-600">
      No users found.
    </div>

    <div v-if="!loading && isAdmin && users.length > 0" class="overflow-x-auto">
      <table class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-50">
          <tr>
            <th
              class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
            >
              Email
            </th>
            <th
              class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
            >
              Credits
            </th>
            <th
              class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
            >
              Status
            </th>
            <th
              class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
            >
              Actions
            </th>
          </tr>
        </thead>
        <tbody class="bg-white divide-y divide-gray-200">
          <tr v-for="user in users" :key="user.id">
            <td class="px-6 py-4 whitespace-nowrap">
              <div
                v-if="editingUser !== user.id"
                class="text-sm font-medium text-gray-900"
              >
                {{ user.email }}
              </div>
              <input
                v-else
                v-model="editForm.email"
                type="email"
                class="w-full px-2 py-1 border border-gray-300 rounded text-sm"
              />
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
              <div
                v-if="editingUser !== user.id"
                class="text-sm text-gray-900 font-semibold"
              >
                {{ user.credits || 0 }}
              </div>
              <input
                v-else
                v-model.number="editForm.credits"
                type="number"
                min="0"
                class="w-full px-2 py-1 border border-gray-300 rounded text-sm"
              />
            </td>
            <td class="px-6 py-4 whitespace-nowrap">
              <div v-if="editingUser !== user.id" class="text-sm text-gray-900">
                <span
                  :class="user.is_active ? 'text-green-600' : 'text-red-600'"
                  class="font-medium mr-2"
                >
                  {{ user.is_active ? "Active" : "Inactive" }}
                </span>
                <span
                  :class="
                    user.is_verified ? 'text-green-600' : 'text-yellow-600'
                  "
                  class="font-medium mr-2"
                >
                  {{ user.is_verified ? "Verified" : "Not Verified" }}
                </span>
                <span
                  v-if="user.is_superuser"
                  class="text-purple-600 font-medium"
                  >Superuser</span
                >
              </div>
              <div v-else class="space-y-2">
                <label class="flex items-center text-sm">
                  <input
                    v-model="editForm.is_active"
                    type="checkbox"
                    class="mr-2"
                  />
                  Active
                </label>
                <label class="flex items-center text-sm">
                  <input
                    v-model="editForm.is_verified"
                    type="checkbox"
                    class="mr-2"
                  />
                  Verified
                </label>
                <label class="flex items-center text-sm">
                  <input
                    v-model="editForm.is_superuser"
                    type="checkbox"
                    class="mr-2"
                  />
                  Superuser
                </label>
              </div>
            </td>
            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium">
              <div v-if="editingUser !== user.id" class="flex gap-2">
                <button
                  class="text-blue-600 hover:text-blue-900"
                  @click="startEdit(user)"
                >
                  Edit
                </button>
                <button
                  class="text-red-600 hover:text-red-900"
                  @click="deleteUser(user.id)"
                >
                  Delete
                </button>
              </div>
              <div v-else class="flex gap-2">
                <button
                  class="text-green-600 hover:text-green-900"
                  @click="saveUser(user.id)"
                >
                  Save
                </button>
                <button
                  class="text-gray-600 hover:text-gray-900"
                  @click="cancelEdit"
                >
                  Cancel
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
