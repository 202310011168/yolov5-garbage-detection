<script setup lang="ts">
import { ref, onUnmounted, onMounted, nextTick, watch } from 'vue'
import type { Detection } from '../composables/useDetection'
import { useDetection } from '../composables/useDetection'
import { getClassNameCN, getClassColor } from '../utils/classNames'

const props = defineProps<{
  currentModel: string
  confidence: number
  iou: number
}>()

const emit = defineEmits<{
  (e: 'detections', detections: Detection[], counts: Record<string, number>): void
}>()

const { detectBase64 } = useDetection()

const videoRef = ref<HTMLVideoElement | null>(null)
const overlayCanvasRef = ref<HTMLCanvasElement | null>(null)
const containerRef = ref<HTMLDivElement | null>(null)
const isStreaming = ref(false)
const error = ref<string | null>(null)
const mediaStream = ref<MediaStream | null>(null)
const detectInterval = ref<number | null>(null)
const isDetecting = ref(false)
const isCameraLoading = ref(false)
const rawDetections = ref<Detection[]>([])

let videoReady = false
let stableDetections: Detection[] = []
let detectionHistory: Detection[][] = []
const HISTORY_SIZE = 2

async function startCamera() {
  if (isStreaming.value || isCameraLoading.value) return

  isCameraLoading.value = true
  error.value = null
  videoReady = false
  stableDetections = []
  detectionHistory = []
  rawDetections.value = []

  try {
    const stream = await navigator.mediaDevices.getUserMedia({
      video: {
        width: { ideal: 1280 },
        height: { ideal: 720 },
        facingMode: 'user',
      },
    })

    mediaStream.value = stream

    if (videoRef.value) {
      videoRef.value.srcObject = stream
      await videoRef.value.play()
      isStreaming.value = true

      videoRef.value.addEventListener('loadedmetadata', onVideoReady, { once: true })

      setTimeout(() => {
        if (isStreaming.value && !videoReady && videoRef.value && videoRef.value.videoWidth > 0) {
          onVideoReady()
        }
      }, 1000)
    }
  } catch (err) {
    console.error('Camera start failed:', err)
    error.value = err instanceof Error ? err.message : '无法访问摄像头'
  } finally {
    isCameraLoading.value = false
  }
}

function onVideoReady() {
  if (!isStreaming.value || videoReady) return
  videoReady = true

  nextTick(() => {
    initOverlayCanvas()
    startDetection()
  })
}

function initOverlayCanvas() {
  if (!overlayCanvasRef.value || !containerRef.value) return

  const container = containerRef.value
  const canvas = overlayCanvasRef.value

  canvas.width = container.clientWidth
  canvas.height = container.clientHeight
}

function getVideoDisplayRect() {
  if (!videoRef.value || !containerRef.value) return null

  const video = videoRef.value
  const container = containerRef.value
  const videoWidth = video.videoWidth
  const videoHeight = video.videoHeight

  if (videoWidth === 0 || videoHeight === 0) return null

  const containerWidth = container.clientWidth
  const containerHeight = container.clientHeight

  const scale = Math.min(containerWidth / videoWidth, containerHeight / videoHeight)
  const displayWidth = videoWidth * scale
  const displayHeight = videoHeight * scale
  const offsetX = (containerWidth - displayWidth) / 2
  const offsetY = (containerHeight - displayHeight) / 2

  return { scale, offsetX, offsetY, displayWidth, displayHeight, videoWidth, videoHeight }
}

function stopCamera() {
  stopDetection()

  if (mediaStream.value) {
    mediaStream.value.getTracks().forEach(track => track.stop())
    mediaStream.value = null
  }

  if (videoRef.value) {
    videoRef.value.srcObject = null
  }

  if (overlayCanvasRef.value) {
    const ctx = overlayCanvasRef.value.getContext('2d')
    if (ctx) {
      ctx.clearRect(0, 0, overlayCanvasRef.value.width, overlayCanvasRef.value.height)
    }
  }

  isStreaming.value = false
  videoReady = false
  stableDetections = []
  detectionHistory = []
  rawDetections.value = []
}

