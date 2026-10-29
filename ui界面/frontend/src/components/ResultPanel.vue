<script setup lang="ts">
import type { Detection } from '../composables/useDetection'
import { getClassNameCN, getClassColor } from '../utils/classNames'

const props = defineProps<{
  detections: Detection[]
  counts: Record<string, number>
}>()

function getTotalCount() {
  return Object.values(props.counts).reduce((sum, count) => sum + count, 0)
}
</script>

<template>
  <div class="space-y-4">
    <div class="p-4 bg-bilibili-bg rounded-lg">
      <div class="flex items-center justify-between">
        <span class="text-sm text-bilibili-text-secondary">检测到</span>
        <span class="text-3xl font-bold text-bilibili-pink">{{ getTotalCount() }}</span>
        <span class="text-sm text-bilibili-text-secondary">个物体</span>
      </div>
    </div>

    <div v-if="Object.keys(counts).length > 0" class="space-y-3">
      <h4 class="text-xs font-medium text-bilibili-text-secondary uppercase tracking-wide">
        类别统计
      </h4>
      <div class="space-y-3">
        <div
          v-for="(count, className) in counts"
          :key="className"
          class="flex items-center gap-3"
        >
          <div
            class="w-1 h-10 rounded-full"
            :style="{ backgroundColor: getClassColor(className) }"
          ></div>
          <div class="flex-1">
            <div class="flex items-center justify-between mb-1.5">
              <span class="text-sm font-medium text-bilibili-text-primary">
                {{ getClassNameCN(className) }}
              </span>
              <span class="text-sm font-mono text-bilibili-text-secondary">{{ count }} 个</span>
            </div>
            <div class="h-1.5 bg-bilibili-bg rounded-full overflow-hidden">
              <div
                class="h-full rounded-full transition-all duration-500"
                :style="{
                  width: `${(count / Math.max(getTotalCount(), 1)) * 100}%`,
                  backgroundColor: getClassColor(className)
                }"
              ></div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-else class="text-center py-8">
      <div class="w-14 h-14 mx-auto mb-3 rounded-full bg-bilibili-bg flex items-center justify-center">
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="28"
          height="28"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="1.5"
          stroke-linecap="round"
          stroke-linejoin="round"
          class="text-bilibili-text-tertiary"
        >
          <circle cx="11" cy="11" r="8"/>
          <path d="m21 21-4.3-4.3"/>
        </svg>
      </div>
      <p class="text-sm text-bilibili-text-secondary">暂无检测结果</p>
      <p class="text-xs text-bilibili-text-tertiary mt-1">上传图片或开启摄像头开始检测</p>
    </div>

    <div v-if="detections.length > 0" class="pt-4 border-t border-bilibili-border">
      <h4 class="text-xs font-medium text-bilibili-text-secondary uppercase tracking-wide mb-3">
        检测详情
      </h4>
      <div class="space-y-2 max-h-56 overflow-y-auto">
        <div
          v-for="(det, index) in detections"
          :key="index"
          class="flex items-center justify-between py-2 px-3 bg-bilibili-bg rounded-lg"
        >
          <div class="flex items-center gap-2">
            <div
              class="w-2 h-2 rounded-full"
              :style="{ backgroundColor: getClassColor(det.class) }"
            ></div>
            <span class="text-sm text-bilibili-text-primary">
              {{ getClassNameCN(det.class) }}
            </span>
          </div>
          <span class="text-sm font-mono text-bilibili-pink">
            {{ (det.confidence * 100).toFixed(1) }}%
          </span>
        </div>
      </div>
    </div>
  </div>
</template>
