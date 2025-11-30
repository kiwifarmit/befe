<script setup>
import { ref, onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import { authenticatedFetch, getCurrentUser, isAdmin } from '../utils/auth';

const router = useRouter();
const users = ref([]);
const loading = ref(true);
const error = ref('');
const currentPage = ref(1);
const pageSize = ref(50);
const totalUsers = ref(0);
const totalPages = ref(0);

// Edit/Create modal state
const showModal = ref(false);
const editingUser = ref(null);
const modalLoading = ref(false);
const modalError = ref('');
const modalSuccess = ref('');

// Form fields
const formEmail = ref('');
const formPassword = ref('');
const formIsActive = ref(true);
const formIsSuperuser = ref(false);
const formCredits = ref(10);

// Delete confirmation
const showDeleteModal = ref(false);
const deletingUser = ref(null);
const deleteLoading = ref(false);

// Check admin access
const checkAdminAccess = async () => {
  const admin = await isAdmin();
  if (!admin) {
    router.push('/profile');
  }
};

// Fetch users list
const fetchUsers = async (page = 1) => {
  try {
    loading.value = true;
    error.value = '';
    const response = await authenticatedFetch(`/users?page=${page}&size=${pageSize.value}`);
    
    if (!response.ok) {
      if (response.status === 403) {
        error.value = 'Access denied. Admin privileges required.';
        router.push('/profile');
        return;
      }
      let errorMessage = 'Failed to fetch users';
      try {
        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
          const data = await response.json();
          errorMessage = data.detail || errorMessage;
        } else {
          const text = await response.text();
          errorMessage = `Server error (${response.status}): ${text.substring(0, 100)}`;
        }
      } catch (e) {
        errorMessage = `Server error (${response.status}): ${response.statusText}`;
      }
      throw new Error(errorMessage);
    }
    
    const data = await response.json();
    users.value = data.items || [];
    totalUsers.value = data.total || 0;
    totalPages.value = data.pages || 0;
    currentPage.value = data.page || 1;
  } catch (e) {
    if (e.message === 'TOKEN_EXPIRED') {
      router.push('/login');
    } else {
      error.value = e.message || 'Failed to fetch users';
    }
  } finally {
    loading.value = false;
  }
};

// Open create modal
const openCreateModal = () => {
  editingUser.value = null;
  formEmail.value = '';
  formPassword.value = '';
  formIsActive.value = true;
  formIsSuperuser.value = false;
  formCredits.value = 10;
  modalError.value = '';
  modalSuccess.value = '';
  showModal.value = true;
};

// Open edit modal
const openEditModal = (user) => {
  editingUser.value = user;
  formEmail.value = user.email;
  formPassword.value = '';
  formIsActive.value = user.is_active;
  formIsSuperuser.value = user.is_superuser;
  formCredits.value = user.credits;
  modalError.value = '';
  modalSuccess.value = '';
  showModal.value = true;
};

// Close modal
const closeModal = () => {
  showModal.value = false;
  editingUser.value = null;
};

// Save user (create or update)
const saveUser = async () => {
  modalError.value = '';
  modalSuccess.value = '';
  modalLoading.value = true;
  
  try {
    const updateData = {
      is_active: formIsActive.value,
      is_superuser: formIsSuperuser.value,
      credits: formCredits.value
    };
    
    if (formPassword.value) {
      updateData.password = formPassword.value;
    }
    
    if (editingUser.value) {
      // Update existing user
      if (formEmail.value !== editingUser.value.email) {
        updateData.email = formEmail.value;
      }
      
      const response = await authenticatedFetch(`/users/${editingUser.value.id}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(updateData),
      });
      
      if (!response.ok) {
        let errorMessage = 'Failed to update user';
        try {
          const contentType = response.headers.get('content-type');
          if (contentType && contentType.includes('application/json')) {
            const data = await response.json();
            errorMessage = data.detail || errorMessage;
          } else {
            // If response is not JSON (e.g., HTML error page), get text
            const text = await response.text();
            errorMessage = `Server error (${response.status}): ${text.substring(0, 100)}`;
          }
        } catch (e) {
          errorMessage = `Server error (${response.status}): ${response.statusText}`;
        }
        modalError.value = errorMessage;
        return;
      }
      
      modalSuccess.value = 'User updated successfully';
    } else {
      // Create new user - use register endpoint
      const response = await authenticatedFetch('/auth/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: formEmail.value,
          password: formPassword.value || 'TempPass123', // Default password if not provided
        }),
      });
      
      if (!response.ok) {
        let errorMessage = 'Failed to create user';
        try {
          const contentType = response.headers.get('content-type');
          if (contentType && contentType.includes('application/json')) {
            const data = await response.json();
            errorMessage = data.detail || errorMessage;
          } else {
            // If response is not JSON (e.g., HTML error page), get text
            const text = await response.text();
            errorMessage = `Server error (${response.status}): ${text.substring(0, 100)}`;
          }
        } catch (e) {
          errorMessage = `Server error (${response.status}): ${response.statusText}`;
        }
        modalError.value = errorMessage;
        return;
      }
      
      const newUser = await response.json();
      
      // Update the new user's admin status and credits
      const updateResponse = await authenticatedFetch(`/users/${newUser.id}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          is_active: formIsActive.value,
          is_superuser: formIsSuperuser.value,
          credits: formCredits.value
        }),
      });
      
      if (!updateResponse.ok) {
        let errorMessage = 'User created but failed to update settings';
        try {
          const contentType = updateResponse.headers.get('content-type');
          if (contentType && contentType.includes('application/json')) {
            const data = await updateResponse.json();
            errorMessage = data.detail || errorMessage;
          } else {
            const text = await updateResponse.text();
            errorMessage = `Server error (${updateResponse.status}): ${text.substring(0, 100)}`;
          }
        } catch (e) {
          errorMessage = `Server error (${updateResponse.status}): ${updateResponse.statusText}`;
        }
        modalError.value = errorMessage;
        return;
      }
      
      modalSuccess.value = 'User created successfully';
    }
    
    // Refresh users list
    await fetchUsers(currentPage.value);
    
    // Close modal after a short delay
    setTimeout(() => {
      closeModal();
    }, 1500);
  } catch (e) {
    if (e.message === 'TOKEN_EXPIRED') {
      router.push('/login');
    } else {
      modalError.value = e.message || 'Failed to save user';
    }
  } finally {
    modalLoading.value = false;
  }
};

