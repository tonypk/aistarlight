import { defineStore } from "pinia";
import { computed, ref } from "vue";
import {
  authApi,
  type Company,
  type LoginData,
  type RegisterData,
} from "../api/auth";

export const useAuthStore = defineStore("auth", () => {
  const user = ref<Record<string, string> | null>(null);
  const accessToken = ref(localStorage.getItem("access_token") || "");
  const companies = ref<Company[]>([]);
  const userLoading = ref(false);

  const isAuthenticated = computed(() => !!accessToken.value);
  const currentRole = computed(
    () => user.value?.role || localStorage.getItem("user_role") || "viewer",
  );
  const isOwnerOrAdmin = computed(() =>
    ["owner", "admin", "company_admin"].includes(currentRole.value),
  );

  async function login(data: LoginData) {
    const res = await authApi.login(data);
    const tokens = res.data.data;
    accessToken.value = tokens.access_token;
    localStorage.setItem("access_token", tokens.access_token);
    localStorage.setItem("refresh_token", tokens.refresh_token);
    await fetchUser();
  }

  async function register(data: RegisterData) {
    await authApi.register(data);
    await login({ email: data.email, password: data.password });
  }

  async function fetchUser() {
    if (userLoading.value) return;
    userLoading.value = true;
    try {
      const res = await authApi.me();
      user.value = res.data.data;
      if (user.value?.role) {
        localStorage.setItem("user_role", user.value.role);
      }
    } finally {
      userLoading.value = false;
    }
  }

  async function fetchCompanies() {
    try {
      const res = await authApi.listCompanies();
      companies.value = res.data.data.companies || [];
    } catch {
      companies.value = [];
    }
  }

  async function switchCompany(tenantId: string) {
    const res = await authApi.switchCompany(tenantId);
    const tokens = res.data.data;
    accessToken.value = tokens.access_token;
    localStorage.setItem("access_token", tokens.access_token);
    localStorage.setItem("refresh_token", tokens.refresh_token);
    await fetchUser();
    await fetchCompanies();
  }

  async function logout() {
    const refreshToken = localStorage.getItem("refresh_token");
    if (refreshToken) {
      try {
        await authApi.logout(refreshToken);
      } catch {
        // Best-effort token revocation
      }
    }
    user.value = null;
    accessToken.value = "";
    companies.value = [];
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    localStorage.removeItem("user_role");
  }

  async function initUser() {
    if (isAuthenticated.value && !user.value) {
      await fetchUser();
    }
  }

  return {
    user,
    accessToken,
    companies,
    isAuthenticated,
    currentRole,
    isOwnerOrAdmin,
    userLoading,
    login,
    register,
    fetchUser,
    fetchCompanies,
    switchCompany,
    logout,
    initUser,
  };
});
