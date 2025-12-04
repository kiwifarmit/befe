/**
 * Tests for ForgotPassword.vue component
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { mount } from "@vue/test-utils";
import { createRouter, createWebHistory } from "vue-router";
import ForgotPassword from "../../views/ForgotPassword.vue";

// Mock global fetch
global.fetch = vi.fn();

// Mock router
const createTestRouter = () => {
  return createRouter({
    history: createWebHistory(),
    routes: [
      { path: "/forgot-password", component: ForgotPassword },
      { path: "/login", component: { template: "<div>Login</div>" } },
    ],
  });
};

describe("ForgotPassword.vue", () => {
  let router;
  let wrapper;

  beforeEach(() => {
    router = createTestRouter();
    vi.clearAllMocks();
  });

  const mountForgotPassword = async () => {
    await router.push("/forgot-password");
    wrapper = mount(ForgotPassword, {
      global: {
        plugins: [router],
      },
    });
    await router.isReady();
    return wrapper;
  };

  it("should render forgot password form", async () => {
    wrapper = await mountForgotPassword();

    expect(wrapper.find("h2").text()).toBe("Forgot Password");
    expect(wrapper.find('input[type="email"]').exists()).toBe(true);
    expect(wrapper.find('button[type="submit"]').exists()).toBe(true);
  });

  it("should bind email input", async () => {
    wrapper = await mountForgotPassword();

    const emailInput = wrapper.find('input[type="email"]');
    await emailInput.setValue("test@example.com");

    expect(wrapper.vm.email).toBe("test@example.com");
  });

  it("should submit form and show success message", async () => {
    global.fetch.mockResolvedValueOnce({
      ok: true,
      status: 202,
    });

    wrapper = await mountForgotPassword();

    await wrapper.find('input[type="email"]').setValue("test@example.com");
    await wrapper.find("form").trigger("submit.prevent");
    await wrapper.vm.$nextTick();

    expect(global.fetch).toHaveBeenCalledWith("/auth/forgot-password", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ email: "test@example.com" }),
    });

    await wrapper.vm.$nextTick();
    expect(wrapper.vm.message).toContain("reset link has been sent");
    expect(wrapper.find(".text-green-600").exists()).toBe(true);
  });

  it("should show error message on failure", async () => {
    global.fetch.mockResolvedValueOnce({
      ok: false,
      status: 400,
      json: () => Promise.resolve({ detail: "Email not found" }),
    });

    wrapper = await mountForgotPassword();

    await wrapper.find('input[type="email"]').setValue("test@example.com");
    await wrapper.find("form").trigger("submit.prevent");
    await wrapper.vm.$nextTick();

    expect(wrapper.vm.error).toBe("Email not found");
    expect(wrapper.find(".text-red-500").exists()).toBe(true);
  });

  it("should show loading state during submission", async () => {
    global.fetch.mockImplementationOnce(
      () =>
        new Promise((resolve) =>
          setTimeout(
            () =>
              resolve({
                ok: true,
                status: 202,
              }),
            100,
          ),
        ),
    );

    wrapper = await mountForgotPassword();

    await wrapper.find('input[type="email"]').setValue("test@example.com");
    const button = wrapper.find('button[type="submit"]');
    await wrapper.find("form").trigger("submit.prevent");

    expect(wrapper.vm.loading).toBe(true);
    expect(button.text()).toBe("Sending...");
    expect(button.attributes("disabled")).toBeDefined();
  });

  it("should disable inputs during loading", async () => {
    global.fetch.mockImplementationOnce(
      () =>
        new Promise((resolve) =>
          setTimeout(
            () =>
              resolve({
                ok: true,
                status: 202,
              }),
            100,
          ),
        ),
    );

    wrapper = await mountForgotPassword();

    await wrapper.find('input[type="email"]').setValue("test@example.com");
    await wrapper.find("form").trigger("submit.prevent");

    const emailInput = wrapper.find('input[type="email"]');
    expect(emailInput.attributes("disabled")).toBeDefined();
  });

  it("should have link back to login", async () => {
    wrapper = await mountForgotPassword();

    // Router-link renders as <a> tag in Vue Router
    const loginLink = wrapper.find("a");
    expect(loginLink.exists()).toBe(true);
    // Check if it's the login link by text content
    const allLinks = wrapper.findAll("a");
    const loginLinkElement = allLinks.find((link) =>
      link.text().includes("Back to Login"),
    );
    expect(loginLinkElement).toBeTruthy();
  });

  it("should clear error and message on new submission", async () => {
    global.fetch
      .mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: () => Promise.resolve({ detail: "Error" }),
      })
      .mockResolvedValueOnce({
        ok: true,
        status: 202,
      });

    wrapper = await mountForgotPassword();

    // First failed attempt
    await wrapper.find('input[type="email"]').setValue("test@example.com");
    await wrapper.find("form").trigger("submit.prevent");
    await wrapper.vm.$nextTick();

    expect(wrapper.vm.error).toBe("Error");

    // Second successful attempt
    await wrapper.find("form").trigger("submit.prevent");
    await wrapper.vm.$nextTick();

    expect(wrapper.vm.error).toBe("");
    expect(wrapper.vm.message).toContain("reset link has been sent");
  });

  it("should handle network errors", async () => {
    // Suppress console.error for this test
    const consoleError = console.error;
    console.error = vi.fn();

    global.fetch.mockRejectedValueOnce(new Error("Network error"));

    wrapper = await mountForgotPassword();

    await wrapper.find('input[type="email"]').setValue("test@example.com");
    await wrapper.find("form").trigger("submit.prevent");
    await wrapper.vm.$nextTick();
    await new Promise((resolve) => setTimeout(resolve, 50));

    // Error message can be the error message or a generic one
    expect(wrapper.vm.error).toBeTruthy();
    expect(wrapper.vm.error.length).toBeGreaterThan(0);

    // Restore console.error
    console.error = consoleError;
  });
});
