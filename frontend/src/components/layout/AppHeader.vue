<script setup lang="ts">
import { useAuthStore } from '../../stores/auth'

const auth = useAuthStore()
</script>

<template>
  <header class="header">
    <div class="header-left">
      <h1 class="page-title">
        <router-view name="title" />
      </h1>
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
.user-info {
  font-size: 14px;
  color: #555;
}
</style>
