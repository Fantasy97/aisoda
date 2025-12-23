<template>
  <div class="odm-select-window w-full h-full flex flex-col bg-white">
    <!-- 搜索和操作栏 -->
    <div class="search-action-bar">
      <div class="search-box">
        <svg class="search-icon" width="20" height="20" viewBox="0 0 16 16" fill="none">
          <circle cx="6.5" cy="6.5" r="4.5" stroke="currentColor" stroke-width="1.5"/>
          <path d="M14 14l-3.5-3.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
        </svg>
        <input 
          v-model="searchQuery"
          type="text"
          class="search-input"
          placeholder="搜索历史ODM需求..."
        />
      </div>
      <div class="action-buttons">
        <button class="btn btn-secondary" @click="toggleFilterPanel">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <path d="M2 4h12M4 8h8M6 12h4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
          </svg>
          筛选
        </button>
        <button class="btn btn-primary" @click="$emit('create')">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <path d="M8 2v12M2 8h12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          </svg>
          新建ODM
        </button>
      </div>
    </div>

    <!-- 筛选标签栏 -->
    <div class="filter-bar px-6 py-3 border-b border-gray-200 bg-white">
      <div class="flex items-center gap-4">
        <span class="filter-label text-sm text-gray-600 font-medium">状态:</span>
        <div class="filter-tags flex items-center gap-2 flex-wrap">
          <div 
            v-for="filter in filters"
            :key="filter.value"
            class="filter-tag px-3 py-1.5 text-xs rounded-md cursor-pointer transition-all"
            :class="activeFilter === filter.value ? 'filter-tag-active' : 'filter-tag-inactive'"
            @click="activeFilter = filter.value"
          >
            {{ filter.label }}
          </div>
        </div>
      </div>
    </div>

    <!-- 卡片列表容器 -->
    <div class="card-list-container">
      <div class="card-grid">
        <!-- 空状态 -->
        <div 
          v-if="filteredOdms.length === 0 && !isLoading"
          class="empty-state"
          style="grid-column: 1 / -1; text-align: center; padding: 60px;"
        >
          <div style="font-size: 48px; margin-bottom: 16px; opacity: 0.3;">📭</div>
          <div style="color: #999; font-size: 14px;">
            {{ searchQuery ? '未找到匹配的ODM需求' : '暂无历史ODM需求' }}
          </div>
          <p v-if="!searchQuery" class="text-xs mt-2 text-gray-400">点击上方按钮创建新的ODM项目</p>
        </div>

        <!-- 加载状态 -->
        <div 
          v-if="isLoading"
          class="loading-indicator"
          style="grid-column: 1 / -1; text-align: center; padding: 40px; color: #999;"
        >
          <div style="margin-bottom: 12px;">加载中...</div>
        </div>

        <!-- 卡片列表 -->
        <div
          v-for="odm in filteredOdms"
          v-else
          :key="odm.id"
          class="design-card"
          @click="selectOdm(odm)"
        >
          <!-- 卡片头部 -->
          <div class="card-header">
            <div class="card-header-top">
              <div class="card-title">{{ odm.name }}</div>
              <span class="card-status" :class="getStatusClass(odm)">
                {{ getStatusLabel(odm) }}
              </span>
            </div>
            <div class="card-date">{{ formatDate(odm.createDate) }}</div>
          </div>

          <!-- 卡片描述 -->
          <div class="card-desc">{{ odm.description }}</div>

          <!-- 卡片元信息 -->
          <div class="card-meta">
            <div class="card-author">
              <div class="author-avatar">{{ odm.code.substring(0, 2).toUpperCase() }}</div>
              <span>{{ odm.code }}</span>
            </div>
            <div class="card-item-count">{{ odm.itemCount || 0 }} 项</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

// Props
const props = defineProps({
  odms: {
    type: Array,
    default: () => []
  }
})

// Emits
const emit = defineEmits(['select', 'create'])

// 搜索查询
const searchQuery = ref('')

// 筛选状态
const activeFilter = ref('all')
const isLoading = ref(false)
const showFilterPanel = ref(false)

// 筛选选项
const filters = [
  { label: '全部', value: 'all' },
  { label: '进行中', value: 'active' },
  { label: '已完成', value: 'completed' },
  { label: '已归档', value: 'archived' }
]

// 过滤后的ODM列表
const filteredOdms = computed(() => {
  let result = props.odms
  
  // 应用状态筛选
  if (activeFilter.value !== 'all') {
    // 这里可以根据实际的状态字段进行筛选
    // 暂时根据 itemCount 模拟状态：有项目的为进行中，无项目的为已完成
    if (activeFilter.value === 'active') {
      result = result.filter(odm => (odm.itemCount || 0) > 0)
    } else if (activeFilter.value === 'completed') {
      result = result.filter(odm => (odm.itemCount || 0) === 0)
    }
  }
  
  // 应用搜索查询
  if (searchQuery.value.trim()) {
    const query = searchQuery.value.toLowerCase()
    result = result.filter(odm => 
      odm.name.toLowerCase().includes(query) ||
      odm.code.toLowerCase().includes(query) ||
      (odm.description && odm.description.toLowerCase().includes(query))
    )
  }
  
  return result
})

// 选择ODM
function selectOdm(odm) {
  emit('select', odm)
}

// 切换筛选面板
function toggleFilterPanel() {
  showFilterPanel.value = !showFilterPanel.value
}

