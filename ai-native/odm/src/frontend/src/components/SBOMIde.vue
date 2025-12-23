<template>
  <div class="sbom-ide h-screen flex flex-col">
    <!-- 顶部标题栏 -->
    <div class="h-10 bg-white/95 backdrop-blur-sm flex items-center border-b border-gray-200 px-3 space-x-3 z-50 relative shadow-sm flex-shrink-0" id="conversation-bar">
      <!-- 左侧 Logo -->
      <div class="flex items-center gap-4">
        <div class="text-lg font-bold bg-gradient-primary bg-clip-text text-transparent select-none whitespace-nowrap">
          🎨 超级BOM
        </div>
      </div>
      
      <!-- 中间 AI 输入框 -->
      <div class="flex-1 relative" id="ai-command-center" ref="aiCommandCenter">
        <div class="relative z-50 bg-gray-50 rounded-md border border-gray-300 transition-all duration-200" 
             :class="{ 'expanded-input border-primary-500 ring-1 ring-primary-500': isAiPanelOpen }"
             id="ai-input-wrapper">
          <div class="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none">
            <i class="fa-solid fa-wand-magic-sparkles text-primary-500 text-xs animate-pulse"></i>
          </div>
          <input 
            type="text" 
            id="ai-main-input" 
            v-model="aiInput"
            @focus="openAiPanel"
            class="block w-full p-1.5 pl-9 text-xs text-gray-700 bg-transparent border-none focus:ring-0 focus:outline-none placeholder-gray-400 h-8" 
            placeholder="Ask AI to layout modules..." 
            autocomplete="off">
        </div>
        <!-- Dropdown Chat Panel -->
        <div 
          id="ai-history-panel" 
          :class="{ 'hidden': !isAiPanelOpen, 'border-primary-500 ring-1 ring-primary-500 ring-t-0': isAiPanelOpen }"
          class="absolute top-full left-0 w-full bg-white border border-gray-300 border-t-0 rounded-b-md shadow-2xl z-40 flex flex-col h-[320px]">
          <div class="flex-1 overflow-y-auto p-3 space-y-3" id="dropdown-chat-history">
            <div class="flex items-start space-x-2">
              <div class="w-6 h-6 rounded-full bg-gradient-primary flex items-center justify-center flex-shrink-0">
                <i class="fa-solid fa-robot text-white text-[10px]"></i>
              </div>
              <div class="bg-gray-50 p-2 rounded-lg rounded-tl-none border border-gray-200 text-xs text-gray-700">
                我是 AI 助手。拖拽右侧组件以创建文档，或在此输入需求。
              </div>
            </div>
          </div>
          <div class="p-2 border-t border-gray-200 bg-gray-50 rounded-b-md flex justify-between items-center text-[10px]">
            <button 
              @click="openFullAiAssistant(); closeAiPanel();" 
              class="flex items-center space-x-2 text-primary-600 hover:text-primary-700 transition-colors bg-white hover:bg-gray-100 px-3 py-1.5 rounded border border-gray-300">
              <i class="fa-solid fa-up-right-from-square"></i><span>打开完整版</span>
            </button>
          </div>
        </div>
      </div>

      <!-- 右侧用户信息 -->
      <div class="flex items-center gap-4">
        <div class="flex items-center gap-2 px-3 py-1.5 rounded-full bg-gray-100 hover:bg-gray-200 cursor-pointer transition-colors">
          <div class="w-7 h-7 rounded-full bg-gradient-primary flex items-center justify-center text-white text-xs font-semibold">
            ?
          </div>
          <span class="text-sm text-gray-700">未登录</span>
        </div>
      </div>
    </div>

    <!-- 主体区域 -->
    <div class="flex-1 flex overflow-hidden">
      <!-- 1. 左侧导航栏  -->
      <aside class="w-64 bg-white/95 backdrop-blur-sm border-r border-gray-200 flex flex-col flex-shrink-0 z-10 shadow-sm">
        <div class="sidebar-section flex flex-col h-full">
          <div class="sidebar-title flex items-center justify-between px-4 py-3 border-b border-gray-200">
            <span class="text-sm font-semibold text-gray-700">我的应用</span>
            <button class="sidebar-add-btn w-6 h-6 flex items-center justify-center rounded hover:bg-gray-100 transition-colors text-gray-500 hover:text-gray-700" title="添加导航项">
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M8 2v12M2 8h12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
              </svg>
            </button>
          </div>
          <div class="flex-1 overflow-y-auto py-2">
            <!-- 动态导航项列表 -->
            <template v-for="(navItem, index) in navItems" :key="navItem.id">
              <!-- 父级导航项 -->
              <div>
                <div 
                  class="sidebar-item flex items-center gap-3 px-4 py-2.5 cursor-pointer transition-colors"
                  :class="activeNavItem === navItem.id ? 'bg-primary-50 text-primary-700 hover:bg-primary-100' : 'hover:bg-gray-50 text-gray-700'"
                  @click="switchNavItem(navItem.id)">
                  <!-- 展开/折叠图标（如果有子项） -->
                  <button
                    v-if="navItem.children && navItem.children.length > 0"
                    @click.stop="toggleNavItemExpand(navItem.id)"
                    class="w-4 h-4 flex items-center justify-center flex-shrink-0 text-gray-400 hover:text-gray-600 transition-transform"
                    :class="{ 'rotate-90': navItem.expanded }">
                    <svg viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg" class="w-3 h-3">
                      <path d="M6 4l4 4-4 4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                  </button>
                  <div v-else class="w-4 h-4 flex-shrink-0"></div>
                  
                  <!-- ODM需求图标 -->
                  <svg v-if="navItem.icon === 'odm'" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg" class="w-4 h-4 flex-shrink-0">
                    <rect x="2" y="2" width="5" height="5" rx="1" stroke="currentColor" stroke-width="1.5"/>
                    <rect x="9" y="2" width="5" height="5" rx="1" stroke="currentColor" stroke-width="1.5"/>
                    <rect x="2" y="9" width="5" height="5" rx="1" stroke="currentColor" stroke-width="1.5"/>
                    <rect x="9" y="9" width="5" height="5" rx="1" stroke="currentColor" stroke-width="1.5"/>
                  </svg>
                  <!-- 数据查询图标 -->
                  <svg v-else-if="navItem.icon === 'data-query'" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg" class="w-4 h-4 flex-shrink-0">
                    <path d="M8 2L2 6v8h12V6L8 2z" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/>
                  </svg>
                  <!-- 文档搜索图标 -->
                  <svg v-else-if="navItem.icon === 'doc-search'" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg" class="w-4 h-4 flex-shrink-0">
                    <path d="M8 2l1.5 3.5 4 .5-3 3 .5 4L8 11.5 5 13l.5-4L2.5 6l4-.5L8 2z" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round" fill="currentColor" fill-opacity="0.1"/>
                  </svg>
                  <!-- 自定义ODM图标 -->
                  <svg v-else viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg" class="w-4 h-4 flex-shrink-0">
                    <rect x="2" y="2" width="5" height="5" rx="1" stroke="currentColor" stroke-width="1.5"/>
                    <rect x="9" y="2" width="5" height="5" rx="1" stroke="currentColor" stroke-width="1.5"/>
                    <rect x="2" y="9" width="5" height="5" rx="1" stroke="currentColor" stroke-width="1.5"/>
                    <rect x="9" y="9" width="5" height="5" rx="1" stroke="currentColor" stroke-width="1.5"/>
                  </svg>
                  <span class="text-sm flex-1">{{ navItem.title }}</span>
                </div>
                
                <!-- 子项列表（可折叠） -->
                <div 
                  v-if="navItem.children && navItem.children.length > 0 && navItem.expanded"
                  class="pl-8 space-y-0">
                  <div
                    v-for="child in navItem.children"
                    :key="child.id"
                    class="sidebar-item flex items-center gap-3 px-4 py-2 cursor-pointer transition-colors"
                    :class="activeNavItem === child.id ? 'bg-primary-50 text-primary-700 hover:bg-primary-100' : 'hover:bg-gray-50 text-gray-700'"
                    @click="switchNavItem(child.id)">
                    <div class="w-4 h-4 flex-shrink-0"></div>
                    <!-- 子项图标 -->
                    <svg viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg" class="w-4 h-4 flex-shrink-0">
                      <rect x="2" y="2" width="5" height="5" rx="1" stroke="currentColor" stroke-width="1.5"/>
                      <rect x="9" y="2" width="5" height="5" rx="1" stroke="currentColor" stroke-width="1.5"/>
                      <rect x="2" y="9" width="5" height="5" rx="1" stroke="currentColor" stroke-width="1.5"/>
                      <rect x="9" y="9" width="5" height="5" rx="1" stroke="currentColor" stroke-width="1.5"/>
                    </svg>
                    <span class="text-sm flex-1">{{ child.title }}</span>
                  </div>
                </div>
              </div>
            </template>
          </div>
        </div>
      </aside>
      
      <!-- 2. 主内容区域（中间工作台 + 右侧边栏作为一个整体） -->
      <!-- 当点击"ODM需求"父项时，显示ODM选择界面 -->
      <div class="flex-1 flex overflow-hidden w-full" v-show="activeNavItem === 'odm'">
        <OdmSelectWindow :odms="historyOdms" @select="handleOdmSelect" @create="openOdmSelectModal" class="flex-1" />
      </div>
      
      <!-- 当点击ODM子项时，显示工作台 -->
      <div class="flex-1 flex overflow-hidden" v-show="getNavItemType(activeNavItem) === 'odm' && activeNavItem !== 'odm'">
        <!-- 2.1 中间工作台 (Main Canvas) -->
        <main class="flex-1 bg-white flex flex-col relative transition-all">
          <!-- Canvas Area (Grid System) -->
          <div id="main-canvas" ref="mainCanvas" class="flex-1 overflow-hidden relative" :style="canvasStyle">
            <!-- Empty State -->
            <div 
              v-if="openWindowIds.length === 0"
              id="empty-state" 
              class="absolute inset-0 flex flex-col items-center justify-center text-gray-500 z-0 pointer-events-none">
              <div class="flex space-x-4 mb-4 opacity-40">
                <i class="fa-solid fa-file-circle-plus text-5xl text-gray-400"></i>
              </div>
              <p class="text-sm text-gray-700">工作台为空</p>
              <p class="text-xs mt-2 text-gray-500">从右侧目录点击或拖拽文件以打开</p>
            </div>
            
            <!-- Windows -->
            <template v-for="(instId, index) in openWindowIds" :key="instId">
              <div 
                :id="instId"
                :style="getWindowStyle(index)"
                class="tile-window relative bg-white border border-gray-300 flex flex-col z-10 w-full h-full overflow-hidden transition-all duration-200 shadow-md"
                @dragover.prevent="handleWindowDragOver($event, instId)"
                @dragleave="handleWindowDragLeave($event, instId)"
                @drop.prevent="handleWindowDrop($event, instId)">
                <div 
                  class="window-header h-8 bg-gray-100 flex items-center justify-between px-3 border-b border-gray-300 group select-none cursor-move" 
                  draggable="true"
                  @dragstart="handleWindowDragStart($event, instId)"
                  @dragend="handleWindowDragEnd">
                  <div class="flex items-center text-xs text-gray-800 truncate pointer-events-none font-medium">
                    <i :class="getWindowIcon(instId)" class="mr-2 text-primary-600"></i>
                    {{ getWindowTitle(instId) }}
                  </div>
                  <button 
                    class="text-gray-400 hover:text-red-500" 
                    title="Close View" 
                    @click="closeWindow(instId)">
                    <i class="fa-solid fa-xmark"></i>
                  </button>
                </div>
                <div class="flex-1 p-4 overflow-y-auto window-content bg-white relative">
                  <component :is="getWindowComponent(instId)" :item="getProjectItem(instId)" />
                </div>
              </div>
            </template>
            
            <!-- Gutters -->
            <template v-if="openWindowIds.length >= 2">
              <div 
                class="gutter gutter-v"
                :style="{ gridColumn: '2 / 3', gridRow: '1 / -1' }"
                @mousedown="initResize($event, 'col')"></div>
            </template>
            <template v-if="openWindowIds.length >= 3">
              <div 
                class="gutter gutter-h"
                :style="getGutterHStyle()"
                @mousedown="initResize($event, 'row')"></div>
            </template>
          </div>
        </main>

        <!-- 2.2 统一右侧边栏 -->
        <aside class="w-80 bg-white/95 backdrop-blur-sm border-r border-gray-200 flex flex-col flex-shrink-0 z-10 shadow-sm">
        <div class="flex border-b border-gray-200 bg-white select-none">
          <div 
            class="flex-1 py-3 text-xs font-bold text-center sidebar-tab text-gray-500 transition-colors" 
            :class="{ 'active bg-gradient-primary text-white': activeSidebarTab === 'explorer' }"
            @click="switchSidebarTab('explorer')" 
            id="tab-explorer">
            <i class="fa-solid fa-box-open mr-2"></i>组件库
          </div>
          <div 
            class="flex-1 py-3 text-xs font-bold text-center sidebar-tab text-gray-500 transition-colors" 
            :class="{ 'active bg-gradient-primary text-white': activeSidebarTab === 'builder' }"
            @click="switchSidebarTab('builder')" 
            id="tab-builder">
            <i class="fa-solid fa-folder-tree mr-2"></i>项目目录
            <span v-if="projectItems.length > 0" id="tab-badge" class="ml-1 px-1.5 rounded-full bg-primary-500 text-white text-[10px]">
              {{ projectItems.length }}
            </span>
          </div>
        </div>

        <!-- Panel: Explorer -->
        <div 
          id="panel-explorer" 
          v-show="activeSidebarTab === 'explorer'"
          class="flex-1 flex flex-col overflow-y-auto">
          <div class="p-2 px-3 text-[10px] text-gray-500 uppercase tracking-wider font-bold bg-gray-50 border-b border-gray-200 flex justify-between items-center">
            Available Resources
          </div>
          
          <!-- Section 1: Customer Selection -->
          <div class="mb-1 mt-2">
            <div 
              class="px-3 py-1 text-xs text-gray-700 hover:bg-gray-100 cursor-pointer flex items-center group select-none transition-colors" 
              @click="toggleExplorerSection('customerSelection')">
              <i 
                class="fa-solid fa-chevron-down text-[10px] w-4 transition-transform duration-200"
                :class="{ '-rotate-90': !explorerSections.customerSelection }"></i>
              <span class="font-bold text-primary-600">
                <i class="fa-solid fa-bolt mr-2"></i>客户选配
              </span>
            </div>
            <div 
              v-show="explorerSections.customerSelection"
              class="pl-4 mt-1 space-y-[1px] transition-all duration-200 origin-top">
              <div 
                v-for="item in customerSelectionItems"
                :key="item.id"
                class="draggable-item px-4 py-3 hover:bg-gray-50 cursor-pointer border-l-2 border-transparent hover:border-primary-500 group" 
                draggable="true"
                :data-type="item.type"
                :data-id="item.id"
                :data-title="item.title"
                @dragstart="handleDragStart($event, item)"
                @click="handleItemClick(item)">
                <div class="flex justify-between items-center">
                  <div class="text-sm text-gray-700">{{ item.title }}</div>
                </div>
                <div class="text-[10px] text-gray-500" :class="item.recommended ? 'mono-font text-green-600' : ''">
                  {{ item.recommended ? 'RECOMMENDED' : item.description }}
                </div>
              </div>
            </div>
          </div>

          <!-- Section 2: Service Tools -->
          <div class="mt-2">
            <div 
              class="px-3 py-1 text-xs text-gray-700 hover:bg-gray-100 cursor-pointer flex items-center group select-none transition-colors" 
              @click="toggleExplorerSection('serviceTools')">
              <i 
                class="fa-solid fa-chevron-down text-[10px] w-4 transition-transform duration-200"
                :class="{ '-rotate-90': !explorerSections.serviceTools }"></i>
              <span class="font-bold text-secondary-600">
                <i class="fa-solid fa-calculator mr-2"></i>服务工具
              </span>
            </div>
            <div 
              v-show="explorerSections.serviceTools"
              class="pl-4 mt-1 space-y-[1px] transition-all duration-200 origin-top">
              <div 
                v-for="item in serviceToolItems"
                :key="item.id"
                class="draggable-item px-4 py-3 hover:bg-gray-50 cursor-pointer group" 
                draggable="true"
                :data-type="item.type"
                :data-id="item.id"
                :data-title="item.title"
                @dragstart="handleDragStart($event, item)"
                @click="handleItemClick(item)">
                <div class="flex justify-between items-center">
                  <div class="text-sm text-gray-700">{{ item.title }}</div>
                </div>
                <div class="text-[10px] text-gray-500" :class="item.colorClass">
                  <i v-if="item.icon" :class="item.icon" class="mr-1"></i>{{ item.description }}
                </div>
              </div>
            </div>
          </div>

          <!-- Section 3: Dev Tools -->
          <div class="mt-2">
            <div 
              class="px-3 py-1 text-xs text-gray-700 hover:bg-gray-100 cursor-pointer flex items-center group select-none transition-colors" 
              @click="toggleExplorerSection('devTools')">
              <i 
                class="fa-solid fa-chevron-down text-[10px] w-4 transition-transform duration-200"
                :class="{ '-rotate-90': !explorerSections.devTools }"></i>
              <span class="font-bold text-green-600">
                <i class="fa-solid fa-battery-full mr-2"></i>研发工具
              </span>
            </div>
            <div 
              v-show="explorerSections.devTools"
              class="pl-4 mt-1 space-y-[1px] transition-all duration-200 origin-top">
              <div 
                v-for="item in devToolItems"
                :key="item.id"
                class="draggable-item px-4 py-3 hover:bg-gray-50 cursor-pointer border-l-2 border-transparent hover:border-green-500 group" 
                draggable="true"
                :data-type="item.type"
                :data-id="item.id"
                :data-title="item.title"
                @dragstart="handleDragStart($event, item)"
                @click="handleItemClick(item)">
                <div class="flex justify-between items-center">
                  <div class="text-sm text-gray-700">{{ item.title }}</div>
                </div>
                <div class="text-[10px] text-gray-500" :class="item.recommended ? 'mono-font text-green-600' : ''">
                  {{ item.recommended ? 'RECOMMENDED' : item.description }}
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Panel: Builder (Renamed concept to Project Directory) -->
        <div 
          id="panel-builder" 
          v-show="activeSidebarTab === 'builder'"
          class="flex-1 flex flex-col h-full">
          <!-- Drop Zone / List -->
          <div 
            id="brochure-stage" 
            ref="brochureStage"
            class="flex-1 overflow-y-auto p-2 space-y-1 bg-gray-50"
            @dragover.prevent="handleBuilderDragOver"
            @dragleave="handleBuilderDragLeave"
            @drop.prevent="handleBuilderDrop">
            <div 
              v-if="projectItems.length === 0"
              id="brochure-hint" 
              class="border border-dashed border-gray-300 rounded p-6 text-center mt-10 bg-white">
              <i class="fa-solid fa-folder-open text-gray-400 text-2xl mb-2"></i>
              <p class="text-xs text-gray-500">项目为空<br>从组件库添加内容</p>
              <button 
                @click="switchSidebarTab('explorer')" 
                class="mt-4 text-xs text-primary-600 hover:text-primary-700 underline">
                打开组件库
              </button>
            </div>
            <!-- Items -->
            <div 
              v-for="item in projectItems"
              :key="item.instanceId"
              :class="{ 'active-file-indicator bg-blue-50 border-blue-200': openWindowIds.includes(item.instanceId) }"
              class="draggable-builder-item p-2 rounded cursor-pointer border border-gray-200 hover:border-gray-400 group flex items-center justify-between mb-1 select-none transition-all bg-white hover:bg-gray-100 shadow-sm"
              draggable="true"
              :data-instance-id="item.instanceId"
              @click="openWindow(item.instanceId)"
              @dragstart="handleBuilderItemDragStart($event, item)"
              @dragend="handleBuilderItemDragEnd">
              <div class="flex items-center space-x-3 overflow-hidden pointer-events-none">
                <div 
                  :class="openWindowIds.includes(item.instanceId) ? 'bg-gradient-primary text-white shadow-md' : 'bg-gray-200 text-gray-600'"
                  class="w-8 h-8 rounded flex items-center justify-center flex-shrink-0 transition-all">
                  <i :class="getItemIcon(item.type)"></i>
                </div>
                <div class="flex flex-col overflow-hidden">
                  <div 
                    :class="openWindowIds.includes(item.instanceId) ? 'text-blue-700 font-semibold' : 'text-gray-800'"
                    class="text-xs truncate">
                    {{ item.title }}
                  </div>
                  <div 
                    :class="openWindowIds.includes(item.instanceId) ? 'text-blue-600' : 'text-gray-500'"
                    class="text-[10px] truncate">
                    {{ openWindowIds.includes(item.instanceId) ? '已打开' : '已保存' }}
                  </div>
                </div>
              </div>
              <button 
                class="text-gray-500 hover:text-red-600 p-1 opacity-0 group-hover:opacity-100 transition-opacity hover:bg-red-50 rounded" 
                title="Delete File"
                @click.stop="deleteProjectItem(item.instanceId)">
                <i class="fa-solid fa-trash-can"></i>
              </button>
            </div>
          </div>
          <!-- Footer Action -->
          <div class="p-4 border-t border-gray-200 bg-white flex-shrink-0">
            <button 
              @click="openPreviewModal" 
              class="w-full bg-gradient-primary hover:opacity-90 text-white text-xs font-bold py-2 px-4 rounded transition flex items-center justify-center shadow-lg">
              <i class="fa-solid fa-eye mr-2"></i> 预览方案
            </button>
          </div>
        </div>
      </aside>
      </div>

      <!-- 数据查询视图 -->
      <div class="flex-1 flex overflow-hidden" v-show="getNavItemType(activeNavItem) === 'data-query'">
        <div class="flex-1 bg-white flex items-center justify-center">
          <div class="text-center text-gray-400">
            <i class="fa-solid fa-folder-open text-5xl mb-4 opacity-30"></i>
            <p class="text-sm text-gray-600">数据查询功能</p>
            <p class="text-xs mt-2 text-gray-400">开发中...</p>
          </div>
        </div>
      </div>

      <!-- 文档搜索视图 -->
      <div class="flex-1 flex overflow-hidden" v-show="getNavItemType(activeNavItem) === 'doc-search'">
        <div class="flex-1 bg-white flex items-center justify-center">
          <div class="text-center text-gray-400">
            <i class="fa-solid fa-magnifying-glass text-5xl mb-4 opacity-30"></i>
            <p class="text-sm text-gray-600">文档搜索功能</p>
            <p class="text-xs mt-2 text-gray-400">开发中...</p>
          </div>
        </div>
      </div>
    </div>

    <!-- PREVIEW MODAL -->
    <div 
      v-if="showPreviewModal"
      id="preview-modal" 
      class="fixed inset-0 z-[60] bg-black/80 flex items-center justify-center backdrop-blur-sm animate-[fadeIn_0.2s_ease-out]">
      <div class="bg-[#1e1e1e] w-[1200px] h-[750px] rounded-lg border border-[#2d313a] flex flex-col shadow-2xl overflow-hidden">
        <!-- Header -->
        <div class="h-12 border-b border-[#2d313a] flex items-center justify-between px-4 bg-[#16191f]">
          <div class="flex items-center space-x-2">
            <i class="fa-solid fa-print text-gray-400"></i>
            <span class="font-bold text-gray-200 text-sm">{{ showExportPreview ? 'PDF 导出预览' : '项目方案预览' }}</span>
          </div>
          <button 
            @click="closePreviewModal" 
            class="text-gray-500 hover:text-white transition">
            <i class="fa-solid fa-xmark"></i>
          </button>
        </div>
        
        <!-- Body -->
        <div class="flex-1 flex overflow-hidden">
          <!-- 导出预览模式 -->
          <template v-if="showExportPreview">
            <!-- 右侧 PDF 页签 -->
            <div class="w-56 bg-[#16191f] border-r border-[#2d313a] overflow-y-auto p-2 space-y-1">
              <div 
                v-for="(page, index) in pdfPages"
                :key="index"
                :class="{ active: currentPdfPage === index }"
                class="preview-tab p-2 rounded cursor-pointer mb-1 text-xs text-gray-400 hover:text-white hover:bg-[#2d313a] flex items-center space-x-2 transition"
                @click="currentPdfPage = index">
                <span class="w-4 text-center text-[10px] opacity-50">{{ index + 1 }}</span>
                <span class="truncate">{{ page.title }}</span>
              </div>
            </div>
            
            <!-- 主内容区域 -->
            <div class="flex-1 flex flex-col overflow-hidden bg-[#252830]">
              <!-- PDF 需求总结 -->
              <div class="p-4 bg-[#1e222b] border-b border-[#2d313a]">
                <div class="text-sm font-bold text-gray-300 mb-3">PDF 需求总结</div>
                <div class="grid grid-cols-2 gap-4 text-xs">
                  <div class="flex items-center space-x-2">
                    <span class="text-gray-500 min-w-[80px]">基准型号:</span>
                    <span class="text-gray-200 font-mono">{{ bomDiffData.model_info?.base_model || 'SP0030-00-23-5QP' }}</span>
                  </div>
                  <div class="flex items-center space-x-2">
                    <span class="text-gray-500 min-w-[80px]">对比型号:</span>
                    <span class="text-gray-200 font-mono">{{ bomDiffData.model_info?.target_model || 'SP0030-3Q-23-5QP' }}</span>
                  </div>
                  <div class="flex items-center space-x-2">
                    <span class="text-gray-500 min-w-[80px]">差异数量:</span>
                    <span class="text-blue-400 font-bold">{{ bomDiffData.statistics?.diff_count || 0 }} 项</span>
                  </div>
                  <div class="flex items-center space-x-2">
                    <span class="text-gray-500 min-w-[80px]">子BOM数量:</span>
                    <span class="text-purple-400 font-bold">{{ bomDiffData.statistics?.sub_bom_count || 0 }} 项</span>
                  </div>
                </div>
              </div>
              
              <!-- 根据页签类型显示不同内容 -->
              <div class="flex-1 overflow-y-auto p-4">
                <!-- 统计汇总 -->
                <template v-if="pdfPages[currentPdfPage]?.type === 'summary'">
                  <div class="bg-white rounded border border-gray-200 p-6">
                    <h2 class="text-lg font-bold text-gray-800 mb-6">统计汇总</h2>
                    
                    <div class="space-y-4 text-sm text-gray-800 leading-relaxed">
                      <div class="mb-4">
                        <p class="text-base font-semibold text-gray-900 mb-2">
                          请参考 <span class="font-mono text-blue-600">DE0030-5L-20-52-00P</span> 新建-5L鸿富瀚 BOM
                        </p>
                      </div>
                      
                      <div class="bg-yellow-50 border-l-4 border-yellow-400 p-4 rounded">
                        <div class="flex items-start">
                          <div class="flex-shrink-0">
                            <i class="fa-solid fa-circle-exclamation text-yellow-600"></i>
                          </div>
                          <div class="ml-3">
                            <p class="text-sm font-semibold text-yellow-800 mb-2">差异物料:</p>
                            <p class="text-sm text-gray-700">
                              上盖、纸箱、纸箱标签(内容)、电气标签(内容)、快装、CQC、质保卡(<span class="font-mono">540-100519.00</span>)、合格证(<span class="font-mono">540-200540-00</span>)
                            </p>
                          </div>
                        </div>
                      </div>
                      
                      <div class="bg-red-50 border-l-4 border-red-400 p-4 rounded">
                        <div class="flex items-start">
                          <div class="flex-shrink-0">
                            <i class="fa-solid fa-trash-can text-red-600"></i>
                          </div>
                          <div class="ml-3">
                            <p class="text-sm font-semibold text-red-800 mb-2">删除物料:</p>
                            <p class="text-sm text-gray-700">
                              资料库标签、爱士推营业执照
                            </p>
                          </div>
                        </div>
                      </div>
                      
                      <div class="bg-blue-50 border-l-4 border-blue-400 p-4 rounded">
                        <div class="flex items-start">
                          <div class="flex-shrink-0">
                            <i class="fa-solid fa-barcode text-blue-600"></i>
                          </div>
                          <div class="ml-3">
                            <p class="text-sm font-semibold text-blue-800 mb-1">棒子料号:</p>
                            <p class="text-sm font-mono text-gray-700">B9301V-07-10P</p>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </template>
                
                <!-- BOM差异表 -->
                <template v-else-if="pdfPages[currentPdfPage]?.type === 'diff'">
                  <div class="bg-white rounded border border-gray-200 overflow-hidden">
                    <table class="w-full text-sm border-collapse">
                      <thead class="bg-gray-100 border-b border-gray-300">
                        <tr>
                          <th class="py-2 px-3 text-left border-r border-gray-300 font-semibold text-gray-700">物料名称</th>
                          <th class="py-2 px-3 text-left border-r border-gray-300 font-semibold text-gray-700">原始料号</th>
                          <th class="py-2 px-3 text-left border-r border-gray-300 font-semibold text-gray-700">变更料号</th>
                          <th class="py-2 px-3 text-center font-semibold text-gray-700">变更类型</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr 
                          v-for="(item, index) in bomDiffData.diff_items" 
                          :key="index"
                          class="border-b border-gray-200 hover:bg-gray-50">
                          <td class="py-2 px-3 border-r border-gray-200 text-gray-800">{{ item['MPART.NAME'] }}</td>
                          <td class="py-2 px-3 border-r border-gray-200">
                            <div v-if="item.base_bom['MPART.NO']" class="flex flex-col space-y-1">
                              <span class="font-mono text-gray-700">{{ item.base_bom['MPART.NO'] }} x{{ item.base_bom['MPART.BNUM'] }}</span>
                              <div class="flex flex-wrap gap-1">
                                <span class="px-1.5 py-0.5 bg-purple-100 text-purple-700 rounded text-[10px]">{{ item.base_bom['MPART.PRNT'] }}</span>
                                <span class="px-1.5 py-0.5 bg-blue-100 text-blue-700 rounded text-[10px]">{{ item.base_bom['MPART.OP'] }}</span>
                              </div>
                            </div>
                            <span v-else class="text-gray-400 text-xs">-</span>
                          </td>
                          <td class="py-2 px-3 border-r border-gray-200">
                            <div v-if="item.target_bom['MPART.NO']" class="flex flex-col space-y-1">
                              <span class="font-mono text-gray-700">{{ item.target_bom['MPART.NO'] }} x{{ item.target_bom['MPART.BNUM'] }}</span>
                              <div class="flex flex-wrap gap-1">
                                <span class="px-1.5 py-0.5 bg-purple-100 text-purple-700 rounded text-[10px]">{{ item.target_bom['MPART.PRNT'] }}</span>
                                <span class="px-1.5 py-0.5 bg-blue-100 text-blue-700 rounded text-[10px]">{{ item.target_bom['MPART.OP'] }}</span>
                              </div>
                            </div>
                            <span v-else class="text-gray-400 text-xs">-</span>
                          </td>
                          <td class="py-2 px-3 text-center">
                            <span 
                              class="px-2 py-1 rounded text-xs font-semibold"
                              :class="getChangeTypeClass(item.target_bom.REMARK)">
                              {{ getChangeTypeLabel(item.target_bom.REMARK) }}
                            </span>
                          </td>
                        </tr>
                        <tr v-if="bomDiffData.diff_items.length === 0">
                          <td colspan="4" class="py-8 text-center text-gray-500">暂无差异数据</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                </template>
                
                <!-- 子BOM明细 -->
                <template v-else-if="pdfPages[currentPdfPage]?.type === 'sub_bom'">
                  <div class="bg-white rounded border border-gray-200 overflow-hidden">
                    <table class="w-full text-sm border-collapse">
                      <thead class="bg-gray-100 border-b border-gray-300">
                        <tr>
                          <th class="py-2 px-3 text-left border-r border-gray-300 font-semibold text-gray-700">物料名称</th>
                          <th class="py-2 px-3 text-left border-r border-gray-300 font-semibold text-gray-700">料号</th>
                          <th class="py-2 px-3 text-left border-r border-gray-300 font-semibold text-gray-700">父料号</th>
                          <th class="py-2 px-3 text-left border-r border-gray-300 font-semibold text-gray-700">数量</th>
                          <th class="py-2 px-3 text-left border-r border-gray-300 font-semibold text-gray-700">操作类型</th>
                          <th class="py-2 px-3 text-center font-semibold text-gray-700">备注</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr 
                          v-for="(item, index) in bomDiffData.sub_bom_items" 
                          :key="index"
                          class="border-b border-gray-200 hover:bg-gray-50">
                          <td class="py-2 px-3 border-r border-gray-200 text-gray-800">{{ item['MPART.NAME'] }}</td>
                          <td class="py-2 px-3 border-r border-gray-200 font-mono text-gray-700">{{ item['MPART.NO'] }}</td>
                          <td class="py-2 px-3 border-r border-gray-200 font-mono text-gray-700">{{ item['MPART.PRNT'] }}</td>
                          <td class="py-2 px-3 border-r border-gray-200 text-gray-700">{{ item['MPART.BNUM'] }}</td>
                          <td class="py-2 px-3 border-r border-gray-200">
                            <span class="px-1.5 py-0.5 bg-blue-100 text-blue-700 rounded text-[10px]">{{ item['MPART.OP'] }}</span>
                          </td>
                          <td class="py-2 px-3 text-center">
                            <span class="px-2 py-1 rounded text-xs font-semibold bg-green-100 text-green-800">
                              {{ item['REMARK'] }}
                            </span>
                          </td>
                        </tr>
                        <tr v-if="bomDiffData.sub_bom_items.length === 0">
                          <td colspan="6" class="py-8 text-center text-gray-500">暂无子BOM数据</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                </template>
              </div>
            </div>
          </template>
          
          <!-- 普通预览模式 -->
          <template v-else>
            <!-- Sidebar / Tabs -->
            <div class="w-56 bg-[#16191f] border-r border-[#2d313a] overflow-y-auto p-2 space-y-1" id="preview-tabs">
              <div 
                v-for="(item, index) in projectItems"
                :key="index"
                :class="{ active: currentPreviewTab === index }"
                class="preview-tab p-2 rounded cursor-pointer mb-1 text-xs text-gray-400 hover:text-white hover:bg-[#2d313a] flex items-center space-x-2 transition"
                @click="switchPreviewTab(index)">
                <span class="w-4 text-center text-[10px] opacity-50">{{ index + 1 }}</span>
                <span class="truncate">{{ item.title }}</span>
              </div>
            </div>
            
            <!-- Preview Pane (Canvas for A4) -->
            <div class="flex-1 bg-[#252830] p-8 flex items-start justify-center overflow-y-auto relative custom-scrollbar">
              <div id="preview-content" class="a4-paper transform scale-90 origin-top" v-html="previewContent"></div>
            </div>
          </template>
        </div>
        
        <!-- Footer -->
        <div class="h-14 border-t border-[#2d313a] bg-[#16191f] flex items-center justify-end px-4 space-x-3">
          <div class="mr-auto text-[10px] text-gray-500">
            <i class="fa-solid fa-circle-info mr-1"></i> {{ showExportPreview ? 'PDF 导出预览模式' : '导出将生成标准 A4 PDF 文档' }}
          </div>
          <button 
            v-if="showExportPreview"
            @click="showExportPreview = false" 
            class="text-xs text-gray-400 hover:text-white px-3 py-2 rounded hover:bg-[#2d313a] transition">
            返回预览
          </button>
          <button 
            @click="closePreviewModal" 
            class="text-xs text-gray-400 hover:text-white px-3 py-2 rounded hover:bg-[#2d313a] transition">
            取消
          </button>
          <button 
            @click="realExportPDF" 
            :disabled="isExporting"
            class="bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold py-2 px-4 rounded shadow-lg transition flex items-center"
            :class="{ 'opacity-75 cursor-wait': isExporting, 'bg-green-600': exportSuccess }">
            <i :class="exportSuccess ? 'fa-solid fa-check' : (isExporting ? 'fa-solid fa-circle-notch fa-spin' : 'fa-solid fa-file-export')" class="mr-2"></i>
            {{ exportSuccess ? 'Sent to Email' : (isExporting ? 'Generating...' : '确认导出 PDF') }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import ProductWindow from '../../components/ProductWindow.vue'
import CalculatorWindow from '../../components/CalculatorWindow.vue'
import AiAssistantWindow from '../../components/AiAssistantWindow.vue'
import Viewer3DWindow from '../../components/Viewer3DWindow.vue'
import ProductParamsWindow from '../../components/ProductParamsWindow.vue'
import OdmSelectWindow from '../../components/OdmSelectWindow.vue'

// State Management
// 为每个导航项维护独立的工作区状态
const workspaceStates = ref(new Map()) // Map<navItemId, { projectItems: [], openWindowIds: [] }>
const gridCols = ref([50, 50])
const gridRows = ref([50, 50])
const MAX_WINDOWS = 4
const draggingWindowId = ref(null)
const draggedBuilderItem = ref(null)
const draggedData = ref(null)
const isAiPanelOpen = ref(false)
const aiInput = ref('')
const activeSidebarTab = ref('builder')
const activeNavItem = ref('odm') // 当前选中的导航项: 'odm', 'data-query', 'doc-search'

// 获取当前激活导航项的工作区状态
const projectItems = computed({
  get() {
    return getWorkspaceState(activeNavItem.value).projectItems
  },
  set(value) {
    getWorkspaceState(activeNavItem.value).projectItems = value
  }
})

const openWindowIds = computed({
  get() {
    return getWorkspaceState(activeNavItem.value).openWindowIds
  },
  set(value) {
    getWorkspaceState(activeNavItem.value).openWindowIds = value
  }
})

// 获取或创建工作区状态
function getWorkspaceState(navItemId) {
  if (!workspaceStates.value.has(navItemId)) {
    workspaceStates.value.set(navItemId, {
      projectItems: [],
      openWindowIds: []
    })
  }
  return workspaceStates.value.get(navItemId)
}
// 导航项列表（动态管理）
const navItems = ref([
  { 
    id: 'odm', 
    title: 'ODM需求', 
    icon: 'odm', 
    type: 'odm',
    expanded: true, // 默认展开
    children: [] // 子项列表
  },
  { id: 'data-query', title: '数据查询', icon: 'data-query', type: 'data-query' },
  { id: 'doc-search', title: '文档搜索', icon: 'doc-search', type: 'doc-search' }
])
const explorerSections = reactive({
  customerSelection: true,  // 客户选配
  serviceTools: true,        // 服务工具
  devTools: true             // 研发工具
})
// 历史ODM需求数据
const historyOdms = ref([
  { 
    id: 'odm-001', 
    name: '正泰', 
    code: 'ZT', 
    description: '浙江正泰安能电力系统工程有限公司历史信息', 
    createDate: new Date('2024-01-15'),
    itemCount: 12
  },
  { 
    id: 'odm-002', 
    name: '鸿富瀚', 
    code: 'LT', 
    description: '深圳市富智新能源科技有限公司历史信息', 
    createDate: new Date('2024-01-10'),
    itemCount: 8
  },
  { 
    id: 'odm-003', 
    name: 'TCL', 
    code: 'TCL', 
    description: '惠州TCL光伏科技有限公司历史信息', 
    createDate: new Date('2024-01-05'),
    itemCount: 15
  }
])
const showPreviewModal = ref(false)
const currentPreviewTab = ref(0)
const previewContent = ref('')
const isExporting = ref(false)
const exportSuccess = ref(false)
const showExportPreview = ref(false) // 是否显示导出预览模式
const pdfPages = ref([]) // PDF页签列表
const currentPdfPage = ref(0) // 当前PDF页签索引

// Refs
const mainCanvas = ref(null)
const brochureStage = ref(null)
const aiCommandCenter = ref(null)

// Data
const customerSelectionItems = [
  { id: 'requirement-discussion', type: 'product', title: '需求讨论', description: '客户需求讨论与确认', recommended: false },
  { id: 'model-selection', type: 'product', title: '型号选择', description: 'RECOMMENDED', recommended: true },
]

const serviceToolItems = [
  { id: 'ai-guide', type: 'ai-assistant', title: 'AI 智能导购', description: '智能推荐系统', icon: 'fa-solid fa-wand-magic-sparkles', colorClass: 'text-purple-400' },
  { id: '3d-model', type: '3d-viewer', title: '3D 模型展示', description: '交互式3D查看器', icon: 'fa-solid fa-cube', colorClass: 'text-orange-400' },
  { id: 'product-params', type: 'product-params', title: '产品手册', description: '产品参数文档', icon: 'fa-solid fa-sliders', colorClass: 'text-blue-400' }
]

const devToolItems = [
  { id: 'design-diff-table', type: 'product', title: '设计差异表', description: 'BOM设计差异对比', recommended: false },
  { id: 'doc-change', type: 'product', title: '文档变更', description: '文档变更记录', recommended: false }
]

// Computed
const canvasStyle = computed(() => {
  if (openWindowIds.value.length === 0) {
    return { display: 'flex' }
  }
  
  const colTemplate = `${gridCols.value[0]}% 4px ${gridCols.value[1]}%`
  const rowTemplate = `${gridRows.value[0]}% 4px ${gridRows.value[1]}%`
  
  let style = { display: 'grid' }
  
  if (openWindowIds.value.length === 1) {
    style.gridTemplateColumns = '1fr'
    style.gridTemplateRows = '1fr'
  } else if (openWindowIds.value.length === 2) {
    style.gridTemplateColumns = colTemplate
    style.gridTemplateRows = '1fr'
  } else if (openWindowIds.value.length >= 3) {
    style.gridTemplateColumns = colTemplate
    style.gridTemplateRows = rowTemplate
  }
  
  return style
})

// Methods
function addProjectItem(data) {
  const instanceId = 'inst-' + Date.now() + Math.random().toString(36).substr(2, 5)
  const newItem = {
    instanceId: instanceId,
    type: data.type,
    title: data.title,
    originalId: data.id
  }
  
  projectItems.value.push(newItem)
  
  // Auto open in canvas if space permits
  if (openWindowIds.value.length < MAX_WINDOWS) {
    openWindow(instanceId)
  }
}

function openWindow(instanceId) {
  if (openWindowIds.value.includes(instanceId)) {
    return
  }
  
  if (openWindowIds.value.length >= MAX_WINDOWS) {
    alert("工作台已满 (最多4个窗口)，请先关闭一个窗口")
    return
  }

  openWindowIds.value.push(instanceId)
}

function closeWindow(instanceId) {
  openWindowIds.value = openWindowIds.value.filter(id => id !== instanceId)
}

function deleteProjectItem(instanceId) {
  projectItems.value = projectItems.value.filter(item => item.instanceId !== instanceId)
  
  // Also close window if open
  if (openWindowIds.value.includes(instanceId)) {
    openWindowIds.value = openWindowIds.value.filter(id => id !== instanceId)
  }
}

function getProjectItem(instanceId) {
  return projectItems.value.find(p => p.instanceId === instanceId)
}

function getWindowTitle(instanceId) {
  const item = getProjectItem(instanceId)
  return item ? item.title : ''
}

function getWindowIcon(instanceId) {
  const item = getProjectItem(instanceId)
  if (!item) return 'fa-solid fa-bolt'
  
  let iconClass = 'fa-solid fa-bolt'
  if (item.type === 'calculator') iconClass = 'fa-solid fa-calculator'
  if (item.type === 'ai-assistant') iconClass = 'fa-solid fa-robot text-purple-500'
  if (item.type === '3d-viewer') iconClass = 'fa-solid fa-cube text-orange-500'
  if (item.type === 'product-params') iconClass = 'fa-solid fa-sliders text-blue-500'
  
  return iconClass
}

function getWindowComponent(instanceId) {
  const item = getProjectItem(instanceId)
  if (!item) return null
  
  const componentMap = {
    'product': ProductWindow,
    'calculator': CalculatorWindow,
    'ai-assistant': AiAssistantWindow,
    '3d-viewer': Viewer3DWindow,
    'product-params': ProductParamsWindow
  }
  
  return componentMap[item.type] || null
}

function getWindowStyle(index) {
  const length = openWindowIds.value.length
  
  if (length === 1) {
    return { gridColumn: '1 / -1', gridRow: '1 / -1' }
  } else if (length === 2) {
    return {
      gridColumn: index === 0 ? '1 / 2' : '3 / 4',
      gridRow: '1 / -1'
    }
  } else if (length === 3) {
    if (index === 0) return { gridColumn: '1 / 2', gridRow: '1 / -1' }
    if (index === 1) return { gridColumn: '3 / 4', gridRow: '1 / 2' }
    if (index === 2) return { gridColumn: '3 / 4', gridRow: '3 / 4' }
  } else if (length === 4) {
    if (index === 0) return { gridColumn: '1 / 2', gridRow: '1 / 2' }
    if (index === 1) return { gridColumn: '3 / 4', gridRow: '1 / 2' }
    if (index === 2) return { gridColumn: '1 / 2', gridRow: '3 / 4' }
    if (index === 3) return { gridColumn: '3 / 4', gridRow: '3 / 4' }
  }
  
  return {}
}

function getGutterHStyle() {
  return {
    gridRow: '2 / 3',
    gridColumn: openWindowIds.value.length === 3 ? '3 / 4' : '1 / -1'
  }
}

function getItemIcon(type) {
  const iconMap = {
    'product': 'fa-solid fa-bolt',
    'calculator': 'fa-solid fa-chart-pie',
    'ai-assistant': 'fa-solid fa-robot',
    '3d-viewer': 'fa-solid fa-cube',
    'product-params': 'fa-solid fa-sliders'
  }
  return iconMap[type] || 'fa-solid fa-file'
}

// Drag & Drop Handlers
function handleDragStart(e, item) {
  draggedData.value = {
    type: item.type,
    title: item.title,
    id: item.id
  }
}

// Click Handler - Add item and open window
function handleItemClick(item) {
  // Add item to project and open window
  addProjectItem({
    type: item.type,
    title: item.title,
    id: item.id
  })
}

function handleWindowDragStart(e, instId) {
  draggingWindowId.value = instId
  e.dataTransfer.effectAllowed = 'move'
}

function handleWindowDragEnd() {
  draggingWindowId.value = null
}

function handleWindowDragOver(e, instId) {
  e.preventDefault()
  if (draggingWindowId.value && draggingWindowId.value !== instId) {
    e.currentTarget.classList.add('window-drag-target')
  }
}

function handleWindowDragLeave(e, instId) {
  e.currentTarget.classList.remove('window-drag-target')
}

function handleWindowDrop(e, instId) {
  e.preventDefault()
  e.stopPropagation()
  e.currentTarget.classList.remove('window-drag-target')
  
  if (draggingWindowId.value && draggingWindowId.value !== instId) {
    const srcIdx = openWindowIds.value.indexOf(draggingWindowId.value)
    const tgtIdx = openWindowIds.value.indexOf(instId)
    if (srcIdx > -1 && tgtIdx > -1) {
      // Swap positions
      [openWindowIds.value[srcIdx], openWindowIds.value[tgtIdx]] = 
      [openWindowIds.value[tgtIdx], openWindowIds.value[srcIdx]]
    }
  }
}

function handleBuilderItemDragStart(e, item) {
  draggedBuilderItem.value = e.currentTarget
  draggedData.value = {
    type: item.type,
    title: item.title,
    id: item.originalId,
    instanceId: item.instanceId,
    source: 'builder'
  }
  e.currentTarget.classList.add('dragging')
  e.dataTransfer.effectAllowed = 'move'
}

function handleBuilderItemDragEnd(e) {
  draggedBuilderItem.value = null
  draggedData.value = null
  e.currentTarget.classList.remove('dragging')
}

function handleBuilderDragOver(e) {
  e.preventDefault()
  if (draggedBuilderItem.value) {
    const afterElement = getDragAfterElement(brochureStage.value, e.clientY)
    if (afterElement == null) {
      brochureStage.value.appendChild(draggedBuilderItem.value)
    } else {
      brochureStage.value.insertBefore(draggedBuilderItem.value, afterElement)
    }
  } else {
    brochureStage.value.classList.add('bg-gray-800')
  }
}

function handleBuilderDragLeave(e) {
  if (!draggedBuilderItem.value) {
    brochureStage.value.classList.remove('bg-gray-800')
  }
}

function handleBuilderDrop(e) {
  e.preventDefault()
  brochureStage.value.classList.remove('bg-gray-800')
  
  // Internal Sort Drop
  if (draggedBuilderItem.value) {
    const newOrderIds = [...brochureStage.value.querySelectorAll('.draggable-builder-item')]
      .map(el => el.dataset.instanceId)
    const newProjectItems = []
    newOrderIds.forEach(id => {
      const item = projectItems.value.find(p => p.instanceId === id)
      if (item) newProjectItems.push(item)
    })
    projectItems.value = newProjectItems
    draggedBuilderItem.value = null
    return
  }
  
  // New Item Drop from Explorer
  if (draggedData.value && draggedData.value.source !== 'builder') {
    addProjectItem(draggedData.value)
    draggedData.value = null
  }
}

function getDragAfterElement(container, y) {
  const draggableElements = [...container.querySelectorAll('.draggable-builder-item:not(.dragging)')]
  return draggableElements.reduce((closest, child) => {
    const box = child.getBoundingClientRect()
    const offset = y - box.top - box.height / 2
    if (offset < 0 && offset > closest.offset) {
      return { offset: offset, element: child }
    } else {
      return closest
    }
  }, { offset: Number.NEGATIVE_INFINITY }).element
}

// Canvas Drop Handler
function handleCanvasDrop(e) {
  e.preventDefault()
  if (!draggedData.value) return
  
  // Check if dragging internal window
  if (draggingWindowId.value) return
  
  // Check if dragging existing project item (from builder)
  if (draggedData.value.source === 'builder') {
    openWindow(draggedData.value.instanceId)
  } else {
    // Dragging new from Explorer
    addProjectItem(draggedData.value)
  }
  draggedData.value = null
}

// Resize Logic
function initResize(e, type) {
  e.preventDefault()
  const canvas = mainCanvas.value
  const startX = e.clientX
  const startY = e.clientY
  const rect = canvas.getBoundingClientRect()
  const startColPct = gridCols.value[0]
  const startRowPct = gridRows.value[0]

  function onMouseMove(e) {
    if (type === 'col') {
      const deltaX = e.clientX - startX
      const deltaPct = (deltaX / rect.width) * 100
      let newPct = Math.max(10, Math.min(90, startColPct + deltaPct))
      gridCols.value = [newPct, 100 - newPct]
    } else {
      const deltaY = e.clientY - startY
      const deltaPct = (deltaY / rect.height) * 100
      let newPct = Math.max(10, Math.min(90, startRowPct + deltaPct))
      gridRows.value = [newPct, 100 - newPct]
    }
  }
  
  function onMouseUp() {
    document.removeEventListener('mousemove', onMouseMove)
    document.removeEventListener('mouseup', onMouseUp)
  }
  
  document.addEventListener('mousemove', onMouseMove)
  document.addEventListener('mouseup', onMouseUp)
}

// AI Panel
function openAiPanel() {
  isAiPanelOpen.value = true
}

function closeAiPanel() {
  isAiPanelOpen.value = false
}

function openFullAiAssistant() {
  addProjectItem({ type: 'ai-assistant', title: 'AI 智能导购', id: 'ai-full-mode' })
}

// Sidebar
function switchSidebarTab(tabName) {
  activeSidebarTab.value = tabName
}

function toggleExplorerSection(section) {
  explorerSections[section] = !explorerSections[section]
}

// Navigation
function switchNavItem(navItemId) {
  // 保存当前工作区状态（如果需要）
  // 由于使用了computed，状态已经自动保存到workspaceStates中
  
  // 切换到新的导航项
  activeNavItem.value = navItemId
  
  // 确保新导航项有工作区状态
  getWorkspaceState(navItemId)
  
  // 触发响应式更新（通过computed自动处理）
}

function getNavItemType(navItemId) {
  // 先查找父项
  const item = navItems.value.find(n => n.id === navItemId)
  if (item) return item.type
  
  // 再查找子项
  for (const navItem of navItems.value) {
    if (navItem.children) {
      const child = navItem.children.find(c => c.id === navItemId)
      if (child) return child.type || navItem.type
    }
  }
  return null
}

// 切换导航项展开/折叠
function toggleNavItemExpand(navItemId) {
  const item = navItems.value.find(n => n.id === navItemId)
  if (item && item.children) {
    item.expanded = !item.expanded
  }
}

// 新建ODM子页签
function openOdmSelectModal() {
  // 找到"ODM需求"项
  const odmItem = navItems.value.find(n => n.id === 'odm')
  if (!odmItem) {
    return
  }
  
  // 确保children数组存在
  if (!odmItem.children) {
    odmItem.children = []
  }
  
  // 创建新的子页签（使用时间戳作为唯一ID）
  const newNavItemId = `odm-${Date.now()}`
  const newChildItem = {
    id: newNavItemId,
    title: `新ODM项目 ${odmItem.children.length + 1}`,
    icon: 'odm-custom',
    type: 'odm'
  }
  
  // 添加到ODM需求的children中
  odmItem.children.push(newChildItem)
  
  // 确保展开状态
  odmItem.expanded = true
  
  // 初始化新子项的工作区状态
  getWorkspaceState(newNavItemId)
  
  // 切换到新创建的导航项
  switchNavItem(newNavItemId)
  
  // 自动打开需求讨论组件
  openRequirementDiscussion()
}

// 处理从历史ODM选择
function handleOdmSelect(odm) {
  // 找到"ODM需求"项
  const odmItem = navItems.value.find(n => n.id === 'odm')
  if (!odmItem) {
    return
  }
  
  // 确保children数组存在
  if (!odmItem.children) {
    odmItem.children = []
  }
  
  // 创建新的导航项ID
  const newNavItemId = `odm-${odm.id}`
  
  // 检查是否已存在相同ID的子项
  const existingChild = odmItem.children.find(c => c.id === newNavItemId)
  if (existingChild) {
    // 如果已存在，直接切换到该导航项
    switchNavItem(newNavItemId)
    // 确保展开状态
    odmItem.expanded = true
    // 打开需求讨论组件
    openRequirementDiscussion()
    return
  }
  
  // 创建新的子项
  const newChildItem = {
    id: newNavItemId,
    title: odm.name,
    icon: 'odm-custom',
    type: 'odm',
    odmData: odm
  }
  
  // 添加到ODM需求的children中
  odmItem.children.push(newChildItem)
  
  // 确保展开状态
  odmItem.expanded = true
  
  // 初始化新子项的工作区状态
  getWorkspaceState(newNavItemId)
  
  // 切换到新创建的导航项
  switchNavItem(newNavItemId)
  
  // 打开需求讨论组件
  openRequirementDiscussion()
}

function openRequirementDiscussion() {
  // 找到需求讨论组件
  const requirementItem = customerSelectionItems.find(item => item.id === 'requirement-discussion')
  if (requirementItem) {
    // 添加项目并打开窗口
    addProjectItem({
      type: requirementItem.type,
      title: requirementItem.title,
      id: requirementItem.id
    })
  }
}

// Preview Modal
function openPreviewModal() {
  if (projectItems.value.length === 0) {
    alert("请先添加项目内容")
    return
  }
  
  showPreviewModal.value = true
  currentPreviewTab.value = 0
  switchPreviewTab(0)
}

function closePreviewModal() {
  showPreviewModal.value = false
  showExportPreview.value = false
  exportSuccess.value = false
  isExporting.value = false
  currentPdfPage.value = 0
}

function switchPreviewTab(index) {
  currentPreviewTab.value = index
  const item = projectItems.value[index]
  
  if (item.type === 'product') {
    previewContent.value = `
      <h1 class="text-2xl font-bold mb-2 border-b-2 border-blue-600 pb-2">${item.title}</h1>
      <div class="text-sm text-gray-500 mb-8">Technical Specification Sheet</div>
      
      <div class="flex mb-8">
        <div class="w-1/2 pr-4">
          <div class="bg-gray-100 h-48 rounded flex items-center justify-center border border-gray-200">
            <i class="fa-solid fa-server text-6xl text-gray-400"></i>
          </div>
        </div>
        <div class="w-1/2 pl-4">
          <h2 class="text-lg font-bold mb-4 text-gray-800">Key Features</h2>
          <ul class="list-disc list-inside space-y-2 text-sm text-gray-700">
            <li>Max. PV array power: 4500 Wp STC</li>
            <li>MPPT Voltage range: 80V - 550V</li>
            <li>Max. Input Current: 16 A</li>
            <li>Protection Class: IP66</li>
            <li>Integrated WiFi stick</li>
          </ul>
        </div>
      </div>
      
      <h2 class="text-lg font-bold mb-4 text-gray-800">Performance Data</h2>
      <table class="w-full text-sm text-left border-collapse">
        <thead>
          <tr class="bg-gray-100 border-b border-gray-300">
            <th class="py-2 px-2">Parameter</th>
            <th class="py-2 px-2">Value</th>
          </tr>
        </thead>
        <tbody>
          <tr class="border-b border-gray-200"><td class="py-2 px-2">Nominal AC Power</td><td class="py-2 px-2 font-mono">5000 W</td></tr>
          <tr class="border-b border-gray-200"><td class="py-2 px-2">Max. Efficiency</td><td class="py-2 px-2 font-mono">98.4%</td></tr>
          <tr class="border-b border-gray-200"><td class="py-2 px-2">Grid Connection</td><td class="py-2 px-2">Single Phase</td></tr>
        </tbody>
      </table>
    `
  } else if (item.type === 'calculator') {
    previewContent.value = `
      <h1 class="text-2xl font-bold mb-2 border-b-2 border-green-600 pb-2">ROI Analysis</h1>
      <div class="text-sm text-gray-500 mb-8">Generated Report for: Villa Project</div>
      
      <div class="grid grid-cols-2 gap-4 mb-8">
        <div class="bg-blue-50 p-4 rounded border border-blue-100">
          <div class="text-xs text-gray-500">Estimated Payback</div>
          <div class="text-3xl font-bold text-blue-600">3.2 Years</div>
        </div>
        <div class="bg-green-50 p-4 rounded border border-green-100">
          <div class="text-xs text-gray-500">25-Year Savings</div>
          <div class="text-3xl font-bold text-green-600">¥ 124,500</div>
        </div>
      </div>
      
      <h2 class="text-lg font-bold mb-4 text-gray-800">Financial Projection</h2>
      <div class="bg-gray-50 h-64 w-full border border-gray-200 rounded flex items-end justify-around px-8 pb-0 pt-8 mb-4">
        <div class="w-8 bg-blue-400 h-[20%]"></div>
        <div class="w-8 bg-blue-500 h-[40%]"></div>
        <div class="w-8 bg-blue-600 h-[60%]"></div>
        <div class="w-8 bg-blue-700 h-[80%]"></div>
        <div class="w-8 bg-blue-800 h-[90%]"></div>
      </div>
      <div class="text-center text-xs text-gray-500 italic">Simulated annual yield based on 40m² roof area.</div>
    `
  } else if (item.type === 'product-params') {
    previewContent.value = `
      <h1 class="text-2xl font-bold mb-2 border-b-2 border-blue-600 pb-2">${item.title}</h1>
      <div class="text-sm text-gray-500 mb-8">产品参数配置报告</div>
      
      <div class="mb-6">
        <h2 class="text-lg font-bold mb-4 text-gray-800">产品型号筛选</h2>
        <div class="bg-gray-50 p-4 rounded border border-gray-200">
          <p class="text-sm text-gray-700 mb-2">支持多选产品型号进行参数对比</p>
          <div class="flex flex-wrap gap-2">
            <span class="px-3 py-1 bg-blue-100 text-blue-800 rounded text-sm">ASW6000-S</span>
            <span class="px-3 py-1 bg-blue-100 text-blue-800 rounded text-sm">ASW8000-S</span>
          </div>
        </div>
      </div>
      
      <div class="mb-6">
        <h2 class="text-lg font-bold mb-4 text-gray-800">配置类型筛选</h2>
        <div class="bg-gray-50 p-4 rounded border border-gray-200">
          <p class="text-sm text-gray-700 mb-2">可筛选标配或选配参数</p>
          <div class="flex gap-2">
            <span class="px-3 py-1 bg-green-100 text-green-800 rounded text-sm">标配</span>
            <span class="px-3 py-1 bg-purple-100 text-purple-800 rounded text-sm">选配</span>
          </div>
        </div>
      </div>
      
      <h2 class="text-lg font-bold mb-4 text-gray-800">参数配置表</h2>
      <table class="w-full text-sm text-left border-collapse border border-gray-300">
        <thead>
          <tr class="bg-gray-100 border-b border-gray-300">
            <th class="py-2 px-3 border border-gray-300">参数名称</th>
            <th class="py-2 px-3 border border-gray-300">参数值</th>
            <th class="py-2 px-3 border border-gray-300">配置类型</th>
          </tr>
        </thead>
        <tbody>
          <tr class="border-b border-gray-200">
            <td class="py-2 px-3 border border-gray-300">最大功率</td>
            <td class="py-2 px-3 border border-gray-300 font-mono">6000W / 8000W / 10000W</td>
            <td class="py-2 px-3 border border-gray-300">标配</td>
          </tr>
          <tr class="border-b border-gray-200">
            <td class="py-2 px-3 border border-gray-300">输入电压</td>
            <td class="py-2 px-3 border border-gray-300 font-mono">80V-550V</td>
            <td class="py-2 px-3 border border-gray-300">标配</td>
          </tr>
          <tr class="border-b border-gray-200">
            <td class="py-2 px-3 border border-gray-300">WiFi模块</td>
            <td class="py-2 px-3 border border-gray-300">内置 / 外置</td>
            <td class="py-2 px-3 border border-gray-300">选配</td>
          </tr>
        </tbody>
      </table>
    `
  } else {
    previewContent.value = `
      <h1 class="text-2xl font-bold mb-2 border-b-2 border-purple-600 pb-2">${item.title}</h1>
      <div class="text-sm text-gray-500 mb-8">Module Report</div>
      <div class="p-8 border border-dashed border-gray-300 rounded bg-gray-50 text-center text-gray-400">
        <i class="fa-solid fa-cube text-4xl mb-4"></i>
        <p>Visual content placeholder for ${item.type}</p>
      </div>
    `
  }
}

// BOM差异数据
const bomDiffData = ref({
  model_info: {
    base_model: 'SP0030-00-23-5QP',
    target_model: 'SP0030-3Q-23-5QP',
    title: 'SP0030-3Q-23-5QP 机种BOM差异表',
    create_date: '2024-01-15',
    creator: '系统管理员'
  },
  diff_items: [
    {
      'MPART.NAME': '一键扫码标签',
      base_bom: {
        'MPART.NO': '532-000103-00',
        'MPART.PRNT': 'SP0030-00-23-5QP',
        'MPART.BNUM': 1,
        'MPART.OP': '组装',
        'REMARK': ''
      },
      target_bom: {
        'MPART.NO': '532-000213-00',
        'MPART.PRNT': 'SP0030-3Q-23-5QP',
        'MPART.BNUM': 1,
        'MPART.OP': '组装',
        'REMARK': 'change'
      }
    },
    {
      'MPART.NAME': '文档包',
      base_bom: {
        'MPART.NO': '334-010915-00',
        'MPART.PRNT': 'SP0030-00-23-5QP',
        'MPART.BNUM': 1,
        'MPART.OP': '包装',
        'REMARK': ''
      },
      target_bom: {
        'MPART.NO': '334-000269-00',
        'MPART.PRNT': 'SP0030-3Q-23-5QP',
        'MPART.BNUM': 1,
        'MPART.OP': '包装',
        'REMARK': 'change'
      }
    },
    {
      'MPART.NAME': '数据棒',
      base_bom: {
        'MPART.NO': 'B93000-07-10P',
        'MPART.PRNT': 'SP0030-00-23-5QP',
        'MPART.BNUM': 1,
        'MPART.OP': '包装',
        'REMARK': ''
      },
      target_bom: {
        'MPART.NO': 'B93092-07-10P',
        'MPART.PRNT': 'SP0030-3Q-23-5QP',
        'MPART.BNUM': 1,
        'MPART.OP': '包装',
        'REMARK': 'change'
      }
    },
    {
      'MPART.NAME': '纸箱标签内容',
      base_bom: {
        'MPART.NO': '532-300167-00',
        'MPART.PRNT': 'SP0030-00-23-5QP',
        'MPART.BNUM': 1,
        'MPART.OP': '包装',
        'REMARK': ''
      },
      target_bom: {
        'MPART.NO': '532-300277-00',
        'MPART.PRNT': 'SP0030-3Q-23-5QP',
        'MPART.BNUM': 1,
        'MPART.OP': '包装',
        'REMARK': 'change'
      }
    },
    {
      'MPART.NAME': 'PE袋250X170',
      base_bom: {
        'MPART.NO': '',
        'MPART.PRNT': '',
        'MPART.BNUM': 0,
        'MPART.OP': '',
        'REMARK': ''
      },
      target_bom: {
        'MPART.NO': '536-10044-00',
        'MPART.PRNT': 'SP0030-3Q-23-5QP',
        'MPART.BNUM': 1,
        'MPART.OP': '包装',
        'REMARK': 'add'
      }
    },
    {
      'MPART.NAME': '标签50X10',
      base_bom: {
        'MPART.NO': '',
        'MPART.PRNT': '',
        'MPART.BNUM': 0,
        'MPART.OP': '',
        'REMARK': ''
      },
      target_bom: {
        'MPART.NO': '532-10014-00',
        'MPART.PRNT': 'SP0030-3Q-23-5QP',
        'MPART.BNUM': 1,
        'MPART.OP': '包装',
        'REMARK': 'add'
      }
    },
    {
      'MPART.NAME': '质保卡条形码标签',
      base_bom: {
        'MPART.NO': '',
        'MPART.PRNT': '',
        'MPART.BNUM': 0,
        'MPART.OP': '',
        'REMARK': ''
      },
      target_bom: {
        'MPART.NO': '532-10000-00',
        'MPART.PRNT': 'SP0030-3Q-23-5QP',
        'MPART.BNUM': 2,
        'MPART.OP': '包装',
        'REMARK': 'add'
      }
    },
    {
      'MPART.NAME': '旧版包装袋',
      base_bom: {
        'MPART.NO': '536-20011-00',
        'MPART.PRNT': 'SP0030-00-23-5QP',
        'MPART.BNUM': 1,
        'MPART.OP': '包装',
        'REMARK': ''
      },
      target_bom: {
        'MPART.NO': '',
        'MPART.PRNT': '',
        'MPART.BNUM': 0,
        'MPART.OP': '',
        'REMARK': 'delete'
      }
    },
    {
      'MPART.NAME': '主控板',
      base_bom: {
        'MPART.NO': '334-101191-00',
        'MPART.PRNT': 'SP0030-00-23-5QP',
        'MPART.BNUM': 1,
        'MPART.OP': '组装',
        'REMARK': ''
      },
      target_bom: {
        'MPART.NO': '334-101192-00',
        'MPART.PRNT': 'SP0030-3Q-23-5QP',
        'MPART.BNUM': 1,
        'MPART.OP': '组装',
        'REMARK': 'change'
      }
    },
    {
      'MPART.NAME': '显示屏模块',
      base_bom: {
        'MPART.NO': '334-200001-00',
        'MPART.PRNT': 'SP0030-00-23-5QP',
        'MPART.BNUM': 1,
        'MPART.OP': '组装',
        'REMARK': ''
      },
      target_bom: {
        'MPART.NO': '334-200002-00',
        'MPART.PRNT': 'SP0030-3Q-23-5QP',
        'MPART.BNUM': 1,
        'MPART.OP': '组装',
        'REMARK': 'change'
      }
    }
  ],
  sub_bom_items: [
    {
      'MPART.NAME': 'CQC证书-30K-新TCL',
      'MPART.NO': '540-300670-00',
      'MPART.PRNT': '334-000338-00',
      'MPART.BNUM': 1,
      'MPART.OP': '包装',
      'REMARK': 'Add'
    },
    {
      'MPART.NAME': '快装-钣金上盖-新TCL',
      'MPART.NO': '540-300655-00',
      'MPART.PRNT': '334-000338-00',
      'MPART.BNUM': 1,
      'MPART.OP': '包装',
      'REMARK': 'Add'
    },
    {
      'MPART.NAME': '质保卡-Aiswei',
      'MPART.NO': '532-08152-04',
      'MPART.PRNT': '334-000338-00',
      'MPART.BNUM': 1,
      'MPART.OP': '包装',
      'REMARK': 'Add'
    },
    {
      'MPART.NAME': '合格证-Aiswei',
      'MPART.NO': '540-30091-01',
      'MPART.PRNT': '334-000338-00',
      'MPART.BNUM': 1,
      'MPART.OP': '包装',
      'REMARK': 'Add'
    },
    {
      'MPART.NAME': '营业执照-Aiswei',
      'MPART.NO': '540-30092-02',
      'MPART.PRNT': '334-000338-00',
      'MPART.BNUM': 1,
      'MPART.OP': '包装',
      'REMARK': 'Add'
    }
  ],
  statistics: {
    diff_count: 10,
    sub_bom_count: 5,
    change_count: 5,
    add_count: 3,
    delete_count: 1,
    total_base_parts: 125,
    total_target_parts: 127
  }
})

// PDF页签数据
function initPdfPages() {
  pdfPages.value = [
    { title: '统计汇总', type: 'summary' },
    { title: 'BOM差异表', type: 'diff' },
    { title: '子BOM明细', type: 'sub_bom' }
  ]
}

// 获取变更类型样式
function getChangeTypeClass(remark) {
  const classMap = {
    'change': 'bg-yellow-100 text-yellow-800',
    'add': 'bg-green-100 text-green-800',
    'delete': 'bg-red-100 text-red-800'
  }
  return classMap[remark] || 'bg-gray-100 text-gray-800'
}

// 获取变更类型标签
function getChangeTypeLabel(remark) {
  const labelMap = {
    'change': '变更',
    'add': '新增',
    'delete': '删除'
  }
  return labelMap[remark] || '未知'
}

function realExportPDF() {
  isExporting.value = true
  exportSuccess.value = false
  
  // 初始化PDF页签
  initPdfPages()
  
  setTimeout(() => {
    // 切换到导出预览模式
    showExportPreview.value = true
    currentPdfPage.value = 0 // 默认显示第一个页签（统计汇总）
    isExporting.value = false
    
    // 模拟加载BOM差异数据（实际应该从API获取）
    // bomDiffData.value = await fetchBomDiffData()
    
    setTimeout(() => {
      exportSuccess.value = true
      // 不自动关闭，让用户查看预览
      // closePreviewModal()
    }, 500)
  }, 1500)
}

// Lifecycle
onMounted(() => {
  // 初始化默认导航项的工作区状态
  navItems.value.forEach(item => {
    getWorkspaceState(item.id)
    // 如果有子项，也初始化子项的工作区状态
    if (item.children) {
      item.children.forEach(child => {
        getWorkspaceState(child.id)
      })
    }
  })
  
  // 初始化当前激活导航项的工作区状态
  getWorkspaceState(activeNavItem.value)
  
  if (mainCanvas.value) {
    mainCanvas.value.addEventListener('dragover', (e) => e.preventDefault())
    mainCanvas.value.addEventListener('drop', handleCanvasDrop)
  }
  
  // Click outside to close AI panel
  document.addEventListener('click', (e) => {
    if (aiCommandCenter.value && !aiCommandCenter.value.contains(e.target)) {
      closeAiPanel()
    }
  })
})

onUnmounted(() => {
  if (mainCanvas.value) {
    mainCanvas.value.removeEventListener('dragover', (e) => e.preventDefault())
    mainCanvas.value.removeEventListener('drop', handleCanvasDrop)
  }
})
</script>

<style scoped>
/* IDE 风格字体 */
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&family=Inter:wght@400;500;600&display=swap');

.sbom-ide {
  font-family: 'Inter', sans-serif;
  background-color: #0f1115;
  color: #e2e8f0;
  overflow: hidden;
}

.mono-font {
  font-family: 'JetBrains Mono', monospace;
}

/* 极细边框风格 */
.ide-border {
  border: 1px solid #2d313a;
}
.ide-border-r { border-right: 1px solid #2d313a; }
.ide-border-l { border-left: 1px solid #2d313a; }
.ide-border-b { border-bottom: 1px solid #2d313a; }
.ide-border-t { border-top: 1px solid #2d313a; }

/* 滚动条隐藏但保留功能 */
:deep(::-webkit-scrollbar) {
  width: 6px;
  height: 6px;
}
:deep(::-webkit-scrollbar-track) { background: #0f1115; }
:deep(::-webkit-scrollbar-thumb) { background: #333; border-radius: 3px; }
:deep(::-webkit-scrollbar-thumb:hover) { background: #444; }

/* 导航项子项展开/折叠动画 */
.sidebar-item {
  transition: all 0.2s ease;
}

/* 子项列表动画 */
.pl-8 {
  animation: slideDown 0.2s ease-out;
}

@keyframes slideDown {
  from {
    opacity: 0;
    max-height: 0;
  }
  to {
    opacity: 1;
    max-height: 500px;
  }
}

/* 拖拽视觉反馈 */
.dragging {
  opacity: 0.5;
  border: 1px dashed #3b82f6;
}
.sortable-ghost {
  opacity: 0.4;
  background-color: #2d313a;
  border: 1px dashed #666;
}
.drag-over {
  background-color: rgba(59, 130, 246, 0.1);
  border: 1px dashed #3b82f6;
}

/* Tab 样式 */
.sidebar-tab {
  cursor: pointer;
  border-bottom: 2px solid transparent;
  transition: all 0.2s;
}
.sidebar-tab.active {
  border-bottom-color: #3b82f6;
  color: #fff;
  background-color: #3b82f6;
}
.sidebar-tab:hover:not(.active) {
  color: #1f2937;
  background-color: #f3f4f6;
  border-bottom-color: #e5e7eb;
}

/* 品牌色 */
.brand-blue { color: #3b82f6; }
.bg-brand-blue { background-color: #3b82f6; }

/* Grid Background */
.grid-bg {
  background-image: linear-gradient(rgba(255, 255, 255, 0.05) 1px, transparent 1px),
  linear-gradient(90deg, rgba(255, 255, 255, 0.05) 1px, transparent 1px);
  background-size: 20px 20px;
}

/* 主工作区 Grid 布局 */
#main-canvas {
  display: grid;
  grid-template-columns: 1fr;
  grid-template-rows: 1fr;
  background-color: #f5f5f7;
  position: relative;
}

/* 工作台区域滚动条样式（亮色主题） */
#main-canvas :deep(::-webkit-scrollbar) {
  width: 8px;
  height: 8px;
}
#main-canvas :deep(::-webkit-scrollbar-track) {
  background: #f5f5f7;
  border-radius: 4px;
}
#main-canvas :deep(::-webkit-scrollbar-thumb) {
  background: #d1d5db;
  border-radius: 4px;
}
#main-canvas :deep(::-webkit-scrollbar-thumb:hover) {
  background: #9ca3af;
}

/* 拖拽手柄样式 */
.gutter {
  background-color: #e5e7eb;
  z-index: 20;
  transition: background-color 0.2s;
}
.gutter:hover, .gutter.active {
  background-color: #3b82f6;
}
.gutter-v {
  width: 4px;
  cursor: col-resize;
  height: 100%;
}
.gutter-h {
  height: 4px;
  cursor: row-resize;
  width: 100%;
}

/* AI Panel Animations */
.expanded-input {
  border-bottom-left-radius: 0;
  border-bottom-right-radius: 0;
  border-bottom-color: transparent;
}

/* Window Active/Drag States */
.window-drag-target {
  box-shadow: inset 0 0 0 2px #3b82f6;
  background-color: rgba(59, 130, 246, 0.08) !important;
  border-color: #3b82f6 !important;
}
.active-file-indicator {
  border-left: 3px solid #3b82f6;
  background-color: #eff6ff;
  border-color: #3b82f6;
}

/* A4 Paper Preview Style */
.a4-paper {
  width: 595px;
  height: 842px;
  background: white;
  color: #333;
  box-shadow: 0 0 15px rgba(0,0,0,0.5);
  padding: 40px;
  font-family: 'Inter', sans-serif;
  transform-origin: top center;
  transition: all 0.3s;
}
.preview-tab.active {
  background-color: #2563eb;
  color: white;
  border-color: transparent;
}

/* Draggable Item Styles - Clickable */
.draggable-item {
  transition: all 0.2s ease;
  user-select: none;
}

.draggable-item:hover {
  transform: translateX(2px);
}

.draggable-item:active {
  transform: translateX(0);
  opacity: 0.8;
}

/* PDF 导出预览表格样式 */
#preview-modal table {
  font-size: 12px;
}

#preview-modal table th {
  background-color: #f3f4f6;
  font-weight: 600;
  color: #374151;
}

#preview-modal table td {
  color: #1f2937;
}

#preview-modal table tr:hover {
  background-color: #f9fafb;
}
</style>
