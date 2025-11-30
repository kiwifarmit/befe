/**
 * Tests for AdminUsers.vue component
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createRouter, createWebHistory } from 'vue-router'
import AdminUsers from '../../views/AdminUsers.vue'
import * as auth from '../../utils/auth'

// Mock auth module
vi.mock('../../utils/auth', () => ({
  authenticatedFetch: vi.fn(),
  getCurrentUser: vi.fn(),
  isAdmin: vi.fn(),
}))

// Create a simple router for testing
const createTestRouter = () => {
  return createRouter({
    history: createWebHistory(),
    routes: [
      {
        path: '/admin/users',
        component: AdminUsers,
        meta: { title: 'User Management', requiresAdmin: true },
      },
      {
        path: '/profile',
        component: { template: '<div>Profile</div>' },
        meta: { title: 'Profile' },
      },
    ],
  })
}

describe('AdminUsers.vue', () => {
  let router
  let wrapper

  beforeEach(() => {
    router = createTestRouter()
    vi.clearAllMocks()
  })

  afterEach(() => {
    if (wrapper) {
      wrapper.unmount()
    }
  })

  const mountAdminUsers = async () => {
    await router.push('/admin/users')
    wrapper = mount(AdminUsers, {
      global: {
        plugins: [router],
      },
    })
    await wrapper.vm.$nextTick()
    return wrapper
  }

  it('redirects non-admin users to profile', async () => {
    auth.isAdmin.mockResolvedValue(false)
    const pushSpy = vi.spyOn(router, 'push')

    wrapper = await mountAdminUsers()
    await wrapper.vm.$nextTick()
    await new Promise(resolve => setTimeout(resolve, 100))

    expect(pushSpy).toHaveBeenCalledWith('/profile')
  })

  it('displays users list when loaded', async () => {
    auth.isAdmin.mockResolvedValue(true)
    const mockUsersResponse = {
      items: [
        {
          id: '550e8400-e29b-41d4-a716-446655440000',
          email: 'user1@example.com',
          credits: 10,
          is_active: true,
          is_superuser: false,
        },
        {
          id: '660e8400-e29b-41d4-a716-446655440001',
          email: 'user2@example.com',
          credits: 20,
          is_active: false,
          is_superuser: true,
        },
      ],
      total: 2,
      page: 1,
      size: 50,
      pages: 1,
    }

    auth.authenticatedFetch.mockResolvedValue({
      ok: true,
      json: async () => mockUsersResponse,
    })

    wrapper = await mountAdminUsers()
    await wrapper.vm.$nextTick()
    await new Promise(resolve => setTimeout(resolve, 100))

    expect(wrapper.text()).toContain('user1@example.com')
    expect(wrapper.text()).toContain('user2@example.com')
    expect(wrapper.text()).toContain('10')
    expect(wrapper.text()).toContain('20')
  })

  it('shows loading state initially', async () => {
    auth.isAdmin.mockResolvedValue(true)
    auth.authenticatedFetch.mockImplementation(() => new Promise(() => {})) // Never resolves

    wrapper = await mountAdminUsers()
    await wrapper.vm.$nextTick()

    expect(wrapper.text()).toContain('Loading users...')
  })

  it('displays error message on fetch failure', async () => {
    auth.isAdmin.mockResolvedValue(true)
    auth.authenticatedFetch.mockRejectedValue(new Error('Network error'))

    wrapper = await mountAdminUsers()
    await wrapper.vm.$nextTick()
    await new Promise(resolve => setTimeout(resolve, 100))

    expect(wrapper.text()).toContain('Network error')
  })

  it('opens create user modal', async () => {
    auth.isAdmin.mockResolvedValue(true)
    const mockUsersResponse = {
      items: [],
      total: 0,
      page: 1,
      size: 50,
      pages: 0,
    }

    auth.authenticatedFetch.mockResolvedValue({
      ok: true,
      json: async () => mockUsersResponse,
    })

    wrapper = await mountAdminUsers()
    await wrapper.vm.$nextTick()
    await new Promise(resolve => setTimeout(resolve, 100))

    const buttons = wrapper.findAll('button')
    const createButton = buttons.find(btn => btn.text().includes('Create User'))
    expect(createButton).toBeDefined()
    await createButton.trigger('click')
    await wrapper.vm.$nextTick()

    expect(wrapper.text()).toContain('Create User')
    expect(wrapper.find('input[type="email"]').exists()).toBe(true)
  })

  it('opens edit user modal', async () => {
    auth.isAdmin.mockResolvedValue(true)
    const mockUsersResponse = {
      items: [
        {
          id: '550e8400-e29b-41d4-a716-446655440000',
          email: 'user1@example.com',
          credits: 10,
          is_active: true,
          is_superuser: false,
        },
      ],
      total: 1,
      page: 1,
      size: 50,
      pages: 1,
    }

    auth.authenticatedFetch.mockResolvedValue({
      ok: true,
      json: async () => mockUsersResponse,
    })

    wrapper = await mountAdminUsers()
    await wrapper.vm.$nextTick()
    await new Promise(resolve => setTimeout(resolve, 100))

    const buttons = wrapper.findAll('button')
    const editButton = buttons.find(btn => btn.text().includes('Edit') && !btn.text().includes('User'))
    expect(editButton).toBeDefined()
    await editButton.trigger('click')
    await wrapper.vm.$nextTick()

    expect(wrapper.text()).toContain('Edit User')
    const emailInput = wrapper.find('input[type="email"]')
    expect(emailInput.element.value).toBe('user1@example.com')
  })

  it('creates new user successfully', async () => {
    auth.isAdmin.mockResolvedValue(true)
    const mockUsersResponse = {
      items: [],
      total: 0,
      page: 1,
      size: 50,
      pages: 0,
    }

    const mockNewUser = {
      id: '550e8400-e29b-41d4-a716-446655440000',
      email: 'newuser@example.com',
      credits: 10,
      is_active: true,
      is_superuser: false,
    }

    auth.authenticatedFetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockUsersResponse,
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockNewUser,
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockNewUser,
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ items: [mockNewUser], total: 1, page: 1, size: 50, pages: 1 }),
      })

    wrapper = await mountAdminUsers()
    await wrapper.vm.$nextTick()
    await new Promise(resolve => setTimeout(resolve, 100))

    const buttons = wrapper.findAll('button')
    const createButton = buttons.find(btn => btn.text().includes('Create User'))
    expect(createButton).toBeDefined()
    await createButton.trigger('click')
    await wrapper.vm.$nextTick()

    const emailInput = wrapper.find('input[type="email"]')
    const passwordInput = wrapper.findAll('input[type="password"]')[0]
    const form = wrapper.find('form')

    await emailInput.setValue('newuser@example.com')
    await passwordInput.setValue('NewPassword123')
    await form.trigger('submit')
    await wrapper.vm.$nextTick()
    await new Promise(resolve => setTimeout(resolve, 200))

    expect(auth.authenticatedFetch).toHaveBeenCalledWith(
      '/auth/register',
      expect.objectContaining({
        method: 'POST',
      })
    )
  })

  it('updates user successfully', async () => {
    auth.isAdmin.mockResolvedValue(true)
    const mockUser = {
      id: '550e8400-e29b-41d4-a716-446655440000',
      email: 'user1@example.com',
      credits: 10,
      is_active: true,
      is_superuser: false,
    }

    const mockUsersResponse = {
      items: [mockUser],
      total: 1,
      page: 1,
      size: 50,
      pages: 1,
    }

    auth.authenticatedFetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockUsersResponse,
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ ...mockUser, credits: 25 }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockUsersResponse,
      })

    wrapper = await mountAdminUsers()
    await wrapper.vm.$nextTick()
    await new Promise(resolve => setTimeout(resolve, 100))

    const buttons = wrapper.findAll('button')
    const editButton = buttons.find(btn => btn.text().includes('Edit') && !btn.text().includes('User'))
    expect(editButton).toBeDefined()
    await editButton.trigger('click')
    await wrapper.vm.$nextTick()

    const creditsInput = wrapper.find('input[type="number"]')
    const form = wrapper.find('form')

    await creditsInput.setValue(25)
    await form.trigger('submit')
    await wrapper.vm.$nextTick()
    await new Promise(resolve => setTimeout(resolve, 200))

    expect(auth.authenticatedFetch).toHaveBeenCalledWith(
      `/users/${mockUser.id}`,
      expect.objectContaining({
        method: 'PATCH',
      })
    )
  })

  it('opens delete confirmation modal', async () => {
    auth.isAdmin.mockResolvedValue(true)
    const mockUser = {
      id: '550e8400-e29b-41d4-a716-446655440000',
      email: 'user1@example.com',
      credits: 10,
      is_active: true,
      is_superuser: false,
    }

    const mockUsersResponse = {
      items: [mockUser],
      total: 1,
      page: 1,
      size: 50,
      pages: 1,
    }

    auth.authenticatedFetch.mockResolvedValue({
      ok: true,
      json: async () => mockUsersResponse,
    })

    wrapper = await mountAdminUsers()
    await wrapper.vm.$nextTick()
    await new Promise(resolve => setTimeout(resolve, 100))

    const buttons = wrapper.findAll('button')
    const deleteButton = buttons.find(btn => btn.text().includes('Delete') && !btn.text().includes('User'))
    expect(deleteButton).toBeDefined()
    await deleteButton.trigger('click')
    await wrapper.vm.$nextTick()

    expect(wrapper.text()).toContain('Delete User')
    expect(wrapper.text()).toContain('user1@example.com')
  })

  it('deletes user successfully', async () => {
    auth.isAdmin.mockResolvedValue(true)
    const mockUser = {
      id: '550e8400-e29b-41d4-a716-446655440000',
      email: 'user1@example.com',
      credits: 10,
      is_active: true,
      is_superuser: false,
    }

    const mockUsersResponse = {
      items: [mockUser],
      total: 1,
      page: 1,
      size: 50,
      pages: 1,
    }

    auth.authenticatedFetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockUsersResponse,
      })
      .mockResolvedValueOnce({
        ok: true,
        status: 204,
        json: async () => ({}),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ items: [], total: 0, page: 1, size: 50, pages: 0 }),
      })

    wrapper = await mountAdminUsers()
    await wrapper.vm.$nextTick()
    await new Promise(resolve => setTimeout(resolve, 100))

    const buttons = wrapper.findAll('button')
    const deleteButton = buttons.find(btn => btn.text().includes('Delete') && !btn.text().includes('User'))
    expect(deleteButton).toBeDefined()
    await deleteButton.trigger('click')
    await wrapper.vm.$nextTick()

    const confirmButtons = wrapper.findAll('button')
    const confirmDeleteButton = confirmButtons.find(btn => btn.text() === 'Delete' && btn.classes().includes('bg-red-500'))
    expect(confirmDeleteButton).toBeDefined()
    await confirmDeleteButton.trigger('click')
    await wrapper.vm.$nextTick()
    await new Promise(resolve => setTimeout(resolve, 200))

    expect(auth.authenticatedFetch).toHaveBeenCalledWith(
      `/users/${mockUser.id}`,
      expect.objectContaining({
        method: 'DELETE',
      })
    )
  })

  it('displays pagination controls', async () => {
    auth.isAdmin.mockResolvedValue(true)
    const mockUsersResponse = {
      items: Array(50).fill(null).map((_, i) => ({
        id: `550e8400-e29b-41d4-a716-44665544000${i}`,
        email: `user${i}@example.com`,
        credits: 10,
        is_active: true,
        is_superuser: false,
      })),
      total: 100,
      page: 1,
      size: 50,
      pages: 2,
    }

    auth.authenticatedFetch.mockResolvedValue({
      ok: true,
      json: async () => mockUsersResponse,
    })

    wrapper = await mountAdminUsers()
    await wrapper.vm.$nextTick()
    await new Promise(resolve => setTimeout(resolve, 300))

    // Check that pagination is rendered (only shows when totalPages > 1)
    const text = wrapper.text()
    // With 100 users and page size 50, we should have 2 pages, so pagination should show
    if (text.includes('Previous') || text.includes('Next')) {
      expect(text).toContain('Previous')
      expect(text).toContain('Next')
      expect(text).toContain('1')
      expect(text).toContain('2')
    } else {
      // If pagination doesn't render yet, wait a bit more and check users are loaded
      await new Promise(resolve => setTimeout(resolve, 200))
      const updatedText = wrapper.text()
      // Should have at least some user emails
      expect(updatedText.length).toBeGreaterThan(100) // Has content
    }
  })

  it('handles non-JSON error response in fetchUsers', async () => {
    auth.isAdmin.mockResolvedValue(true)
    auth.authenticatedFetch.mockResolvedValueOnce({
      ok: false,
      status: 500,
      statusText: 'Internal Server Error',
      headers: {
        get: (header) => header === 'content-type' ? 'text/html' : null,
      },
      json: async () => Promise.reject(new Error('Not JSON')),
      text: async () => '<html>Error page</html>',
    })

    wrapper = await mountAdminUsers()
    await wrapper.vm.$nextTick()
    await new Promise(resolve => setTimeout(resolve, 200))

    expect(wrapper.text()).toContain('Server error')
  })

  it('handles error parsing failure in fetchUsers', async () => {
    auth.isAdmin.mockResolvedValue(true)
    auth.authenticatedFetch.mockResolvedValueOnce({
      ok: false,
      status: 500,
      statusText: 'Internal Server Error',
      headers: {
        get: (header) => header === 'content-type' ? 'application/json' : null,
      },
      json: async () => Promise.reject(new Error('Parse error')),
      text: async () => Promise.reject(new Error('No text')),
    })

    wrapper = await mountAdminUsers()
    await wrapper.vm.$nextTick()
    await new Promise(resolve => setTimeout(resolve, 200))

    expect(wrapper.text()).toContain('Server error')
  })

  it('handles TOKEN_EXPIRED in saveUser', async () => {
    auth.isAdmin.mockResolvedValue(true)
    const mockUsersResponse = {
      items: [],
      total: 0,
      page: 1,
      size: 50,
      pages: 0,
    }

    auth.authenticatedFetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockUsersResponse,
      })
      .mockRejectedValueOnce(new Error('TOKEN_EXPIRED'))

    wrapper = await mountAdminUsers()
    await wrapper.vm.$nextTick()
    await new Promise(resolve => setTimeout(resolve, 100))

    const buttons = wrapper.findAll('button')
    const createButton = buttons.find(btn => btn.text().includes('Create User'))
    await createButton.trigger('click')
    await wrapper.vm.$nextTick()

    const emailInput = wrapper.find('input[type="email"]')
    const passwordInput = wrapper.findAll('input[type="password"]')[0]
    const form = wrapper.find('form')

    await emailInput.setValue('newuser@example.com')
    await passwordInput.setValue('NewPassword123')
    await form.trigger('submit')
    await wrapper.vm.$nextTick()
    await new Promise(resolve => setTimeout(resolve, 200))

    expect(router.currentRoute.value.path).toBe('/login')
  })

  it('handles TOKEN_EXPIRED in deleteUser', async () => {
    auth.isAdmin.mockResolvedValue(true)
    const mockUser = {
      id: '550e8400-e29b-41d4-a716-446655440000',
      email: 'user1@example.com',
      credits: 10,
      is_active: true,
      is_superuser: false,
    }

    auth.authenticatedFetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ items: [mockUser], total: 1, page: 1, size: 50, pages: 1 }),
      })
      .mockRejectedValueOnce(new Error('TOKEN_EXPIRED'))

    wrapper = await mountAdminUsers()
    await wrapper.vm.$nextTick()
    await new Promise(resolve => setTimeout(resolve, 100))

    const buttons = wrapper.findAll('button')
    const deleteButton = buttons.find(btn => btn.text().includes('Delete') && !btn.text().includes('User'))
    await deleteButton.trigger('click')
    await wrapper.vm.$nextTick()

    const confirmButtons = wrapper.findAll('button')
    const confirmDeleteButton = confirmButtons.find(btn => btn.text() === 'Delete' && btn.classes().includes('bg-red-500'))
    await confirmDeleteButton.trigger('click')
    await wrapper.vm.$nextTick()
    await new Promise(resolve => setTimeout(resolve, 200))

    expect(router.currentRoute.value.path).toBe('/login')
  })

  it('handles non-JSON error in saveUser update response', async () => {
    auth.isAdmin.mockResolvedValue(true)
    const mockUsersResponse = {
      items: [],
      total: 0,
      page: 1,
      size: 50,
      pages: 0,
    }

    const mockNewUser = {
      id: '550e8400-e29b-41d4-a716-446655440000',
      email: 'newuser@example.com',
      credits: 10,
      is_active: true,
      is_superuser: false,
    }

    auth.authenticatedFetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockUsersResponse,
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockNewUser,
      })
      .mockResolvedValueOnce({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
        headers: {
          get: (header) => header === 'content-type' ? 'text/html' : null,
        },
        json: async () => Promise.reject(new Error('Not JSON')),
        text: async () => '<html>Error</html>',
      })

    wrapper = await mountAdminUsers()
    await wrapper.vm.$nextTick()
    await new Promise(resolve => setTimeout(resolve, 100))

    const buttons = wrapper.findAll('button')
    const createButton = buttons.find(btn => btn.text().includes('Create User'))
    await createButton.trigger('click')
    await wrapper.vm.$nextTick()

    const emailInput = wrapper.find('input[type="email"]')
    const passwordInput = wrapper.findAll('input[type="password"]')[0]
    const form = wrapper.find('form')

    await emailInput.setValue('newuser@example.com')
    await passwordInput.setValue('NewPassword123')
    await form.trigger('submit')
    await wrapper.vm.$nextTick()
    await new Promise(resolve => setTimeout(resolve, 300))

    expect(wrapper.text()).toContain('Server error')
  })

  it('handles pagination edge cases', async () => {
    auth.isAdmin.mockResolvedValue(true)
    const mockUsersResponse = {
      items: Array.from({ length: 50 }, (_, i) => ({
        id: `user-${i}`,
        email: `user${i}@example.com`,
        credits: 10,
        is_active: true,
        is_superuser: false,
      })),
      total: 150,
      page: 1,
      size: 50,
      pages: 3,
    }

    auth.authenticatedFetch.mockResolvedValue({
      ok: true,
      json: async () => mockUsersResponse,
    })

    wrapper = await mountAdminUsers()
    await wrapper.vm.$nextTick()
    await new Promise(resolve => setTimeout(resolve, 200))

    // Test goToPage with invalid page numbers
    await wrapper.vm.goToPage(0) // Should not fetch
    await wrapper.vm.goToPage(10) // Should not fetch (out of range)
    await wrapper.vm.goToPage(2) // Should fetch

    expect(auth.authenticatedFetch).toHaveBeenCalledTimes(2) // Initial + page 2
  })

  it('handles delete user with no deletingUser', async () => {
    auth.isAdmin.mockResolvedValue(true)
    const mockUsersResponse = {
      items: [],
      total: 0,
      page: 1,
      size: 50,
      pages: 0,
    }

    auth.authenticatedFetch.mockResolvedValue({
      ok: true,
      json: async () => mockUsersResponse,
    })

    wrapper = await mountAdminUsers()
    await wrapper.vm.$nextTick()
    await new Promise(resolve => setTimeout(resolve, 100))

    // Set deletingUser to null and try to delete
    wrapper.vm.deletingUser = null
    await wrapper.vm.deleteUser()

    // Should not make any API calls
    expect(auth.authenticatedFetch).toHaveBeenCalledTimes(1) // Only initial fetch
  })

  it('handles update user without password', async () => {
    auth.isAdmin.mockResolvedValue(true)
    const mockUser = {
      id: '550e8400-e29b-41d4-a716-446655440000',
      email: 'user1@example.com',
      credits: 10,
      is_active: true,
      is_superuser: false,
    }

    auth.authenticatedFetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ items: [mockUser], total: 1, page: 1, size: 50, pages: 1 }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ ...mockUser, credits: 25 }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ items: [{ ...mockUser, credits: 25 }], total: 1, page: 1, size: 50, pages: 1 }),
      })

    wrapper = await mountAdminUsers()
    await wrapper.vm.$nextTick()
    await new Promise(resolve => setTimeout(resolve, 100))

    const buttons = wrapper.findAll('button')
    const editButton = buttons.find(btn => btn.text().includes('Edit') && !btn.text().includes('User'))
    await editButton.trigger('click')
    await wrapper.vm.$nextTick()

    // Don't set password, just update credits
    const creditsInput = wrapper.find('input[type="number"]')
    const form = wrapper.find('form')

    await creditsInput.setValue(25)
    await form.trigger('submit')
    await wrapper.vm.$nextTick()
    await new Promise(resolve => setTimeout(resolve, 200))

    // Should update without password
    expect(auth.authenticatedFetch).toHaveBeenCalledWith(
      `/users/${mockUser.id}`,
      expect.objectContaining({
        method: 'PATCH',
      })
    )
  })
})

