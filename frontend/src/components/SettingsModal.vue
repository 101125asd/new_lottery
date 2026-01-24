<template>
  <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm" @click.self="$emit('close')">
    <div class="glass-panel max-w-2xl w-full mx-4 max-h-[80vh] overflow-y-auto">
      <div class="flex justify-between items-center mb-6">
        <h2 class="text-2xl font-bold text-yellow-400">奖项配置</h2>
        <button @click="$emit('close')" class="text-gray-400 hover:text-white transition-colors">
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <div class="space-y-4">
        <div
          v-for="(prize, index) in localPrizes"
          :key="prize.id"
          class="prize-item glass-panel p-4"
        >
          <div class="grid grid-cols-4 gap-4 items-end">
            <div>
              <label class="block text-sm text-yellow-400/80 mb-1">奖项名称</label>
              <input
                v-model="prize.name"
                type="text"
                class="w-full px-3 py-2 bg-transparent border border-white/20 rounded text-white placeholder-white/40 focus:border-yellow-400 focus:outline-none focus:ring-1 focus:ring-yellow-400"
                placeholder="如：一等奖"
              />
            </div>
            <div>
              <label class="block text-sm text-yellow-400/80 mb-1">总数</label>
              <input
                v-model.number="prize.totalCount"
                type="number"
                min="1"
                class="w-full px-3 py-2 bg-transparent border border-white/20 rounded text-white placeholder-white/40 focus:border-yellow-400 focus:outline-none focus:ring-1 focus:ring-yellow-400"
              />
            </div>
            <div>
              <label class="block text-sm text-yellow-400/80 mb-1">每次抽取</label>
              <input
                v-model.number="prize.batchSize"
                type="number"
                min="1"
                class="w-full px-3 py-2 bg-transparent border border-white/20 rounded text-white placeholder-white/40 focus:border-yellow-400 focus:outline-none focus:ring-1 focus:ring-yellow-400"
              />
            </div>
            <div>
              <button
                @click="removePrize(index)"
                class="w-full px-4 py-2 bg-red-600/50 hover:bg-red-600 rounded text-white transition-colors"
              >
                删除
              </button>
            </div>
          </div>
        </div>

        <button
          @click="addPrize"
          class="w-full px-4 py-3 bg-yellow-400/20 hover:bg-yellow-400/30 border border-yellow-400/50 rounded text-yellow-400 font-bold transition-colors"
        >
          + 添加奖项
        </button>
      </div>

      <div class="mt-6 flex gap-4 justify-end">
        <button
          @click="$emit('close')"
          class="px-6 py-2 bg-gray-700/50 hover:bg-gray-700 rounded text-white transition-colors"
        >
          取消
        </button>
        <button
          @click="savePrizes"
          class="px-6 py-2 bg-yellow-400/80 hover:bg-yellow-400 rounded text-black font-bold transition-colors"
        >
          保存
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  prizes: {
    type: Array,
    required: true
  }
})

const emit = defineEmits(['close', 'update'])

const localPrizes = ref(JSON.parse(JSON.stringify(props.prizes)))

watch(() => props.prizes, (newPrizes) => {
  localPrizes.value = JSON.parse(JSON.stringify(newPrizes))
}, { deep: true })

const addPrize = () => {
  const newId = Math.max(...localPrizes.value.map(p => p.id), 0) + 1
  localPrizes.value.push({
    id: newId,
    name: '新奖项',
    totalCount: 10,
    batchSize: 1,
    remaining: 10
  })
}

const removePrize = (index) => {
  localPrizes.value.splice(index, 1)
}

const savePrizes = () => {
  // 确保每个奖项都有remaining字段
  const updatedPrizes = localPrizes.value.map(prize => ({
    ...prize,
    remaining: prize.remaining !== undefined ? prize.remaining : prize.totalCount
  }))
  emit('update', updatedPrizes)
  emit('close')
}
</script>

<style scoped>
.glass-panel {
  background: rgba(0, 0, 0, 0.8);
  backdrop-filter: blur(16px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
  padding: 24px;
}

.prize-item {
  background: rgba(0, 0, 0, 0.4);
  border: 1px solid rgba(250, 204, 21, 0.2);
}
</style>

