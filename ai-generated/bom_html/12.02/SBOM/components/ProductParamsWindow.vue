<template>
  <div class="h-full flex flex-col bg-[#0f1115] overflow-y-auto p-4">
    <div class="text-sm font-bold text-gray-300 mb-4 border-b border-[#2d313a] pb-2">
      <i class="fa-solid fa-sliders mr-2 text-blue-500"></i>产品参数配置
    </div>
    
    <!-- 产品型号选择 -->
    <div class="mb-6">
      <div class="text-xs font-bold text-gray-400 mb-3 flex items-center">
        <span class="mr-4 min-w-[80px]">产品型号</span>
        <label class="flex items-center text-xs text-gray-300 cursor-pointer">
          <input 
            type="radio" 
            name="model-radio"
            :checked="selectedModels.length === 0"
            @change="selectAllModels"
            class="mr-2 w-3 h-3 text-blue-600 bg-[#1e222b] border-[#2d313a] focus:ring-blue-500 focus:ring-2"
          />
          <span>全部</span>
        </label>
      </div>
      <div class="flex flex-wrap gap-2 ml-[80px]">
        <label 
          v-for="(model, index) in modelOptions" 
          :key="index"
          class="flex items-center px-3 py-1.5 border border-[#2d313a] rounded cursor-pointer hover:border-blue-500 hover:bg-[#1e222b] transition-colors"
          :class="{ 'border-blue-500 bg-[#1e222b]': selectedModels.includes(model.value) }">
          <input 
            type="checkbox" 
            :value="model.value"
            v-model="selectedModels"
            @change="handleModelChange"
            class="mr-2 w-3 h-3 text-blue-600 bg-[#1e222b] border-[#2d313a] focus:ring-blue-500 focus:ring-2"
          />
          <span class="text-xs text-gray-300">{{ model.label }}</span>
        </label>
      </div>
    </div>

    <!-- 筛选配置 -->
    <div class="mb-6">
      <div class="text-xs font-bold text-gray-400 mb-3 flex items-center">
        <span class="mr-4 min-w-[80px]">筛选配置</span>
      </div>
      <div class="flex flex-wrap gap-2 ml-[80px]">
        <label 
          v-for="(config, index) in configOptions" 
          :key="index"
          class="flex items-center px-3 py-1.5 border border-[#2d313a] rounded cursor-pointer hover:border-purple-500 hover:bg-[#1e222b] transition-colors"
          :class="{ 'border-purple-500 bg-[#1e222b]': selectedConfigs.includes(config.value) }">
          <input 
            type="checkbox" 
            :value="config.value"
            v-model="selectedConfigs"
            @change="handleConfigChange"
            class="mr-2 w-3 h-3 text-purple-600 bg-[#1e222b] border-[#2d313a] focus:ring-purple-500 focus:ring-2"
          />
          <span class="text-xs text-gray-300">{{ config.label }}</span>
        </label>
      </div>
    </div>

    <!-- 参数表格预览区域 -->
    <div class="flex-1 bg-[#16191f] rounded border border-[#2d313a] p-4 overflow-y-auto">
      <div class="text-xs text-gray-500 mb-3">参数配置预览</div>
      <div class="space-y-2">
        <div 
          v-for="(param, index) in filteredParams" 
          :key="index"
          class="bg-[#1e222b] p-3 rounded border border-[#2d313a]">
          <div class="text-xs font-bold text-gray-300 mb-2">{{ param.name }}</div>
          <div class="text-[10px] text-gray-500 space-y-1">
            <div v-for="(value, vIndex) in param.values" :key="vIndex" class="flex items-center">
              <span class="w-2 h-2 bg-blue-500 rounded-full mr-2"></span>
              <span>{{ value }}</span>
            </div>
          </div>
        </div>
        <div v-if="filteredParams.length === 0" class="text-center text-xs text-gray-600 py-8">
          暂无参数数据，请选择产品型号和配置
        </div>
      </div>
    </div>

    <!-- 操作按钮 -->
    <div class="mt-4 flex justify-end space-x-2">
      <button 
        @click="resetFilters"
        class="px-4 py-2 text-xs text-gray-400 hover:text-white border border-[#2d313a] rounded hover:bg-[#1e222b] transition-colors">
        重置
      </button>
      <button 
        @click="applyFilters"
        class="px-4 py-2 text-xs font-bold text-white bg-blue-600 hover:bg-blue-500 rounded transition-colors">
        应用筛选
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

defineProps({
  item: {
    type: Object,
    default: () => ({})
  }
})

// 产品型号选项
const modelOptions = ref([
  { label: 'ASW6000-S', value: 'ASW6000-S' },
  { label: 'ASW8000-S', value: 'ASW8000-S' },
  { label: 'ASW10000-S', value: 'ASW10000-S' },
  { label: 'ASW12000-S', value: 'ASW12000-S' }
])

// 筛选配置选项
const configOptions = ref([
  { label: '标配', value: 'standard' },
  { label: '选配', value: 'optional' }
])

// 选中的产品型号
const selectedModels = ref([])

// 选中的配置
const selectedConfigs = ref([])

// 模拟参数数据
const paramsData = ref([
  { name: '最大功率', values: ['6000W', '8000W', '10000W'], models: ['ASW6000-S', 'ASW8000-S', 'ASW10000-S'], config: 'standard' },
  { name: '输入电压', values: ['80V-550V'], models: ['ASW6000-S', 'ASW8000-S'], config: 'standard' },
  { name: 'WiFi模块', values: ['内置', '外置'], models: ['ASW10000-S', 'ASW12000-S'], config: 'optional' },
  { name: '显示屏', values: ['LCD', 'LED'], models: ['ASW6000-S'], config: 'optional' }
])

// 筛选后的参数
const filteredParams = computed(() => {
  let result = paramsData.value

  // 根据选中的型号筛选
  if (selectedModels.value.length > 0) {
    result = result.filter(param => 
      param.models.some(model => selectedModels.value.includes(model))
    )
  }

  // 根据选中的配置筛选
  if (selectedConfigs.value.length > 0) {
    result = result.filter(param => 
      selectedConfigs.value.includes(param.config)
    )
  }

  return result
})

// 选择全部型号
function selectAllModels() {
  selectedModels.value = []
}

// 处理型号变化
function handleModelChange() {
  console.log('Selected models:', selectedModels.value)
}

// 处理配置变化
function handleConfigChange() {
  console.log('Selected configs:', selectedConfigs.value)
}

// 重置筛选
function resetFilters() {
  selectedModels.value = []
  selectedConfigs.value = []
}

// 应用筛选
function applyFilters() {
  console.log('Applying filters:', {
    models: selectedModels.value,
    configs: selectedConfigs.value,
    filteredParams: filteredParams.value
  })
  alert(`已应用筛选：${selectedModels.value.length} 个型号，${selectedConfigs.value.length} 个配置类型`)
}
</script>

<style scoped>
/* 自定义复选框样式 */
input[type="checkbox"]:checked {
  background-color: #3b82f6;
  border-color: #3b82f6;
}

input[type="radio"]:checked {
  background-color: #3b82f6;
  border-color: #3b82f6;
}
</style>
