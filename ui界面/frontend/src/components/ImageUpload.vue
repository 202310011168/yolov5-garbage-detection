<script setup lang="ts">
import { ref, computed, watch } from 'vue'

// Props
const props = defineProps<{
  currentModel: string
  confidence: number
  iou: number
  annotatedImage?: string | null
  isDetecting?: boolean
}>()

const emit = defineEmits<{
  (e: 'upload', file: File): void
  (e: 'clear'): void
  (e: 'loading', isLoading: boolean): void
}>()

// 状态
const isDragging = ref(false)
const previewImage = ref<string | null>(null)
const selectedFile = ref<File | null>(null)
const fileInputRef = ref<HTMLInputElement | null>(null)

// 显示的图片：有标注图就显示标注图，否则显示原图
const displayImage = computed(() => {
  return props.annotatedImage || previewImage.value
})

// 拖放处理
function handleDragOver(e: DragEvent) {
  e.preventDefault()
  isDragging.value = true
}

function handleDragLeave() {
  isDragging.value = false
}

function handleDrop(e: DragEvent) {
  e.preventDefault()
  isDragging.value = false

  const files = e.dataTransfer?.files
  if (files && files.length > 0) {
    handleFile(files[0])
  }
}

// 文件选择处理
function handleFileSelect(e: Event) {
  const input = e.target as HTMLInputElement
  if (input.files && input.files.length > 0) {
    handleFile(input.files[0])
  }
}

// 处理文件
function handleFile(file: File) {
  if (!file.type.startsWith('image/')) {
    alert('请选择图片文件')
    return
  }

  selectedFile.value = file

  const reader = new FileReader()
  reader.onload = (e) => {
    previewImage.value = e.target?.result as string
  }
  reader.readAsDataURL(file)

  emit('upload', file)
}

// 触发文件选择
function triggerFileSelect() {
  fileInputRef.value?.click()
}

// 清除选择
function clearSelection() {
  selectedFile.value = null
  previewImage.value = null
  if (fileInputRef.value) {
    fileInputRef.value.value = ''
  }
  emit('clear')
}

// 预览样式
const previewContainerClass = computed(() => {
  return isDragging.value
    ? 'border-apple-blue bg-apple-blue/5'
    : 'border-apple-gray-2 hover:border-apple-gray-3'
})
</script>

<template>
  <div class="w-full">
    <!-- 文件输入（隐藏） -->
    <input
      ref="fileInputRef"
      type="file"
      accept="image/*"
      @change="handleFileSelect"
      class="hidden"
    />

    <!-- 上传区域 -->
    <div
      v-if="!displayImage"
      @dragover="handleDragOver"
      @dragleave="handleDragLeave"
      @drop="handleDrop"
      @click="triggerFileSelect"
      class="w-full aspect-video border-2 border-dashed rounded-2xl flex flex-col items-center justify-center cursor-pointer transition-all duration-200"
      :class="previewContainerClass"
    >
      <div class="w-16 h-16 rounded-full bg-apple-gray-1 flex items-center justify-center mb-4">
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="32"
          height="32"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="1.5"
          stroke-linecap="round"
          stroke-linejoin="round"
          class="text-apple-gray-3"
        >
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
          <polyline points="17 8 12 3 7 8"/>
          <line x1="12" x2="12" y1="3" y2="15"/>
        </svg>
      </div>

      <p class="text-sm font-medium text-apple-gray-4 mb-2">
        拖拽图片到这里，或点击选择文件
      </p>
      <p class="text-xs text-apple-gray-3">
        支持 JPG、PNG 格式
      </p>
    </div>

    <!-- 预览/检测结果区域 -->
    <div v-else class="relative w-full">
      <div class="w-full aspect-video rounded-2xl overflow-hidden bg-black shadow-apple relative">
        <img
          :src="displayImage"
          alt="检测结果"
          class="w-full h-full object-contain"
        />

        <!-- 检测中覆盖层 -->
        <div
          v-if="isDetecting"
          class="absolute inset-0 flex items-center justify-center bg-black/40 backdrop-blur-sm"
        >
          <div class="flex flex-col items-center gap-3">
            <div class="w-10 h-10 border-3 border-white border-t-transparent rounded-full animate-spin"></div>
            <span class="text-sm text-white font-medium">识别中...</span>
          </div>
        </div>

        <!-- 标注标签 -->
        <div
          v-if="annotatedImage && !isDetecting"
          class="absolute top-3 left-3 px-3 py-1 bg-apple-blue/90 backdrop-blur rounded-full text-xs text-white font-medium"
        >
          已标注
        </div>
      </div>

      <!-- 操作按钮 -->
      <div class="absolute top-3 right-3 flex gap-2">
        <button
          @click="triggerFileSelect"
          class="w-10 h-10 rounded-full bg-black/50 backdrop-blur flex items-center justify-center text-white hover:bg-black/70 transition-colors"
          title="重新选择"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="18"
            height="18"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
            <polyline points="17 8 12 3 7 8"/>
            <line x1="12" x2="12" y1="3" y2="15"/>
          </svg>
        </button>
        <button
          @click="clearSelection"
          class="w-10 h-10 rounded-full bg-black/50 backdrop-blur flex items-center justify-center text-white hover:bg-black/70 transition-colors"
          title="清除"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="18"
            height="18"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <path d="M18 6 6 18"/>
            <path d="m6 6 12 12"/>
          </svg>
        </button>
      </div>

      <!-- 文件名 -->
      <div class="mt-3 flex items-center gap-2">
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
          class="text-apple-gray-3"
        >
          <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/>
          <polyline points="14 2 14 8 20 8"/>
        </svg>
        <span class="text-sm text-apple-gray-3 truncate">{{ selectedFile?.name }}</span>
      </div>
    </div>
  </div>
</template>