// Open delete confirmation
const openDeleteModal = (user) => {
  deletingUser.value = user;
  showDeleteModal.value = true;
};

// Close delete modal
const closeDeleteModal = () => {
  showDeleteModal.value = false;
  deletingUser.value = null;
};

// Delete user
const deleteUser = async () => {
  if (!deletingUser.value) return;
  
  deleteLoading.value = true;
  modalError.value = '';
  
  try {
    const response = await authenticatedFetch(`/users/${deletingUser.value.id}`, {
      method: 'DELETE',
    });
    
    if (!response.ok && response.status !== 204) {
      let errorMessage = 'Failed to delete user';
      try {
        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
          const data = await response.json();
          errorMessage = data.detail || errorMessage;
        } else {
          const text = await response.text();
          errorMessage = `Server error (${response.status}): ${text.substring(0, 100)}`;
        }
      } catch (e) {
        errorMessage = `Server error (${response.status}): ${response.statusText}`;
      }
      modalError.value = errorMessage;
      return;
    }
    
    // Refresh users list
    await fetchUsers(currentPage.value);
    closeDeleteModal();
  } catch (e) {
    if (e.message === 'TOKEN_EXPIRED') {
      router.push('/login');
    } else {
      modalError.value = e.message || 'Failed to delete user';
    }
  } finally {
    deleteLoading.value = false;
  }
};

// Pagination
const goToPage = (page) => {
  if (page >= 1 && page <= totalPages.value) {
    fetchUsers(page);
  }
};

const pageNumbers = computed(() => {
  const pages = [];
  const maxVisible = 5;
  let start = Math.max(1, currentPage.value - Math.floor(maxVisible / 2));
  let end = Math.min(totalPages.value, start + maxVisible - 1);
  
  if (end - start < maxVisible - 1) {
    start = Math.max(1, end - maxVisible + 1);
  }
  
  for (let i = start; i <= end; i++) {
    pages.push(i);
  }
  
  return pages;
});

onMounted(async () => {
  await checkAdminAccess();
  await fetchUsers();
});
</script>