// 格式化日期
function formatDate(date) {
  if (!date) return '未知'
  
  const d = new Date(date)
  const now = new Date()
  const diffTime = Math.abs(now - d)
  const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24))
  
  if (diffDays === 0) {
    return '今天'
  } else if (diffDays === 1) {
    return '昨天'
  } else if (diffDays < 7) {
    return `${diffDays}天前`
  } else if (diffDays < 30) {
    return `${Math.floor(diffDays / 7)}周前`
  } else {
    return d.toLocaleDateString('zh-CN', { year: 'numeric', month: 'short', day: 'numeric' })
  }
}

// 获取状态类名
function getStatusClass(odm) {
  const itemCount = odm.itemCount || 0
  if (itemCount > 0) {
    return 'status-review' // 进行中
  } else {
    return 'status-approved' // 已完成
  }
}

// 获取状态标签
function getStatusLabel(odm) {
  const itemCount = odm.itemCount || 0
  if (itemCount > 0) {
    return '进行中'
  } else {
    return '已完成'
  }
}
</script>

<style scoped>
.odm-select-window {
  font-family: 'Inter', sans-serif;
}

/* 搜索和操作栏样式 */
.search-action-bar {
  background: white;
  border-radius: 12px;
  padding: 20px;
  margin: 20px 32px 0;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  position: relative;
  z-index: 10;
  display: flex;
  gap: 12px;
  align-items: center;
  flex-shrink: 0;
}

.search-box {
  flex: 1;
  position: relative;
}

.search-input {
  width: 100%;
  padding: 12px 16px 12px 44px;
  border: 2px solid #e8e8e8;
  border-radius: 8px;
  font-size: 14px;
  transition: all 0.3s;
  outline: none;
}

.search-input:focus {
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.search-icon {
  position: absolute;
  left: 16px;
  top: 50%;
  transform: translateY(-50%);
  color: #999;
  pointer-events: none;
}

.action-buttons {
  display: flex;
  gap: 8px;
}

.btn {
  padding: 12px 20px;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.3s;
  display: flex;
  align-items: center;
  gap: 6px;
  white-space: nowrap;
}

.btn-primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.btn-secondary {
  background: white;
  color: #667eea;
  border: 2px solid #667eea;
}

.btn-secondary:hover {
  background: rgba(102, 126, 234, 0.1);
}

/* 筛选标签栏样式 */
.filter-bar {
  flex-shrink: 0;
}

.filter-label {
  white-space: nowrap;
}

.filter-tags {
  flex: 1;
}

.filter-tag {
  user-select: none;
}

.filter-tag-active {
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
  color: #667eea;
  font-weight: 600;
  border: 1px solid rgba(102, 126, 234, 0.2);
}

.filter-tag-inactive {
  background: #f9fafb;
  color: #6b7280;
  border: 1px solid #e5e7eb;
}

.filter-tag-inactive:hover {
  background: #f3f4f6;
  border-color: #d1d5db;
  color: #374151;
}

/* 卡片列表容器 */
.card-list-container {
  background: #f9fafb;
  flex: 1;
  overflow-y: auto;
  padding: 0 32px 32px;
  min-height: 0; /* 确保 flex 子元素可以正确滚动 */
}

.card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 20px;
  padding-top: 20px;
  padding-bottom: 20px;
}

/* 设计卡片样式 */
.design-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  transition: all 0.3s;
  cursor: pointer;
  position: relative;
  overflow: hidden;
}

.design-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  transform: scaleX(0);
  transition: transform 0.3s;
}

.design-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}

.design-card:hover::before {
  transform: scaleX(1);
}

.card-header {
  margin-bottom: 12px;
}

.card-header-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.card-status {
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
  white-space: nowrap;
  flex-shrink: 0;
}

.card-date {
  font-size: 12px;
  color: #999;
  white-space: nowrap;
}

.status-draft {
  background: #fff7e6;
  color: #fa8c16;
}

.status-review {
  background: #e6f7ff;
  color: #1890ff;
}

.status-approved {
  background: #f6ffed;
  color: #52c41a;
}

.status-rejected {
  background: #fff1f0;
  color: #ff4d4f;
}

.status-pushed {
  background: #e6f7ff;
  color: #1890ff;
}

.status-failed {
  background: #fff1f0;
  color: #ff4d4f;
}

.status-discarded {
  background: #f5f5f5;
  color: #8c8c8c;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  line-height: 1.4;
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.card-desc {
  font-size: 13px;
  color: #999;
  margin-bottom: 16px;
  line-height: 1.6;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.card-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 12px;
  color: #999;
  padding-top: 12px;
  border-top: 1px solid #f0f0f0;
}

.card-author {
  display: flex;
  align-items: center;
  gap: 6px;
}

.author-avatar {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 11px;
  font-weight: 600;
  flex-shrink: 0;
}

.card-item-count {
  white-space: nowrap;
}

/* 滚动条样式 */
.odm-select-window :deep(::-webkit-scrollbar) {
  width: 8px;
  height: 8px;
}

.odm-select-window :deep(::-webkit-scrollbar-track) {
  background: #f5f5f7;
  border-radius: 4px;
}

.odm-select-window :deep(::-webkit-scrollbar-thumb) {
  background: #d1d5db;
  border-radius: 4px;
}

.odm-select-window :deep(::-webkit-scrollbar-thumb:hover) {
  background: #9ca3af;
}
</style>
