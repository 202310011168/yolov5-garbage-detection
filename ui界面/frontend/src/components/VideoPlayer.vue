<script setup lang="ts">
import { ref, watch, onUnmounted, nextTick, computed } from 'vue'
import type { Detection } from '../composables/useDetection'
import { useDetection } from '../composables/useDetection'
import { getClassNameCN, getClassColor } from '../utils/classNames'

const props = defineProps<{
  videoSrc: string
  annotatedSrc?: string | null
  currentModel: string
  confidence: number
  iou: number
  detectInterval?: number
}>()

const emit = defineEmits<{
  (e: 'detections', detections: Detection[], counts: Record<string, number>): void
  (e: 'loaded'): void
  (e: 'upload', file: File): void
}>()

const { detectBase64 } = useDetection()

const videoRef = ref<HTMLVideoElement | null>(null)
const overlayCanvasRef = ref<HTMLCanvasElement | null>(null)
const containerRef = ref<HTMLDivElement | null>(null)
const isPlaying = ref(false)
const isDetecting = ref(false)
const detectTimer = ref<number | null>(null)
const stableDetections = ref<Detection[]>([])
const detectionHistory: Detection[][] = []
const HISTORY_SIZE = 2
const isVideoLoaded = ref(false)
const isDragOver = ref(false)

const hasAnnotations = computed(() => !!props.annotatedSrc)

function onVideoLoaded() {
  isVideoLoaded.value = true
  nextTick(() => {
    initCanvas()
  })
  emit('loaded')
}

function onVideoDataLoaded() {
  if (!isVideoLoaded.value) {
    isVideoLoaded.value = true
    nextTick(() => {
      initCanvas()
    })
  }
}

function onVideoPlay() {
  if (!isVideoLoaded.value) {
    isVideoLoaded.value = true
    nextTick(() => {
      initCanvas()
    })
  }
  isPlaying.value = true
  startDetectionLoop()
}

