<template>
  <div class="h-full flex flex-col bg-[#0f1115]">
    <div class="text-sm font-bold text-gray-300 px-1 py-2 border-b border-[#2d313a] flex items-center justify-between">
      <div class="flex items-center">
        <i class="fa-solid fa-wand-magic-sparkles mr-2 text-purple-500"></i> AI 智能导购 (Full)
      </div>
    </div>
    <div class="flex-1 flex overflow-hidden">
      <div class="flex-1 flex flex-col border-r border-[#2d313a]">
        <div class="flex-1 overflow-y-auto p-4 space-y-4">
          <div class="flex items-start space-x-3">
            <div class="w-8 h-8 rounded-full bg-purple-900/50 flex items-center justify-center border border-purple-700 flex-shrink-0">
              <i class="fa-solid fa-robot text-purple-300 text-xs"></i>
            </div>
            <div class="bg-[#1e222b] p-3 rounded-lg rounded-tl-none border border-[#2d313a] text-xs text-gray-300 max-w-[80%]">
              我是选型助手，请告诉我您的需求。
            </div>
          </div>
        </div>
        <div class="p-3 border-t border-[#2d313a] bg-[#16191f]">
          <div class="relative">
            <textarea 
              v-model="userInput"
              class="w-full bg-[#0f1115] border border-[#2d313a] rounded-lg p-3 pr-10 text-xs text-white focus:border-purple-500 outline-none resize-none h-12" 
              placeholder="输入需求..."></textarea>
          </div>
        </div>
      </div>
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

const userInput = ref('')
</script>