function stabilizeDetections(newDetections: Detection[]): Detection[] {
  detectionHistory.push([...newDetections])
  if (detectionHistory.length > HISTORY_SIZE) {
    detectionHistory.shift()
  }

  if (detectionHistory.length < 2) {
    return newDetections
  }

  const matched = new Set<number>()
  const result: Detection[] = []
  const lastFrame = detectionHistory[detectionHistory.length - 1]

  for (let i = 0; i < lastFrame.length; i++) {
    const curr = lastFrame[i]
    let bestMatch: Detection | null = null
    let bestIou = 0

    for (const prev of detectionHistory[detectionHistory.length - 2]) {
      if (prev.class !== curr.class) continue
      const iou = calcIou(curr.bbox, prev.bbox)
      if (iou > bestIou && iou > 0.3) {
        bestIou = iou
        bestMatch = prev
      }
    }

    if (bestMatch) {
      const smoothed: Detection = {
        ...curr,
        confidence: Math.max(curr.confidence, bestMatch.confidence),
        bbox: [
          (curr.bbox[0] + bestMatch.bbox[0]) / 2,
          (curr.bbox[1] + bestMatch.bbox[1]) / 2,
          (curr.bbox[2] + bestMatch.bbox[2]) / 2,
          (curr.bbox[3] + bestMatch.bbox[3]) / 2,
        ] as [number, number, number, number]
      }
      result.push(smoothed)
    } else {
      result.push(curr)
    }
  }

  return result
}

function calcIou(a: [number, number, number, number], b: [number, number, number, number]): number {
  const [ax1, ay1, ax2, ay2] = a
  const [bx1, by1, bx2, by2] = b

  const xx1 = Math.max(ax1, bx1)
  const yy1 = Math.max(ay1, by1)
  const xx2 = Math.min(ax2, bx2)
  const yy2 = Math.min(ay2, by2)

  const w = Math.max(0, xx2 - xx1)
  const h = Math.max(0, yy2 - yy1)
  const inter = w * h

  const areaA = (ax2 - ax1) * (ay2 - ay1)
  const areaB = (bx2 - bx1) * (by2 - by1)
  const union = areaA + areaB - inter

  return union > 0 ? inter / union : 0
}

function startDetection() {
  if (detectInterval.value) return

  detectInterval.value = window.setInterval(async () => {
    if (isDetecting.value || !videoRef.value) return

    const videoEl = videoRef.value
    if (videoEl.videoWidth === 0 || videoEl.videoHeight === 0) return

    isDetecting.value = true

    try {
      const videoWidth = videoEl.videoWidth
      const videoHeight = videoEl.videoHeight

      const tempCanvas = document.createElement('canvas')
      tempCanvas.width = videoWidth
      tempCanvas.height = videoHeight
      const tempCtx = tempCanvas.getContext('2d')
      if (!tempCtx) return

      tempCtx.save()
      tempCtx.translate(videoWidth, 0)
      tempCtx.scale(-1, 1)
      tempCtx.drawImage(videoEl, 0, 0, videoWidth, videoHeight)
      tempCtx.restore()
      const imageData = tempCanvas.toDataURL('image/jpeg', 0.95).split(',')[1]

      const result = await detectBase64(
        imageData,
        props.currentModel,
        props.confidence,
        props.iou
      )

      if (result.success) {
        const newDetections = result.detections || []
        rawDetections.value = newDetections
        stableDetections = stabilizeDetections(newDetections)

        const counts: Record<string, number> = {}
        for (const det of stableDetections) {
          counts[det.class] = (counts[det.class] || 0) + 1
        }

        initOverlayCanvas()
        drawDetections(stableDetections)

        emit('detections', stableDetections, counts)
      }
    } catch (err) {
      console.error('Detection failed:', err)
    } finally {
      isDetecting.value = false
    }
  }, 400)
}

function stopDetection() {
  if (detectInterval.value) {
    clearInterval(detectInterval.value)
    detectInterval.value = null
  }
}

function drawDetections(detections: Detection[]) {
  if (!overlayCanvasRef.value) return

  const canvas = overlayCanvasRef.value
  const ctx = canvas.getContext('2d')
  if (!ctx) return

  const rect = getVideoDisplayRect()
  if (!rect) return

  const { scale, offsetX, offsetY, videoWidth } = rect

  ctx.clearRect(0, 0, canvas.width, canvas.height)

  detections.forEach(det => {
    const [x1, y1, x2, y2] = det.bbox

    const dx1 = x1 * scale + offsetX
    const dy1 = y1 * scale + offsetY
    const dx2 = x2 * scale + offsetX
    const dy2 = y2 * scale + offsetY
    const dw = dx2 - dx1
    const dh = dy2 - dy1

    if (dw < 5 || dh < 5) return

    const color = getClassColor(det.class)
    const label = getClassNameCN(det.class)
    const conf = (det.confidence * 100).toFixed(0)

    ctx.strokeStyle = color
    ctx.lineWidth = Math.max(2, 3 * scale)
    ctx.strokeRect(dx1, dy1, dw, dh)

    const labelText = `${label} ${conf}%`
    const fontSize = Math.max(12, 14 * scale)
    ctx.font = `bold ${fontSize}px -apple-system, sans-serif`
    const textWidth = ctx.measureText(labelText).width
    const labelHeight = fontSize + 8

    const labelY = Math.max(labelHeight, dy1)
    ctx.fillStyle = color
    ctx.fillRect(dx1, labelY - labelHeight, textWidth + 12, labelHeight)

    ctx.fillStyle = 'white'
    ctx.textBaseline = 'middle'
    ctx.fillText(labelText, dx1 + 6, labelY - labelHeight / 2)
  })
}