function initCanvas() {
  if (!overlayCanvasRef.value || !containerRef.value || !videoRef.value) return

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

function stabilizeDetections(newDetections: Detection[]): Detection[] {
  detectionHistory.push([...newDetections])
  if (detectionHistory.length > HISTORY_SIZE) {
    detectionHistory.shift()
  }

  if (detectionHistory.length < 2) {
    return newDetections
  }

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

async function detectCurrentFrame() {
  if (isDetecting.value || !videoRef.value) return
  if (videoRef.value.paused || videoRef.value.ended) return

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

    tempCtx.drawImage(videoEl, 0, 0, videoWidth, videoHeight)
    const imageData = tempCanvas.toDataURL('image/jpeg', 0.95).split(',')[1]

    const result = await detectBase64(
      imageData,
      props.currentModel,
      props.confidence,
      props.iou
    )

    if (result.success) {
      const newDetections = result.detections || []
      stableDetections.value = stabilizeDetections(newDetections)

      const counts: Record<string, number> = {}
      for (const det of stableDetections.value) {
        counts[det.class] = (counts[det.class] || 0) + 1
      }

      initCanvas()
      drawDetections(stableDetections.value)

      emit('detections', stableDetections.value, counts)
    }
  } catch (err) {
    console.error('Video frame detection failed:', err)
  } finally {
    isDetecting.value = false
  }
}

function drawDetections(detections: Detection[]) {
  if (!overlayCanvasRef.value) return

  const canvas = overlayCanvasRef.value
  const ctx = canvas.getContext('2d')
  if (!ctx) return

  const rect = getVideoDisplayRect()
  if (!rect) return

  const { scale, offsetX, offsetY } = rect

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

function onPlay() {
  onVideoPlay()
}

function onPause() {
  isPlaying.value = false
  stopDetectionLoop()
}

function onEnded() {
  isPlaying.value = false
  stopDetectionLoop()
}

function startDetectionLoop() {
  stopDetectionLoop()
  if (hasAnnotations.value) return
  const interval = props.detectInterval || 300
  detectTimer.value = window.setInterval(detectCurrentFrame, interval)
}

function stopDetectionLoop() {
  if (detectTimer.value) {
    clearInterval(detectTimer.value)
    detectTimer.value = null
  }
}

function handleResize() {
  if (isVideoLoaded.value) {
    initCanvas()
    if (stableDetections.value.length > 0) {
      drawDetections(stableDetections.value)
    }
  }
}

// 拖放处理
function handleDragOver(e: DragEvent) {
  e.preventDefault()
  isDragOver.value = true
}

function handleDragLeave(e: DragEvent) {
  e.preventDefault()
  isDragOver.value = false
}

function handleDrop(e: DragEvent) {
  e.preventDefault()
  isDragOver.value = false

  const files = e.dataTransfer?.files
  if (files && files.length > 0) {
    const file = files[0]
    if (file.type.startsWith('video/')) {
      emit('upload', file)
    }
  }
}

watch(() => props.currentModel, () => {
  detectionHistory.length = 0
  stableDetections.value = []
})

watch(() => props.confidence, () => {
  detectionHistory.length = 0
  stableDetections.value = []
})

watch(() => props.iou, () => {
  detectionHistory.length = 0
  stableDetections.value = []
})

watch(() => props.videoSrc, () => {
  detectionHistory.length = 0
  stableDetections.value = []
  isVideoLoaded.value = false
  stopDetectionLoop()
})

watch(() => props.annotatedSrc, () => {
  if (props.annotatedSrc) {
    stopDetectionLoop()
    stableDetections.value = []
    detectionHistory.length = 0
  }
})

watch(hasAnnotations, (has) => {
  if (has) {
    stopDetectionLoop()
  } else if (isPlaying.value) {
    startDetectionLoop()
  }
})

onUnmounted(() => {
  stopDetectionLoop()
  window.removeEventListener('resize', handleResize)
})

nextTick(() => {
  window.addEventListener('resize', handleResize)
})

defineExpose({
  stableDetections,
  isPlaying,
})
</script>

<template>
  <div
    ref="containerRef"
    class="relative w-full h-full bg-black overflow-hidden"
    @dragover="handleDragOver"
    @dragleave="handleDragLeave"
    @drop="handleDrop"
  >
    <div class="absolute inset-0 flex items-center justify-center z-0">
      <video
        ref="videoRef"
        :src="annotatedSrc || videoSrc"
        class="max-w-full max-h-full object-contain"
        controls
        playsinline
        @loadedmetadata="onVideoLoaded"
        @loadeddata="onVideoDataLoaded"
        @play="onPlay"
        @pause="onPause"
        @ended="onEnded"
      ></video>
    </div>

    <canvas
      v-if="!hasAnnotations"
      ref="overlayCanvasRef"
      class="absolute inset-0 w-full h-full pointer-events-none z-10"
    ></canvas>

    <!-- 加载中 -->
    <div
      v-if="!isVideoLoaded && videoSrc"
      class="absolute inset-0 flex items-center justify-center"
    >
      <div class="flex flex-col items-center gap-3">
        <div class="w-10 h-10 border-3 border-bilibili-pink border-t-transparent rounded-full animate-spin"></div>
        <span class="text-sm text-bilibili-text-secondary">视频加载中...</span>
      </div>
    </div>

    <!-- 拖放提示 -->
    <div
      v-if="isDragOver"
      class="absolute inset-0 flex items-center justify-center bg-bilibili-pink/10 backdrop-blur-sm border-2 border-dashed border-bilibili-pink pointer-events-none z-10"
    >
      <div class="flex flex-col items-center gap-2">
        <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="text-bilibili-pink">
          <path d="M12 3v12"/>
          <path d="m8 7 4-4 4 4"/>
          <path d="M5 21h14"/>
        </svg>
        <p class="text-base font-medium text-bilibili-pink">松开上传视频</p>
      </div>
    </div>

    <!-- 空状态 -->
    <div
      v-if="!videoSrc"
      class="absolute inset-0 flex flex-col items-center justify-center gap-3 pointer-events-none"
    >
      <div class="w-16 h-16 rounded-full bg-bilibili-card flex items-center justify-center">
        <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="text-bilibili-text-tertiary">
          <polygon points="23 7 16 12 23 17 23 7"/>
          <rect x="1" y="5" width="15" height="14" rx="2" ry="2"/>
        </svg>
      </div>
      <p class="text-sm text-bilibili-text-secondary">拖拽视频文件到此处</p>
      <p class="text-xs text-bilibili-text-tertiary">或从右侧上传</p>
    </div>

    <!-- 标注视频标签 -->
    <div
      v-if="hasAnnotations && isVideoLoaded"
      class="absolute top-4 left-4 px-3 py-1 bg-bilibili-pink/90 backdrop-blur rounded-full text-xs text-white font-medium z-10"
    >
      标注视频
    </div>

    <!-- 实时检测中 -->
    <div
      v-if="!hasAnnotations && isVideoLoaded && isPlaying"
      class="absolute top-4 right-4 flex items-center gap-2 px-3 py-1.5 bg-black/50 backdrop-blur rounded-full z-10"
    >
      <div class="w-2 h-2 rounded-full bg-bilibili-pink animate-pulse"></div>
      <span class="text-xs text-white">实时检测中</span>
    </div>
  </div>
</template>
