<script setup lang="ts">
defineProps<{
  data: Record<string, string> | null
  reportType: string
}>()
</script>

<template>
  <div class="preview" v-if="data">
    <h3>{{ reportType }} Preview</h3>
    <table>
      <tbody>
        <tr v-for="(value, key) in data" :key="key">
          <td class="label">{{ String(key).replace(/_/g, ' ') }}</td>
          <td class="value">{{ value }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<style scoped>
.preview {
  background: #fff;
  border-radius: 12px;
  padding: 24px;
  border: 1px solid #e5e7eb;
}
h3 { margin-bottom: 16px; }
table { width: 100%; }
td { padding: 8px 12px; border-bottom: 1px solid #f3f4f6; }
.label { font-weight: 500; text-transform: capitalize; color: #555; }
.value { text-align: right; font-family: monospace; }
</style>