function handleResize() {
  if (isStreaming.value) {
    initOverlayCanvas()
    if (stableDetections.length > 0) {
      drawDetections(stableDetections)
    }
  }
}

watch(() => props.confidence, () => {
  detectionHistory = []
  stableDetections = []
})

watch(() => props.iou, () => {
  detectionHistory = []
  stableDetections = []
})

watch(() => props.currentModel, () => {
  detectionHistory = []
  stableDetections = []
})

onUnmounted(() => {
  stopCamera()
  window.removeEventListener('resize', handleResize)
})

onMounted(() => {
  window.addEventListener('resize', handleResize)
})

defineExpose({
  startCamera,
  stopCamera,
  isStreaming,
  rawDetections,
})
</script>

<template>
  <div ref="containerRef" class="relative w-full h-full">
    <video
      ref="videoRef"
      class="absolute inset-0 w-full h-full object-contain"
      :class="{ 'opacity-0': !isStreaming }"
      :style="{ transform: 'scaleX(-1)' }"
      playsinline
      muted
    ></video>

    <canvas
      ref="overlayCanvasRef"
      class="absolute inset-0 w-full h-full pointer-events-none"
    ></canvas>

    <div
      v-if="!isStreaming"
      class="absolute inset-0 flex flex-col items-center justify-center bg-bilibili-bg"
    >
      <div class="w-20 h-20 rounded-full bg-bilibili-card flex items-center justify-center mb-4">
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="40"
          height="40"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="1.5"
          stroke-linecap="round"
          stroke-linejoin="round"
          class="text-bilibili-text-tertiary"
        >
          <path d="M14.5 4h-5L7 7H4a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-3l-2.5-3z"/>
          <circle cx="12" cy="13" r="3"/>
        </svg>
      </div>
      <p class="text-sm text-bilibili-text-secondary mb-6">点击下方按钮启动摄像头</p>

      <div
        v-if="error"
        class="absolute bottom-4 left-4 right-4 p-3 bg-red-500/10 border border-red-500/30 rounded-lg"
      >
        <p class="text-sm text-red-400">{{ error }}</p>
      </div>
    </div>

    <div
      v-if="isStreaming"
      class="absolute top-4 right-4 flex items-center gap-2 px-3 py-1.5 bg-black/50 backdrop-blur rounded-full"
    >
      <div class="w-2 h-2 rounded-full bg-bilibili-pink animate-pulse"></div>
      <span class="text-xs text-white">实时检测中</span>
    </div>

    <div class="absolute bottom-4 left-1/2 -translate-x-1/2 flex gap-3">
      <button
        v-if="!isStreaming"
        @click="startCamera"
        :disabled="isCameraLoading"
        class="flex items-center gap-2 px-8 py-3 bg-bilibili-pink text-white rounded-full font-medium text-sm shadow-lg hover:bg-pink-500 transition-all hover:scale-105 active:scale-100"
        :class="{ 'opacity-70 cursor-not-allowed': isCameraLoading }"
      >
        <svg v-if="!isCameraLoading"
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
          <polygon points="5 3 19 12 5 21 5 3"/>
        </svg>
        <svg v-else class="animate-spin"
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
          <path d="M21 12a9 9 0 1 1-6.219-8.56"/>
        </svg>
        {{ isCameraLoading ? '启动中...' : '启动摄像头' }}
      </button>

      <button
        v-else
        @click="stopCamera"
        class="flex items-center gap-2 px-8 py-3 bg-bilibili-card/90 backdrop-blur text-bilibili-text-primary rounded-full font-medium text-sm shadow-lg hover:bg-bilibili-hover transition-all hover:scale-105 active:scale-100 border border-bilibili-border"
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
          <rect width="4" height="16" x="6" y="4"/>
          <rect width="4" height="16" x="14" y="4"/>
        </svg>
        停止检测
      </button>
    </div>
  </div>
</template>
