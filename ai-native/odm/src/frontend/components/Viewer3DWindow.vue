<template>
  <div class="h-full flex flex-col">
    <div class="flex items-center justify-between text-sm font-bold text-gray-300 mb-2 border-b border-gray-700 pb-2">
      <span>
        <i class="fa-solid fa-cube mr-2 text-orange-500"></i>3D 模型
      </span>
      <span class="text-[10px] text-gray-500 bg-gray-800 px-1.5 rounded">WebGL</span>
    </div>
    <div class="flex-1 bg-[#0f1115] relative overflow-hidden rounded border border-gray-800 group grid-bg flex items-center justify-center">
      <div class="w-32 h-40 bg-gradient-to-br from-gray-700 to-gray-800 rounded-lg shadow-2xl relative border border-gray-600 flex flex-col items-center justify-center">
        <div class="absolute top-4 text-[8px] font-bold text-gray-400">ASW</div>
        <div class="w-20 h-8 bg-black/50 rounded mt-2 flex items-center justify-center border border-gray-600/50">
          <span class="text-[8px] text-green-400 font-mono">5.0 kW</span>
        </div>
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
.grid-bg {
  background-image: linear-gradient(rgba(255, 255, 255, 0.05) 1px, transparent 1px),
  linear-gradient(90deg, rgba(255, 255, 255, 0.05) 1px, transparent 1px);
  background-size: 20px 20px;
}
</style>
