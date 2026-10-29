<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import CameraView from './components/CameraView.vue'
import ImageList from './components/ImageList.vue'
import ControlPanel from './components/ControlPanel.vue'
import ResultPanel from './components/ResultPanel.vue'
import VideoPlayer from './components/VideoPlayer.vue'
import { useDetection, type Model, type Detection, type VideoDetectionResponse } from './composables/useDetection'

// 模式：摄像头 / 图片 / 视频
const mode = ref<'camera' | 'image' | 'video'>('image')

// 模型和参数
const models = ref<Model[]>([])
const currentModel = ref('yolov5s')
const confidence = ref(0.6)
const iou = ref(0.45)

// 右侧边栏 Tab
const sidebarTab = ref<'list' | 'params' | 'result'>('list')

// 图片列表
interface ImageItem {
  id: string
  file: File
  name: string
  url: string
  annotatedUrl: string | null
  detections: Detection[]
  counts: Record<string, number>
  isDetected: boolean
  isDetecting: boolean
}

const imageList = ref<ImageItem[]>([])
const currentIndex = ref(0)

const currentImage = computed(() => {
  if (imageList.value.length === 0) return null
  return imageList.value[currentIndex.value]
})

const displayImage = computed(() => {
  if (!currentImage.value) return ''
  return currentImage.value.annotatedUrl || currentImage.value.url
})

// API
const { getModels, detectImage, detectVideo, downloadImage, getDownloadUrl } = useDetection()

// CameraView 引用
const cameraViewRef = ref<InstanceType<typeof CameraView> | null>(null)

// 摄像头检测结果
const cameraDetections = ref<Detection[]>([])
const cameraCounts = ref<Record<string, number>>({})

// 当前显示的检测结果（图片模式或摄像头模式或视频模式）
const currentDetections = computed(() => {
  if (mode.value === 'camera') return cameraDetections.value
  if (mode.value === 'video') return videoDetections.value
  return currentImage.value?.detections || []
})

const currentCounts = computed(() => {
  if (mode.value === 'camera') return cameraCounts.value
  if (mode.value === 'video') return videoCounts.value
  return currentImage.value?.counts || {}
})

// 初始化
onMounted(async () => {
  models.value = await getModels()
  const sModel = models.value.find(m => m.id === 'yolov5s')
  if (sModel) {
    currentModel.value = 'yolov5s'
  } else if (models.value.length > 0) {
    currentModel.value = models.value[0].id
  }
})

// 处理图片文件夹/文件上传
function handleFilesSelected(files: File[]) {
  const newItems: ImageItem[] = files
    .filter(f => f.type.startsWith('image/'))
    .map((file, idx) => ({
      id: `img-${Date.now()}-${idx}`,
      file,
      name: file.name,
      url: URL.createObjectURL(file),
      annotatedUrl: null,
      detections: [],
      counts: {},
      isDetected: false,
      isDetecting: false,
    }))

  if (newItems.length > 0) {
    const oldLen = imageList.value.length
    imageList.value.push(...newItems)
    if (oldLen === 0) {
      currentIndex.value = 0
    }
  }
}

// 切换图片
function prevImage() {
  if (imageList.value.length <= 1) return
  currentIndex.value = (currentIndex.value - 1 + imageList.value.length) % imageList.value.length
}

function nextImage() {
  if (imageList.value.length <= 1) return
  currentIndex.value = (currentIndex.value + 1) % imageList.value.length
}

function selectImage(index: number) {
  currentIndex.value = index
}

// 检测当前图片
async function detectCurrent() {
  if (!currentImage.value || currentImage.value.isDetecting) return

  const item = currentImage.value
  item.isDetecting = true

  try {
    const result = await detectImage(item.file, currentModel.value, confidence.value, iou.value)
    if (result.success) {
      item.detections = result.detections || []
      item.counts = result.counts || {}
      item.annotatedUrl = result.annotated_image ? `data:image/jpeg;base64,${result.annotated_image}` : null
      item.isDetected = true
    }
  } catch (err) {
    console.error('Detection failed:', err)
  } finally {
    item.isDetecting = false
  }
}

