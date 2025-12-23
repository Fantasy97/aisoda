<template>
  <div class="h-full flex flex-col">
    <div class="flex items-start space-x-4 mb-4">
      <div class="w-20 h-20 bg-gray-800 rounded flex items-center justify-center border border-gray-700 flex-shrink-0">
        <i class="fa-solid fa-server text-3xl text-gray-600"></i>
      </div>
      <div>
        <h2 class="text-lg font-bold text-white mb-1 truncate">{{ item?.title || 'TITLE' }}</h2>
        <p class="text-xs text-blue-400 mono-font mb-2">ASW S-G2 SERIES</p>
      </div>
    </div>
    <div class="grid grid-cols-2 gap-2 mono-font text-xs flex-1 content-start">
      <div class="bg-[#16191f] p-2 rounded border border-[#2d313a]">
        <span class="text-gray-500 block text-[10px] mb-0.5">Max. PV</span>
        <span class="text-white">4500 Wp</span>
      </div>
      <div class="bg-[#16191f] p-2 rounded border border-[#2d313a]">
        <span class="text-gray-500 block text-[10px] mb-0.5">Voltage</span>
        <span class="text-white">550V</span>
      </div>
      <div class="bg-[#16191f] p-2 rounded border border-[#2d313a]">
        <span class="text-gray-500 block text-[10px] mb-0.5">Current</span>
        <span class="text-white">16 A</span>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  item: {
    type: Object,
    default: () => ({})
  }
})
</script>

<style scoped>
.mono-font {
  font-family: 'JetBrains Mono', monospace;
}
</style>
