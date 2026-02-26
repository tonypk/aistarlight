<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import AppHeader from './components/layout/AppHeader.vue'
import AppSidebar from './components/layout/AppSidebar.vue'
import ToastContainer from './components/layout/ToastContainer.vue'
import { useAuthStore } from './stores/auth'

const auth = useAuthStore()
const route = useRoute()
const showLayout = computed(() => auth.isAuthenticated && route.name !== 'login')

onMounted(() => {
  auth.initUser()
})
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
    <ToastContainer />
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
  min-width: 0;
}
.content {
  padding: 24px;
  flex: 1;
  overflow-x: auto;
}

@media (max-width: 768px) {
  .main-area {
    margin-left: 0;
  }
  .content {
    padding: 12px;
  }
}
</style>
