/**
 * Tests for ResetPassword.vue component
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { mount } from "@vue/test-utils";
import { createRouter, createWebHistory } from "vue-router";
import ResetPassword from "../../views/ResetPassword.vue";

// Mock global fetch
global.fetch = vi.fn();

// Mock router
const createTestRouter = () => {
  return createRouter({
    history: createWebHistory(),
    routes: [
      {
        path: "/reset-password",
        component: ResetPassword,
      },
      { path: "/login", component: { template: "<div>Login</div>" } },
    ],
  });
};

describe("ResetPassword.vue", () => {
  let router;
  let wrapper;

  beforeEach(() => {
    vi.clearAllMocks();
  });

  const mountResetPassword = async (token = "test-token-123") => {
    router = createTestRouter();
    await router.push({
      path: "/reset-password",
      query: { token },
    });
    wrapper = mount(ResetPassword, {
      global: {
        plugins: [router],
      },
    });
    await router.isReady();
    return wrapper;
  };

  it("should render reset password form", async () => {
    wrapper = await mountResetPassword();

    expect(wrapper.find("h2").text()).toBe("Reset Password");
    expect(wrapper.find('input[type="password"]').exists()).toBe(true);
    expect(wrapper.find('button[type="submit"]').exists()).toBe(true);
  });

  it("should bind password input", async () => {
    wrapper = await mountResetPassword();

    const passwordInput = wrapper.find('input[type="password"]');
    await passwordInput.setValue("newpassword123");

    expect(wrapper.vm.password).toBe("newpassword123");
  });

  it("should extract token from route query", async () => {
    wrapper = await mountResetPassword("my-reset-token");

    expect(wrapper.vm.token).toBe("my-reset-token");
  });

  it("should submit form and redirect to login on success", async () => {
    global.fetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
    });

    wrapper = await mountResetPassword("test-token");

    await wrapper.find('input[type="password"]').setValue("newpassword123");
    await wrapper.find("form").trigger("submit.prevent");
    await wrapper.vm.$nextTick();

    expect(global.fetch).toHaveBeenCalledWith("/auth/reset-password", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        token: "test-token",
        password: "newpassword123",
      }),
    });

    await wrapper.vm.$nextTick();
    await router.isReady();
    // Router navigation happens asynchronously
    await new Promise((resolve) => setTimeout(resolve, 100));
    expect(router.currentRoute.value.path).toBe("/login");
  });

  it("should show error message on failure", async () => {
    global.fetch.mockResolvedValueOnce({
      ok: false,
      status: 400,
    });

    wrapper = await mountResetPassword("invalid-token");

    await wrapper.find('input[type="password"]').setValue("newpassword123");
    await wrapper.find("form").trigger("submit.prevent");
    await wrapper.vm.$nextTick();

    expect(wrapper.vm.error).toBe("Failed to reset password");
    expect(wrapper.find(".text-red-500").exists()).toBe(true);
  });

  it("should handle network errors", async () => {
    global.fetch.mockRejectedValueOnce(new Error("Network error"));

    wrapper = await mountResetPassword("test-token");

    await wrapper.find('input[type="password"]').setValue("newpassword123");
    await wrapper.find("form").trigger("submit.prevent");
    await wrapper.vm.$nextTick();

    expect(wrapper.vm.error).toBe("Failed to reset password");
  });

  it("should have required attribute on password input", async () => {
    wrapper = await mountResetPassword();

    const passwordInput = wrapper.find('input[type="password"]');
    expect(passwordInput.attributes("required")).toBeDefined();
  });

  it("should not redirect if reset fails", async () => {
    global.fetch.mockResolvedValueOnce({
      ok: false,
      status: 400,
    });

    wrapper = await mountResetPassword("test-token");

    await wrapper.find('input[type="password"]').setValue("newpassword123");
    await wrapper.find("form").trigger("submit.prevent");
    await wrapper.vm.$nextTick();

    expect(router.currentRoute.value.path).toBe("/reset-password");
  });
});
