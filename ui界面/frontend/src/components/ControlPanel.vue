<script setup lang="ts">
import { ref, watch } from 'vue'
import type { Model } from '../composables/useDetection'

const props = defineProps<{
  models: Model[]
  currentModel: string
  confidence: number
  iou: number
}>()

const emit = defineEmits<{
  (e: 'update:currentModel', value: string): void
  (e: 'update:confidence', value: number): void
  (e: 'update:iou', value: number): void
}>()

const localModel = ref(props.currentModel)
const localConf = ref(props.confidence)
const localIou = ref(props.iou)

watch(() => props.currentModel, (val) => { localModel.value = val })
watch(() => props.confidence, (val) => { localConf.value = val })
watch(() => props.iou, (val) => { localIou.value = val })

function onModelChange() {
  emit('update:currentModel', localModel.value)
}

function onConfChange() {
  emit('update:confidence', localConf.value)
}

function onIouChange() {
  emit('update:iou', localIou.value)
}

function getModelDisplayName(model: Model) {
  return `${model.name} (${model.size})`
}
</script>

<template>
  <div class="p-4 space-y-5">
    <div class="space-y-2">
      <label class="text-xs font-medium text-bilibili-text-secondary uppercase tracking-wide">
        模型选择
      </label>
      <select
        v-model="localModel"
        @change="onModelChange"
        class="w-full px-3 py-2.5 bg-bilibili-bg border border-bilibili-border rounded-lg text-sm text-bilibili-text-primary focus:ring-2 focus:ring-bilibili-pink focus:border-bilibili-pink focus:outline-none transition-all cursor-pointer"
      >
        <option v-for="model in models" :key="model.id" :value="model.id">
          {{ getModelDisplayName(model) }}
        </option>
      </select>
    </div>

    <div class="space-y-2">
      <div class="flex items-center justify-between">
        <label class="text-xs font-medium text-bilibili-text-secondary uppercase tracking-wide">
          置信度阈值
        </label>
        <span class="text-sm font-mono text-bilibili-pink">{{ localConf.toFixed(2) }}</span>
      </div>
      <input
        type="range"
        v-model.number="localConf"
        @input="onConfChange"
        min="0.1"
        max="1.0"
        step="0.05"
        class="w-full h-1.5 bg-bilibili-bg rounded-full appearance-none cursor-pointer accent-bilibili-pink"
      />
      <div class="flex justify-between text-xs text-bilibili-text-tertiary">
        <span>0.1</span>
        <span>1.0</span>
      </div>
    </div>

    <div class="space-y-2">
      <div class="flex items-center justify-between">
        <label class="text-xs font-medium text-bilibili-text-secondary uppercase tracking-wide">
          IoU 阈值
        </label>
        <span class="text-sm font-mono text-bilibili-pink">{{ localIou.toFixed(2) }}</span>
      </div>
      <input
        type="range"
        v-model.number="localIou"
        @input="onIouChange"
        min="0.1"
        max="1.0"
        step="0.05"
        class="w-full h-1.5 bg-bilibili-bg rounded-full appearance-none cursor-pointer accent-bilibili-pink"
      />
      <div class="flex justify-between text-xs text-bilibili-text-tertiary">
        <span>0.1</span>
        <span>1.0</span>
      </div>
    </div>

    <div class="pt-3 border-t border-bilibili-border">
      <div class="text-xs text-bilibili-text-tertiary space-y-1">
        <p>• 置信度越高，检测越严格</p>
        <p>• IoU 越高，重叠框保留越多</p>
      </div>
    </div>
  </div>
</template>
