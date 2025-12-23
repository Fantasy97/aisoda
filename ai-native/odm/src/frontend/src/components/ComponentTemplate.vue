<template>
  <div class="h-full flex flex-col">
    <!-- 头部区域 -->
    <div class="mb-4 pb-4 border-b border-gray-200">
      <h2 class="text-lg font-bold text-gray-800 mb-2">{{ item?.title || '组件标题' }}</h2>
      <p class="text-xs text-gray-500">组件描述信息</p>
    </div>
    
    <!-- 主要内容区域 -->
    <div class="flex-1 overflow-y-auto">
      <!-- 加载状态 -->
      <div v-if="loading" class="flex items-center justify-center h-full">
        <i class="fa-solid fa-spinner fa-spin text-gray-400 text-2xl"></i>
        <span class="ml-2 text-sm text-gray-500">加载中...</span>
      </div>
      
      <!-- 空状态 -->
      <div v-else-if="items.length === 0" class="flex flex-col items-center justify-center h-full text-gray-400">
        <i class="fa-solid fa-inbox text-4xl mb-2"></i>
        <p class="text-sm">暂无数据</p>
        <button 
          @click="handleAdd"
          class="mt-4 px-4 py-2 bg-primary-600 text-white text-xs rounded hover:bg-primary-700 transition-colors">
          添加数据
        </button>
      </div>
      
      <!-- 内容展示 -->
      <div v-else class="space-y-4">
        <!-- 示例：列表展示 -->
        <div 
          v-for="item in items" 
          :key="item.id"
          class="p-4 bg-white border border-gray-200 rounded-lg hover:border-gray-300 transition-colors">
          <div class="flex items-center justify-between">
            <div>
              <h3 class="text-sm font-semibold text-gray-800">{{ item.name }}</h3>
              <p class="text-xs text-gray-500 mt-1">{{ item.description }}</p>
            </div>
            <div class="flex items-center gap-2">
              <button 
                @click="handleEdit(item)"
                class="p-2 text-gray-400 hover:text-blue-600 transition-colors">
                <i class="fa-solid fa-edit"></i>
              </button>
              <button 
                @click="handleDelete(item)"
                class="p-2 text-gray-400 hover:text-red-600 transition-colors">
                <i class="fa-solid fa-trash"></i>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 底部操作区 -->
    <div class="mt-4 pt-4 border-t border-gray-200 flex items-center justify-end gap-2">
      <button 
        @click="handleCancel"
        class="px-4 py-2 text-sm text-gray-700 bg-gray-100 rounded hover:bg-gray-200 transition-colors">
        取消
      </button>
      <button 
        @click="handleSave"
        class="px-4 py-2 text-sm bg-primary-600 text-white rounded hover:bg-primary-700 transition-colors">
        保存
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'

// Props
const props = defineProps({
  item: {
    type: Object,
    default: () => ({})
  }
})

// 状态管理
const loading = ref(false)
const items = ref([])

// 计算属性
const componentId = computed(() => props.item?.originalId || '')

// 方法
function handleAdd() {
  // 添加逻辑
  console.log('添加新项')
}

function handleEdit(item) {
  // 编辑逻辑
  console.log('编辑项:', item)
}

function handleDelete(item) {
  // 删除逻辑
  console.log('删除项:', item)
}

function handleSave() {
  // 保存逻辑
  console.log('保存数据')
}

function handleCancel() {
  // 取消逻辑
  console.log('取消操作')
}

// 数据加载
async function loadData() {
  loading.value = true
  try {
    // 根据 componentId 加载不同数据
    // const response = await fetch(`/api/data/${componentId}`)
    // const data = await response.json()
    // items.value = data
    
    // 模拟数据
    setTimeout(() => {
      items.value = [
        { id: 1, name: '示例项1', description: '这是示例数据' },
        { id: 2, name: '示例项2', description: '这是示例数据' }
      ]
      loading.value = false
    }, 500)
  } catch (error) {
    console.error('加载数据失败:', error)
    loading.value = false
  }
}

// 生命周期
onMounted(() => {
  loadData()
})
</script>

<style scoped>
/* 组件特定样式 */
</style>