// 批量检测
const isBatchDetecting = ref(false)

async function batchDetect() {
  if (isBatchDetecting.value || imageList.value.length === 0) return

  isBatchDetecting.value = true

  for (let i = 0; i < imageList.value.length; i++) {
    const item = imageList.value[i]
    if (item.isDetected) continue

    currentIndex.value = i
    item.isDetecting = true

    try {
      const result = await detectImage(item.file, currentModel.value, confidence.value, iou.value)
      if (result.success) {
        item.detections = result.detections || []
        item.counts = result.counts || {}
        item.annotatedUrl = result.annotated_image ? `data:image/jpeg;base64,${result.annotated_image}` : null
        item.isDetected = true
      }
    } catch (err) {
      console.error(`检测 ${item.name} 失败:`, err)
    } finally {
      item.isDetecting = false
    }
  }

  isBatchDetecting.value = false
}

// 批量下载
function batchDownload() {
  const detectedItems = imageList.value.filter(item => item.isDetected && item.annotatedUrl)
  if (detectedItems.length === 0) {
    alert('没有已检测的图片可下载')
    return
  }

  detectedItems.forEach((item, idx) => {
    setTimeout(() => {
      if (item.annotatedUrl) {
        const name = item.name.replace(/\.[^.]+$/, '') + '_detected.jpg'
        downloadImage(item.annotatedUrl, name)
      }
    }, idx * 300)
  })
}

// 清空列表
function clearAll() {
  if (imageList.value.length === 0) return
  if (!confirm('确定要清空所有图片吗？')) return

  imageList.value.forEach(item => {
    URL.revokeObjectURL(item.url)
  })
  imageList.value = []
  currentIndex.value = 0
}

// 摄像头检测结果处理
function handleCameraDetections(dets: Detection[], counts: Record<string, number>) {
  cameraDetections.value = dets
  cameraCounts.value = counts
}

// 视频检测相关
const videoFile = ref<File | null>(null)
const videoUrl = ref<string | null>(null)
const videoResult = ref<VideoDetectionResponse | null>(null)
const isVideoDetecting = ref(false)
const frameInterval = ref(10)
const videoPlayerRef = ref<InstanceType<typeof VideoPlayer> | null>(null)
const videoDetectionsLive = ref<Detection[]>([])
const videoCountsLive = ref<Record<string, number>>({})

// 切换模式
function switchMode(newMode: 'camera' | 'image' | 'video') {
  if (mode.value === newMode) return

  if (mode.value === 'camera') {
    cameraViewRef.value?.stopCamera()
  }

  mode.value = newMode
  cameraDetections.value = []
  cameraCounts.value = {}
}

// 检测统计
const detectedCount = computed(() => imageList.value.filter(i => i.isDetected).length)
const totalCount = computed(() => imageList.value.length)

// 视频文件上传
function handleVideoUpload(e: Event) {
  const input = e.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return

  videoFile.value = file
  videoUrl.value = URL.createObjectURL(file)
  videoResult.value = null
  input.value = ''
}

// 视频检测
async function detectVideoFile() {
  if (!videoFile.value || isVideoDetecting.value) return

  isVideoDetecting.value = true
  videoResult.value = null

  try {
    const result = await detectVideo(
      videoFile.value,
      currentModel.value,
      confidence.value,
      iou.value,
      frameInterval.value
    )
    if (result.success) {
      videoResult.value = result
    }
  } catch (err) {
    console.error('Video detection failed:', err)
  } finally {
    isVideoDetecting.value = false
  }
}

// 下载标注视频
function downloadAnnotatedVideo() {
  if (!videoResult.value?.video_url) return
  const url = getDownloadUrl(videoResult.value.video_url)
  const link = document.createElement('a')
  link.href = url
  link.download = 'annotated_video.mp4'
  link.click()
}

// 视频实时检测结果处理
function handleVideoDetections(dets: Detection[], counts: Record<string, number>) {
  videoDetectionsLive.value = dets
  videoCountsLive.value = counts
}

