import { defineStore } from 'pinia'
import { ref } from 'vue'
import { vendorPoliciesApi } from '../api/vendorPolicies'
import type { VendorPolicy, RuleSuggestion, UpdateVendorDefaults } from '../api/vendorPolicies'

export const useVendorPolicyStore = defineStore('vendorPolicies', () => {
  const policies = ref<VendorPolicy[]>([])
  const suggestions = ref<RuleSuggestion[]>([])
  const loading = ref(false)

  async function fetchPolicies(page = 1, limit = 50) {
    loading.value = true
    try {
      const res = await vendorPoliciesApi.list(page, limit)
      policies.value = res.data.data || []
    } finally {
      loading.value = false
    }
  }

  async function updatePolicy(id: string, data: UpdateVendorDefaults) {
    await vendorPoliciesApi.update(id, data)
    await fetchPolicies()
  }

  async function deletePolicy(id: string) {
    await vendorPoliciesApi.delete(id)
    policies.value = policies.value.filter(p => p.id !== id)
  }

  async function fetchSuggestions() {
    const res = await vendorPoliciesApi.suggestions()
    suggestions.value = res.data.data || []
  }

  async function promoteRule(id: string) {
    await vendorPoliciesApi.promote(id)
    await fetchPolicies()
    await fetchSuggestions()
  }

  return {
    policies,
    suggestions,
    loading,
    fetchPolicies,
    updatePolicy,
    deletePolicy,
    fetchSuggestions,
    promoteRule,
  }
})