<template>
  <div class="bg-white p-8 rounded-lg shadow-md mb-4">
    <div class="flex justify-between items-center mb-6">
      <h2 class="text-2xl font-semibold text-gray-800">User Management</h2>
      <button 
        @click="openCreateModal"
        class="bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded cursor-pointer border-none"
      >
        Create User
      </button>
    </div>
    
    <div v-if="loading" class="text-gray-600">Loading users...</div>
    
    <div v-else-if="error" class="text-red-500 mb-4">{{ error }}</div>
    
    <div v-else>
      <!-- Users Table -->
      <div class="overflow-x-auto">
        <table class="min-w-full divide-y divide-gray-200">
          <thead class="bg-gray-50">
            <tr>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Email</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Credits</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Active</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Admin</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
            </tr>
          </thead>
          <tbody class="bg-white divide-y divide-gray-200">
            <tr v-for="user in users" :key="user.id">
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{{ user.email }}</td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{{ user.credits }}</td>
              <td class="px-6 py-4 whitespace-nowrap">
                <span v-if="user.is_active" class="text-green-600">Active</span>
                <span v-else class="text-red-600">Inactive</span>
              </td>
              <td class="px-6 py-4 whitespace-nowrap">
                <span v-if="user.is_superuser" class="text-blue-600">Yes</span>
                <span v-else class="text-gray-500">No</span>
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm font-medium">
                <button 
                  @click="openEditModal(user)"
                  class="text-blue-600 hover:text-blue-900 mr-4"
                >
                  Edit
                </button>
                <button 
                  @click="openDeleteModal(user)"
                  class="text-red-600 hover:text-red-900"
                >
                  Delete
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      
      <!-- Pagination -->
      <div v-if="totalPages > 1" class="mt-6 flex items-center justify-between">
        <div class="text-sm text-gray-700">
          Showing {{ (currentPage - 1) * pageSize + 1 }} to {{ Math.min(currentPage * pageSize, totalUsers) }} of {{ totalUsers }} users
        </div>
        <div class="flex gap-2">
          <button 
            @click="goToPage(currentPage - 1)"
            :disabled="currentPage === 1"
            class="px-3 py-2 border border-gray-300 rounded disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Previous
          </button>
          <button 
            v-for="page in pageNumbers"
            :key="page"
            @click="goToPage(page)"
            :class="[
              'px-3 py-2 border rounded',
              page === currentPage 
                ? 'bg-blue-500 text-white border-blue-500' 
                : 'border-gray-300 hover:bg-gray-50'
            ]"
          >
            {{ page }}
          </button>
          <button 
            @click="goToPage(currentPage + 1)"
            :disabled="currentPage === totalPages"
            class="px-3 py-2 border border-gray-300 rounded disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Next
          </button>
        </div>
      </div>
    </div>
    
    <!-- Edit/Create Modal -->
    <div v-if="showModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white p-6 rounded-lg shadow-lg max-w-md w-full mx-4">
        <h3 class="text-xl font-semibold mb-4">
          {{ editingUser ? 'Edit User' : 'Create User' }}
        </h3>
        
        <div v-if="modalError" class="text-red-500 mb-4 bg-red-50 p-3 rounded">
          {{ modalError }}
        </div>
        
        <div v-if="modalSuccess" class="text-green-600 mb-4 bg-green-50 p-3 rounded">
          {{ modalSuccess }}
        </div>
        
        <form @submit.prevent="saveUser" class="space-y-4">
          <div>
            <label class="block mb-2 font-medium text-gray-700">Email</label>
            <input 
              v-model="formEmail" 
              type="email" 
              required
              :disabled="!!editingUser"
              class="w-full p-2 border border-gray-300 rounded disabled:bg-gray-100"
            />
          </div>
          
          <div>
            <label class="block mb-2 font-medium text-gray-700">
              Password {{ editingUser ? '(leave empty to keep current)' : '' }}
            </label>
            <input 
              v-model="formPassword" 
              type="password" 
              :required="!editingUser"
              minlength="8"
              class="w-full p-2 border border-gray-300 rounded"
            />
          </div>
          
          <div>
            <label class="block mb-2 font-medium text-gray-700">Credits</label>
            <input 
              v-model.number="formCredits" 
              type="number" 
              min="0"
              required
              class="w-full p-2 border border-gray-300 rounded"
            />
          </div>
          
          <div class="flex items-center">
            <input 
              v-model="formIsActive" 
              type="checkbox" 
              id="is-active"
              class="mr-2"
            />
            <label for="is-active" class="text-gray-700">Active</label>
          </div>
          
          <div class="flex items-center">
            <input 
              v-model="formIsSuperuser" 
              type="checkbox" 
              id="is-superuser"
              class="mr-2"
            />
            <label for="is-superuser" class="text-gray-700">Admin (Superuser)</label>
          </div>
          
          <div class="flex gap-3 mt-6">
            <button 
              type="submit"
              :disabled="modalLoading"
              class="flex-1 bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded disabled:opacity-60"
            >
              {{ modalLoading ? 'Saving...' : (editingUser ? 'Update' : 'Create') }}
            </button>
            <button 
              type="button"
              @click="closeModal"
              class="flex-1 bg-gray-300 hover:bg-gray-400 text-gray-800 px-4 py-2 rounded"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
    
    <!-- Delete Confirmation Modal -->
    <div v-if="showDeleteModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white p-6 rounded-lg shadow-lg max-w-md w-full mx-4">
        <h3 class="text-xl font-semibold mb-4 text-red-600">Delete User</h3>
        
        <p class="mb-4">
          Are you sure you want to delete user <strong>{{ deletingUser?.email }}</strong>? 
          This action cannot be undone.
        </p>
        
        <div v-if="modalError" class="text-red-500 mb-4 bg-red-50 p-3 rounded">
          {{ modalError }}
        </div>
        
        <div class="flex gap-3">
          <button 
            @click="deleteUser"
            :disabled="deleteLoading"
            class="flex-1 bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded disabled:opacity-60"
          >
            {{ deleteLoading ? 'Deleting...' : 'Delete' }}
          </button>
          <button 
            @click="closeDeleteModal"
            class="flex-1 bg-gray-300 hover:bg-gray-400 text-gray-800 px-4 py-2 rounded"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

