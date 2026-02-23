<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '../../stores/auth'

const auth = useAuthStore()
const route = useRoute()

const pageTitle = computed(() => {
  return (route.meta.title as string) || 'AIStarlight'
})
</script>

<template>
  <header class="header">
    <div class="header-left">
      <h1 class="page-title">{{ pageTitle }}</h1>
    </div>
    <div class="header-right">
      <span class="user-info" v-if="auth.user">
        {{ auth.user.full_name || auth.user.email }}
      </span>
    </div>
  </header>
</template>

<style scoped>
.header {
  height: 60px;
  background: #fff;
  border-bottom: 1px solid #e5e7eb;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
}
.page-title {
  font-size: 18px;
  font-weight: 600;
  color: #111;
}
.user-info {
  font-size: 14px;
  color: #555;
}
</style>
