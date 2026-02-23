<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import AppHeader from './components/layout/AppHeader.vue'
import AppSidebar from './components/layout/AppSidebar.vue'
import { useAuthStore } from './stores/auth'

const auth = useAuthStore()
const route = useRoute()
const showLayout = computed(() => auth.isAuthenticated && route.name !== 'login')
</script>

<template>
  <div class="app">
    <template v-if="showLayout">
      <AppSidebar />
      <div class="main-area">
        <AppHeader />
        <main class="content">
          <router-view />
        </main>
      </div>
    </template>
    <template v-else>
      <router-view />
    </template>
  </div>
</template>

<style>
.app {
  display: flex;
  min-height: 100vh;
  background: #f5f7fa;
}
.main-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  margin-left: 240px;
}
.content {
  padding: 24px;
  flex: 1;
}
</style>
