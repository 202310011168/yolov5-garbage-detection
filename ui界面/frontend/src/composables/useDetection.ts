import { ref } from 'vue'

// API 基础 URL（直接写死后端地址，不依赖代理，更可靠）
const API_BASE = 'http://localhost:5000/api'

// 检测结果接口
export interface Detection {
  class: string
  confidence: number
  bbox: [number, number, number, number]
}

export interface DetectionResponse {
  success: boolean
  detections: Detection[]
  annotated_image: string
  counts: Record<string, number>
}

export interface Model {
  id: string
  name: string
  size: string
}

export interface VideoDetectionResponse {
  success: boolean
  video_url: string
  total_frames: number
  processed_frames: number
  fps: number
  duration: number
  counts: Record<string, number>
  total_detected: number
  frame_results: Array<{
    frame: number
    time: number
    detections: Detection[]
  }>
}

export function useDetection() {
  const isLoading = ref(false)
  const error = ref<string | null>(null)
  const lastResult = ref<DetectionResponse | null>(null)

  // 获取可用模型列表
  async function getModels(): Promise<Model[]> {
    try {
      const response = await fetch(`${API_BASE}/models`)
      const data = await response.json()
      return data.models || []
    } catch (err) {
      console.error('获取模型列表失败:', err)
      return []
    }
  }

  // 检测图片（文件上传）
  async function detectImage(
    imageFile: File,
    model: string = 'yolov5s',
    conf: number = 0.5,
    iou: number = 0.45
  ): Promise<DetectionResponse> {
    isLoading.value = true
    error.value = null

    try {
      const formData = new FormData()
      formData.append('image', imageFile)
      formData.append('model', model)
      formData.append('conf', conf.toString())
      formData.append('iou', iou.toString())

      const response = await fetch(`${API_BASE}/detect`, {
        method: 'POST',
        body: formData,
      })

      const data = await response.json()
      lastResult.value = data
      return data
    } catch (err) {
      error.value = err instanceof Error ? err.message : '检测失败'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  // 检测图片（base64）
  async function detectBase64(
    imageData: string,
    model: string = 'yolov5s',
    conf: number = 0.5,
    iou: number = 0.45
  ): Promise<DetectionResponse> {
    isLoading.value = true
    error.value = null

    try {
      const response = await fetch(`${API_BASE}/detect_base64`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          image: imageData,
          model,
          conf,
          iou,
        }),
      })

      const data = await response.json()
      lastResult.value = data
      return data
    } catch (err) {
      error.value = err instanceof Error ? err.message : '检测失败'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  // 下载标注图片
  function downloadImage(dataUrl: string, filename: string = 'detected.jpg') {
    const link = document.createElement('a')
    link.href = dataUrl
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  // 检测视频
  async function detectVideo(
    videoFile: File,
    model: string = 'yolov5s',
    conf: number = 0.6,
    iou: number = 0.45,
    frameInterval: number = 10
  ): Promise<VideoDetectionResponse> {
    isLoading.value = true
    error.value = null

    try {
      const formData = new FormData()
      formData.append('video', videoFile)
      formData.append('model', model)
      formData.append('conf', conf.toString())
      formData.append('iou', iou.toString())
      formData.append('frame_interval', frameInterval.toString())

      const response = await fetch(`${API_BASE}/detect_video`, {
        method: 'POST',
        body: formData,
      })

      const data = await response.json()
      return data
    } catch (err) {
      error.value = err instanceof Error ? err.message : '检测失败'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  // 获取完整下载 URL
  function getDownloadUrl(path: string) {
    if (path.startsWith('http')) return path
    return `http://localhost:5000${path}`
  }

  return {
    isLoading,
    error,
    lastResult,
    getModels,
    detectImage,
    detectBase64,
    detectVideo,
    downloadImage,
    getDownloadUrl,
  }
}