// 视频拖放上传
function handleVideoDrop(file: File) {
  videoFile.value = file
  videoUrl.value = URL.createObjectURL(file)
  videoResult.value = null
  videoDetectionsLive.value = []
  videoCountsLive.value = {}
}

// 视频检测结果
const videoDetections = computed(() => {
  if (mode.value !== 'video') return []
  if (videoResult.value) {
    const all: Detection[] = []
    for (const fr of videoResult.value.frame_results) {
      all.push(...fr.detections)
    }
    return all
  }
  return videoDetectionsLive.value
})

const videoCounts = computed(() => {
  if (mode.value !== 'video') return {}
  if (videoResult.value) {
    return videoResult.value.counts || {}
  }
  return videoCountsLive.value
})
</script>

<template>
  <div class="min-h-screen bg-bilibili-bg text-bilibili-text-primary flex flex-col">
    <!-- 顶部导航 -->
    <header class="h-14 bg-bilibili-card border-b border-bilibili-border flex items-center px-6 shrink-0">
      <div class="flex items-center gap-3">
        <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-bilibili-pink to-pink-400 flex items-center justify-center">
          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="white">
            <path d="M3 6h18v12H3z" opacity="0.3"/>
            <path d="M10 9l5 3-5 3V9z" fill="white"/>
          </svg>
        </div>
        <span class="text-base font-semibold">垃圾分类智能检测</span>
      </div>

      <!-- 模式切换 -->
      <div class="ml-8 flex items-center gap-1 bg-bilibili-bg rounded-lg p-1">
        <button
          @click="switchMode('camera')"
          class="px-4 py-1.5 rounded-md text-sm font-medium transition-all"
          :class="mode === 'camera'
            ? 'bg-bilibili-pink text-white shadow-sm'
            : 'text-bilibili-text-secondary hover:text-white'"
        >
          摄像头检测
        </button>
        <button
          @click="switchMode('image')"
          class="px-4 py-1.5 rounded-md text-sm font-medium transition-all"
          :class="mode === 'image'
            ? 'bg-bilibili-pink text-white shadow-sm'
            : 'text-bilibili-text-secondary hover:text-white'"
        >
          图片检测
        </button>
        <button
          @click="switchMode('video')"
          class="px-4 py-1.5 rounded-md text-sm font-medium transition-all"
          :class="mode === 'video'
            ? 'bg-bilibili-pink text-white shadow-sm'
            : 'text-bilibili-text-secondary hover:text-white'"
        >
          视频检测
        </button>
      </div>

      <div class="ml-auto flex items-center gap-4">
        <span class="text-xs text-bilibili-text-tertiary">
          GPU: RTX 4060 Laptop
        </span>
      </div>
    </header>

    <!-- 主体内容 -->
    <div class="flex-1 flex overflow-hidden">
      <!-- 左侧：主预览区 -->
      <div class="flex-1 flex flex-col p-4 gap-3 min-w-0">
        <!-- 视频/图片画面 -->
        <div class="flex-1 bg-black rounded-xl overflow-hidden relative flex items-center justify-center min-h-0">
          <!-- 摄像头模式 -->
          <template v-if="mode === 'camera'">
            <CameraView
              ref="cameraViewRef"
              :current-model="currentModel"
              :confidence="confidence"
              :iou="iou"
              class="w-full h-full"
              @detections="handleCameraDetections"
            />
          </template>

          <!-- 图片模式 -->
          <template v-else-if="mode === 'image'">
            <template v-if="currentImage">
              <img
                :src="displayImage"
                :alt="currentImage.name"
                class="max-w-full max-h-full object-contain"
              />

              <!-- 检测中遮罩 -->
              <div
                v-if="currentImage.isDetecting"
                class="absolute inset-0 flex items-center justify-center bg-black/40 backdrop-blur-sm"
              >
                <div class="flex flex-col items-center gap-3">
                  <div class="w-10 h-10 border-3 border-bilibili-pink border-t-transparent rounded-full animate-spin"></div>
                  <span class="text-sm text-white font-medium">识别中...</span>
                </div>
              </div>

              <!-- 已标注标签 -->
              <div
                v-if="currentImage.isDetected && !currentImage.isDetecting"
                class="absolute top-4 left-4 px-3 py-1 bg-bilibili-pink/90 backdrop-blur rounded-full text-xs text-white font-medium"
              >
                已标注
              </div>
            </template>

            <!-- 空状态 -->
            <div v-else class="flex flex-col items-center gap-4 text-bilibili-text-tertiary">
              <div class="w-20 h-20 rounded-full bg-bilibili-card flex items-center justify-center">
                <svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <rect width="18" height="18" x="3" y="3" rx="2"/>
                  <circle cx="9" cy="9" r="2"/>
                  <path d="m21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21"/>
                </svg>
              </div>
              <p class="text-sm">从右侧上传图片或文件夹开始检测</p>
            </div>
          </template>

          <!-- 视频模式 -->
          <template v-else-if="mode === 'video'">
            <template v-if="videoUrl">
              <VideoPlayer
                ref="videoPlayerRef"
                :video-src="videoUrl || ''"
                :annotated-src="videoResult?.video_url ? getDownloadUrl(videoResult.video_url) : null"
                :current-model="currentModel"
                :confidence="confidence"
                :iou="iou"
                :detect-interval="300"
                class="w-full h-full"
                @detections="handleVideoDetections"
                @upload="handleVideoDrop"
              />

              <!-- 完整检测中遮罩 -->
              <div
                v-if="isVideoDetecting"
                class="absolute inset-0 flex items-center justify-center bg-black/60 backdrop-blur-sm"
              >
                <div class="flex flex-col items-center gap-4">
                  <div class="w-12 h-12 border-4 border-bilibili-pink border-t-transparent rounded-full animate-spin"></div>
                  <span class="text-base text-white font-medium">完整视频检测中，请稍候...</span>
                  <span class="text-sm text-bilibili-text-secondary">可先播放视频实时预览检测效果</span>
                </div>
              </div>
            </template>

            <!-- 空状态 -->
            <div v-else class="flex flex-col items-center gap-4 text-bilibili-text-tertiary">
              <div class="w-20 h-20 rounded-full bg-bilibili-card flex items-center justify-center">
                <svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <polygon points="23 7 16 12 23 17 23 7"/>
                  <rect x="1" y="5" width="15" height="14" rx="2" ry="2"/>
                </svg>
              </div>
              <p class="text-sm">从右侧上传视频开始检测</p>
              <p class="text-xs text-bilibili-text-tertiary">支持 MP4、AVI、MOV 等格式</p>
            </div>
          </template>
        </div>

        <!-- 底部控制栏 -->
        <div class="h-14 bg-bilibili-card rounded-xl flex items-center px-4 gap-3 shrink-0">
          <!-- 图片模式控制 -->
          <template v-if="mode === 'image'">
            <button
              @click="prevImage"
              :disabled="imageList.length <= 1"
              class="w-10 h-10 rounded-lg bg-bilibili-hover flex items-center justify-center text-bilibili-text-secondary hover:text-white transition-colors"
              :class="{ 'opacity-30 cursor-not-allowed': imageList.length <= 1 }"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <polygon points="19 20 9 12 19 4 19 20"/>
                <line x1="5" x2="5" y1="19" y2="5"/>
              </svg>
            </button>

            <button
              @click="nextImage"
              :disabled="imageList.length <= 1"
              class="w-10 h-10 rounded-lg bg-bilibili-hover flex items-center justify-center text-bilibili-text-secondary hover:text-white transition-colors"
              :class="{ 'opacity-30 cursor-not-allowed': imageList.length <= 1 }"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <polygon points="5 4 15 12 5 20 5 4"/>
                <line x1="19" x2="19" y1="5" y2="19"/>
              </svg>
            </button>

            <div class="text-sm text-bilibili-text-secondary ml-2">
              <span v-if="imageList.length > 0" class="text-white font-medium">{{ currentIndex + 1 }}</span>
              <span class="mx-1">/</span>
              <span>{{ totalCount }}</span>
            </div>

            <div class="w-px h-6 bg-bilibili-border mx-2"></div>

            <button
              @click="detectCurrent"
              :disabled="!currentImage || currentImage.isDetecting || isBatchDetecting"
              class="px-4 py-2 rounded-lg text-sm font-medium transition-all flex items-center gap-2"
              :class="(!currentImage || currentImage.isDetecting || isBatchDetecting)
                ? 'bg-bilibili-hover text-bilibili-text-tertiary cursor-not-allowed'
                : 'bg-bilibili-pink text-white hover:bg-pink-500'"
            >
              <svg v-if="currentImage?.isDetecting" class="animate-spin" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 12a9 9 0 1 1-6.219-8.56"/>
              </svg>
              <svg v-else xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"/>
                <circle cx="12" cy="12" r="3"/>
              </svg>
              {{ currentImage?.isDetecting ? '检测中...' : '检测当前' }}
            </button>

            <button
              @click="batchDetect"
              :disabled="isBatchDetecting || imageList.length === 0"
              class="px-4 py-2 rounded-lg text-sm font-medium transition-all flex items-center gap-2"
              :class="(isBatchDetecting || imageList.length === 0)
                ? 'bg-bilibili-hover text-bilibili-text-tertiary cursor-not-allowed'
                : 'bg-bilibili-blue text-white hover:bg-cyan-500'"
            >
              <svg v-if="isBatchDetecting" class="animate-spin" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 12a9 9 0 1 1-6.219-8.56"/>
              </svg>
              <svg v-else xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M3 7V5a2 2 0 0 1 2-2h2"/>
                <path d="M17 3h2a2 2 0 0 1 2 2v2"/>
                <path d="M21 17v2a2 2 0 0 1-2 2h-2"/>
                <path d="M7 21H5a2 2 0 0 1-2-2v-2"/>
                <path d="m7 12 3 3 7-7"/>
              </svg>
              {{ isBatchDetecting ? `批量检测中 (${detectedCount}/${totalCount})` : '批量检测' }}
            </button>

            <button
              @click="batchDownload"
              :disabled="detectedCount === 0"
              class="px-4 py-2 rounded-lg text-sm font-medium transition-all flex items-center gap-2"
              :class="detectedCount === 0
                ? 'bg-bilibili-hover text-bilibili-text-tertiary cursor-not-allowed'
                : 'bg-bilibili-hover text-bilibili-text-secondary hover:text-white'"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                <polyline points="7 10 12 15 17 10"/>
                <line x1="12" x2="12" y1="15" y2="3"/>
              </svg>
              批量下载
            </button>

            <button
              @click="clearAll"
              :disabled="imageList.length === 0"
              class="px-4 py-2 rounded-lg text-sm font-medium transition-all flex items-center gap-2"
              :class="imageList.length === 0
                ? 'bg-bilibili-hover text-bilibili-text-tertiary cursor-not-allowed'
                : 'bg-bilibili-hover text-bilibili-text-secondary hover:text-red-400'"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M3 6h18"/>
                <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/>
                <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/>
              </svg>
              清空
            </button>
          </template>

          <!-- 摄像头模式 -->
          <template v-else-if="mode === 'camera'">
            <div class="text-sm text-bilibili-text-secondary">
              实时检测模式
              <span class="text-bilibili-pink ml-2">●</span>
              <span class="ml-1 text-xs">{{ currentDetections.length }} 个目标</span>
            </div>
          </template>

          <!-- 视频模式 -->
          <template v-else-if="mode === 'video'">
            <button
              @click="detectVideoFile"
              :disabled="!videoFile || isVideoDetecting"
              class="px-4 py-2 rounded-lg text-sm font-medium transition-all flex items-center gap-2"
              :class="(!videoFile || isVideoDetecting)
                ? 'bg-bilibili-hover text-bilibili-text-tertiary cursor-not-allowed'
                : 'bg-bilibili-pink text-white hover:bg-pink-500'"
            >
              <svg v-if="isVideoDetecting" class="animate-spin" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 12a9 9 0 1 1-6.219-8.56"/>
              </svg>
              <svg v-else xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"/>
                <circle cx="12" cy="12" r="3"/>
              </svg>
              {{ isVideoDetecting ? '检测中...' : '开始检测' }}
            </button>

            <button
              v-if="videoResult?.video_url"
              @click="downloadAnnotatedVideo"
              class="px-4 py-2 rounded-lg text-sm font-medium transition-all flex items-center gap-2 bg-bilibili-hover text-bilibili-text-secondary hover:text-white"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                <polyline points="7 10 12 15 17 10"/>
                <line x1="12" x2="12" y1="15" y2="3"/>
              </svg>
              下载标注视频
            </button>

            <div v-if="videoResult" class="text-sm text-bilibili-text-secondary ml-2">
              检测到 <span class="text-bilibili-pink font-medium">{{ videoResult.total_detected }}</span> 个目标
            </div>
          </template>

          <!-- 右侧进度 -->
          <div v-if="mode === 'image' && totalCount > 0" class="ml-auto flex items-center gap-3">
            <div class="text-xs text-bilibili-text-tertiary">
              已检测 <span class="text-bilibili-pink font-medium">{{ detectedCount }}</span> / {{ totalCount }}
            </div>
            <div class="w-32 h-1.5 bg-bilibili-hover rounded-full overflow-hidden">
              <div
                class="h-full bg-bilibili-pink rounded-full transition-all duration-300"
                :style="{ width: totalCount > 0 ? `${(detectedCount / totalCount) * 100}%` : '0%' }"
              ></div>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧边栏 -->
      <div class="w-[340px] bg-bilibili-card border-l border-bilibili-border flex flex-col shrink-0">
        <!-- 边栏 Tab -->
        <div class="h-12 flex items-center border-b border-bilibili-border px-2 shrink-0">
          <button
            v-for="tab in [
              { key: 'list', label: '图片列表', icon: 'M4 6h16M4 12h16M4 18h16' },
              { key: 'params', label: '参数设置', icon: 'M12 2a10 10 0 1 0 10 10' },
              { key: 'result', label: '检测结果', icon: 'M9 11l3 3L22 4' },
            ]"
            :key="tab.key"
            @click="sidebarTab = tab.key as any"
            class="flex-1 h-9 rounded-lg text-xs font-medium transition-all flex items-center justify-center gap-1.5"
            :class="sidebarTab === tab.key
              ? 'bg-bilibili-hover text-white'
              : 'text-bilibili-text-secondary hover:text-white'"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path :d="tab.icon"/>
            </svg>
            {{ tab.label }}
          </button>
        </div>

        <!-- 边栏内容 -->
        <div class="flex-1 min-h-0">
          <!-- 列表 Tab（图片列表 or 视频上传） -->
          <template v-if="sidebarTab === 'list'">
            <!-- 图片模式：图片列表 -->
            <ImageList
              v-if="mode === 'image'"
              :images="imageList"
              :current-index="currentIndex"
              class="h-full"
              @select="selectImage"
              @upload="handleFilesSelected"
            />

            <!-- 视频模式：视频上传 -->
            <div v-else-if="mode === 'video'" class="h-full overflow-y-auto p-4 space-y-4">
              <div class="space-y-3">
                <label class="text-xs font-medium text-bilibili-text-secondary uppercase tracking-wide">
                  上传视频
                </label>
                <label class="block">
                  <input
                    type="file"
                    accept="video/*"
                    @change="handleVideoUpload"
                    class="hidden"
                  />
                  <div class="border-2 border-dashed border-bilibili-border rounded-xl p-6 text-center cursor-pointer hover:border-bilibili-pink hover:bg-bilibili-hover/30 transition-all">
                    <div class="w-12 h-12 mx-auto mb-2 rounded-full bg-bilibili-bg flex items-center justify-center">
                      <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="text-bilibili-pink">
                        <polygon points="23 7 16 12 23 17 23 7"/>
                        <rect x="1" y="5" width="15" height="14" rx="2" ry="2"/>
                      </svg>
                    </div>
                    <p class="text-sm text-bilibili-text-primary font-medium">点击上传视频</p>
                    <p class="text-xs text-bilibili-text-tertiary mt-1">支持 MP4、AVI、MOV 等格式</p>
                  </div>
                </label>
              </div>

              <div v-if="videoFile" class="p-3 bg-bilibili-bg rounded-lg space-y-2">
                <div class="flex items-center gap-3">
                  <div class="w-10 h-10 rounded-lg bg-bilibili-hover flex items-center justify-center shrink-0">
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-bilibili-pink">
                      <polygon points="23 7 16 12 23 17 23 7"/>
                      <rect x="1" y="5" width="15" height="14" rx="2" ry="2"/>
                    </svg>
                  </div>
                  <div class="min-w-0 flex-1">
                    <p class="text-sm text-bilibili-text-primary truncate">{{ videoFile.name }}</p>
                    <p class="text-xs text-bilibili-text-tertiary">{{ (videoFile.size / 1024 / 1024).toFixed(2) }} MB</p>
                  </div>
                </div>
                <div v-if="videoResult" class="pt-2 border-t border-bilibili-border">
                  <div class="flex items-center justify-between text-xs">
                    <span class="text-bilibili-text-secondary">视频时长</span>
                    <span class="text-bilibili-text-primary">{{ videoResult.duration }}s</span>
                  </div>
                  <div class="flex items-center justify-between text-xs mt-1">
                    <span class="text-bilibili-text-secondary">检测帧数</span>
                    <span class="text-bilibili-text-primary">{{ videoResult.processed_frames }} / {{ videoResult.total_frames }}</span>
                  </div>
                </div>
              </div>

              <div class="space-y-2">
                <div class="flex items-center justify-between">
                  <label class="text-xs font-medium text-bilibili-text-secondary uppercase tracking-wide">
                    检测帧间隔
                  </label>
                  <span class="text-sm font-mono text-bilibili-pink">每 {{ frameInterval }} 帧</span>
                </div>
                <input
                  type="range"
                  v-model.number="frameInterval"
                  min="1"
                  max="30"
                  step="1"
                  class="w-full h-1.5 bg-bilibili-bg rounded-full appearance-none cursor-pointer accent-bilibili-pink"
                />
                <div class="flex justify-between text-xs text-bilibili-text-tertiary">
                  <span>每帧</span>
                  <span>每30帧</span>
                </div>
                <p class="text-xs text-bilibili-text-tertiary mt-1">
                  帧间隔越小检测越密，速度越慢
                </p>
              </div>
            </div>

            <!-- 摄像头模式 -->
            <div v-else class="h-full overflow-y-auto p-4">
              <div class="text-center py-8">
                <div class="w-14 h-14 mx-auto mb-3 rounded-full bg-bilibili-bg flex items-center justify-center">
                  <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="text-bilibili-pink">
                    <path d="M14.5 4h-5L7 7H4a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-3l-2.5-3z"/>
                    <circle cx="12" cy="13" r="3"/>
                  </svg>
                </div>
                <p class="text-sm text-bilibili-text-secondary">摄像头检测模式</p>
                <p class="text-xs text-bilibili-text-tertiary mt-1">点击画面中的按钮启动摄像头</p>
              </div>
            </div>
          </template>

          <!-- 参数设置 -->
          <div v-else-if="sidebarTab === 'params'" class="h-full overflow-y-auto">
            <ControlPanel
              :models="models"
              :current-model="currentModel"
              :confidence="confidence"
              :iou="iou"
              @update:current-model="(v) => currentModel = v"
              @update:confidence="(v) => confidence = v"
              @update:iou="(v) => iou = v"
            />
          </div>

          <!-- 检测结果 -->
          <div v-else-if="sidebarTab === 'result'" class="h-full overflow-y-auto p-4">
            <ResultPanel
              :detections="currentDetections"
              :counts="currentCounts"
            />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
