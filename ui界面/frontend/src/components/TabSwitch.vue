<script setup lang="ts">
// Props
const props = defineProps<{
  activeTab: 'camera' | 'image'
}>()

const emit = defineEmits<{
  (e: 'update:activeTab', value: 'camera' | 'image'): void
}>()

const tabs = [
  { id: 'camera' as const, label: '摄像头' },
  { id: 'image' as const, label: '图片上传' },
]

function switchTab(tabId: 'camera' | 'image') {
  emit('update:activeTab', tabId)
}
</script>

<template>
  <div class="flex items-center gap-1 p-1 bg-apple-gray-2 rounded-xl">
    <button
      v-for="tab in tabs"
      :key="tab.id"
      @click="switchTab(tab.id)"
      class="relative px-6 py-2 rounded-lg text-sm font-medium transition-all duration-200"
      :class="activeTab === tab.id
        ? 'bg-white text-apple-gray-4 shadow-sm'
        : 'text-apple-gray-3 hover:text-apple-gray-4'"
    >
      {{ tab.label }}
    </button>
  </div>
</template>
