<script setup lang="ts">
import { ref } from 'vue'
import type { Detection } from '../composables/useDetection'
import { getClassNameCN, getClassColor } from '../utils/classNames'

interface ImageItem {
  id: string
  name: string
  url: string
  annotatedUrl: string | null
  detections: Detection[]
  counts: Record<string, number>
  isDetected: boolean
  isDetecting: boolean
}

defineProps<{
  images: ImageItem[]
  currentIndex: number
}>()

const emit = defineEmits<{
  (e: 'select', index: number): void
  (e: 'upload', files: File[]): void
}>()

const fileInputRef = ref<HTMLInputElement | null>(null)
const folderInputRef = ref<HTMLInputElement | null>(null)
const isDragging = ref(false)

// 选择文件
function triggerFileSelect() {
  fileInputRef.value?.click()
}

// 选择文件夹
function triggerFolderSelect() {
  folderInputRef.value?.click()
}

function handleFileSelect(e: Event) {
  const input = e.target as HTMLInputElement
  if (input.files && input.files.length > 0) {
    emit('upload', Array.from(input.files))
    input.value = ''
  }
}

// 拖放
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
    emit('upload', Array.from(files))
  }
}
</script>

<template>
  <div class="h-full flex flex-col">
    <!-- 上传按钮区 -->
    <div class="p-3 border-b border-bilibili-border shrink-0">
      <div class="flex gap-2">
        <button
          @click="triggerFileSelect"
          class="flex-1 h-9 rounded-lg bg-bilibili-hover text-bilibili-text-secondary hover:text-white text-xs font-medium transition-all flex items-center justify-center gap-1.5"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
            <polyline points="17 8 12 3 7 8"/>
            <line x1="12" x2="12" y1="3" y2="15"/>
          </svg>
          上传图片
        </button>
        <button
          @click="triggerFolderSelect"
          class="flex-1 h-9 rounded-lg bg-bilibili-hover text-bilibili-text-secondary hover:text-white text-xs font-medium transition-all flex items-center justify-center gap-1.5"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M4 20h16a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.93a2 2 0 0 1-1.66-.9l-.82-1.2A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13c0 1.1.9 2 2 2Z"/>
          </svg>
          上传文件夹
        </button>
      </div>

      <!-- 隐藏的文件输入 -->
      <input
        ref="fileInputRef"
        type="file"
        accept="image/*"
        multiple
        @change="handleFileSelect"
        class="hidden"
      />
      <input
        ref="folderInputRef"
        type="file"
        multiple
        webkitdirectory
        @change="handleFileSelect"
        class="hidden"
      />
    </div>

    <!-- 拖放区域（空状态） -->
    <div
      v-if="images.length === 0"
      @dragover="handleDragOver"
      @dragleave="handleDragLeave"
      @drop="handleDrop"
      class="flex-1 flex items-center justify-center m-3 rounded-lg border-2 border-dashed transition-all"
      :class="isDragging
        ? 'border-bilibili-pink bg-bilibili-pink/5'
        : 'border-bilibili-border'"
    >
      <div class="text-center">
        <div class="w-12 h-12 mx-auto mb-3 rounded-full bg-bilibili-hover flex items-center justify-center">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="text-bilibili-text-tertiary">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
            <polyline points="17 8 12 3 7 8"/>
            <line x1="12" x2="12" y1="3" y2="15"/>
          </svg>
        </div>
        <p class="text-xs text-bilibili-text-secondary mb-1">拖拽图片到这里</p>
        <p class="text-xs text-bilibili-text-tertiary">或点击上方按钮上传</p>
      </div>
    </div>

    <!-- 图片列表 -->
    <div v-else class="flex-1 overflow-y-auto p-2 space-y-1">
      <div
        v-for="(img, idx) in images"
        :key="img.id"
        @click="$emit('select', idx)"
        class="flex items-center gap-3 p-2 rounded-lg cursor-pointer transition-all group"
        :class="idx === currentIndex
          ? 'bg-bilibili-hover'
          : 'hover:bg-bilibili-hover/50'"
      >
        <!-- 缩略图 -->
        <div class="w-14 h-14 rounded-md bg-bilibili-bg overflow-hidden flex-shrink-0 relative">
          <img
            :src="img.url"
            :alt="img.name"
            class="w-full h-full object-cover"
          />

          <!-- 检测中遮罩 -->
          <div
            v-if="img.isDetecting"
            class="absolute inset-0 flex items-center justify-center bg-black/50"
          >
            <div class="w-5 h-5 border-2 border-bilibili-pink border-t-transparent rounded-full animate-spin"></div>
          </div>

          <!-- 已检测标记 -->
          <div
            v-if="img.isDetected && !img.isDetecting"
            class="absolute top-0.5 right-0.5 w-3.5 h-3.5 rounded-full bg-bilibili-pink flex items-center justify-center"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
              <polyline points="20 6 9 17 4 12"/>
            </svg>
          </div>

          <!-- 序号 -->
          <div
            v-if="idx === currentIndex"
            class="absolute bottom-0.5 left-0.5 px-1.5 py-0.5 bg-bilibili-pink rounded text-[10px] text-white font-medium"
          >
            {{ idx + 1 }}
          </div>
        </div>

        <!-- 文件名和信息 -->
        <div class="flex-1 min-w-0">
          <p class="text-xs text-bilibili-text-primary truncate">{{ img.name }}</p>
          <div class="flex items-center gap-1.5 mt-1">
            <template v-if="img.isDetected && img.detections.length > 0">
              <span
                v-for="(count, cls) in img.counts"
                :key="cls"
                class="px-1.5 py-0.5 rounded text-[10px] font-medium text-white"
                :style="{ backgroundColor: getClassColor(cls) }"
              >
                {{ getClassNameCN(cls) }} {{ count }}
              </span>
            </template>
            <span v-else-if="img.isDetected" class="text-[10px] text-bilibili-text-tertiary">
              无目标
            </span>
            <span v-else-if="img.isDetecting" class="text-[10px] text-bilibili-pink">
              检测中...
            </span>
            <span v-else class="text-[10px] text-bilibili-text-tertiary">
              待检测
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
