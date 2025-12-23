<template>
  <div class="h-full flex flex-col">
    <div class="text-sm font-bold text-gray-300 mb-2 border-b border-gray-700 pb-2">ROI 收益预估</div>
    <div class="space-y-2 mb-4">
      <div>
        <label class="text-[10px] text-gray-500 block mb-1">屋顶可用面积 (m²)</label>
        <input 
          type="number" 
          v-model="roofArea"
          class="w-full bg-[#111318] border border-gray-700 rounded px-2 py-1 text-xs text-white focus:border-blue-500 outline-none">
      </div>
    </div>
    <div class="flex-1 bg-[#16191f] rounded border border-[#2d313a] relative p-2 flex items-end justify-around pb-0">
      <div class="w-6 bg-blue-900 h-[20%] rounded-t"></div>
      <div class="w-6 bg-blue-800 h-[35%] rounded-t"></div>
      <div class="w-6 bg-blue-700 h-[50%] rounded-t"></div>
      <div class="w-6 bg-blue-600 h-[65%] rounded-t"></div>
      <div class="w-6 bg-blue-500 h-[80%] rounded-t"></div>
    </div>
    <div class="mt-2 text-center text-xs text-gray-400">
      回本: <span class="text-green-400 font-bold">3.2 年</span>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

defineProps({
  item: {
    type: Object,
    default: () => ({})
  }
})

const roofArea = ref(40)
</script>
