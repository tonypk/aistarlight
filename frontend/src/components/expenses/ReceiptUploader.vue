<script setup lang="ts">
import { ref } from 'vue'
import { NUpload, NButton, useMessage } from 'naive-ui'
import type { UploadFileInfo } from 'naive-ui'
import { expenseItemApi } from '../../api/expenses'

const props = defineProps<{
  itemId: string
}>()

const emit = defineEmits<{
  uploaded: []
}>()

const message = useMessage()
const uploading = ref(false)

const MAX_SIZE_MB = 10
const MAX_SIZE_BYTES = MAX_SIZE_MB * 1024 * 1024

async function handleChange(options: { file: UploadFileInfo; fileList: UploadFileInfo[] }) {
  const rawFile = options.file.file
  if (!rawFile) return

  if (rawFile.size > MAX_SIZE_BYTES) {
    message.error(`File too large. Maximum allowed: ${MAX_SIZE_MB}MB.`)
    return
  }

  uploading.value = true
  try {
    await expenseItemApi.uploadReceipt(props.itemId, rawFile)
    message.success('Receipt uploaded successfully')
    emit('uploaded')
  } catch {
    message.error('Failed to upload receipt')
  } finally {
    uploading.value = false
  }
}
</script>

<template>
  <NUpload
    accept=".jpg,.jpeg,.png,.pdf"
    :max="1"
    :show-file-list="false"
    :custom-request="() => {}"
    @change="handleChange"
  >
    <NButton size="small" :loading="uploading" :disabled="uploading">
      Upload Receipt
    </NButton>
  </NUpload>
</template>
