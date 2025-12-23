<template>
  <div class="h-full flex flex-col bg-white overflow-y-auto">
    <!-- 标题栏 -->
    <div class="text-sm font-bold text-gray-800 mb-4 border-b border-gray-200 pb-2 px-4 pt-4 sticky top-0 bg-white z-10">
      <i class="fa-solid fa-building mr-2 text-blue-600"></i>{{ item.title || '需求讨论' }}
    </div>
    
    <!-- 顶部操作栏 -->
    <div class="border-b border-gray-200 bg-gray-50 px-4 py-3 flex justify-between items-center">
      <div class="text-xs text-gray-600">
        <i class="fa-solid fa-info-circle mr-1"></i>
        最后更新：{{ lastUpdateTime }}
      </div>
      <div class="flex space-x-2">
        <button 
          @click="openImportModal"
          class="px-4 py-2 text-xs text-gray-700 hover:text-gray-900 border border-gray-300 rounded hover:bg-gray-100 transition-colors">
          <i class="fa-solid fa-download mr-1"></i>导入
        </button>
        <button 
          @click="updateForm"
          class="px-4 py-2 text-xs font-bold text-white bg-blue-600 hover:bg-blue-700 rounded transition-colors shadow-sm">
          <i class="fa-solid fa-save mr-1"></i>更新
        </button>
      </div>
    </div>
    
    <!-- 表单内容 -->
    <div class="flex-1 px-4 pb-4 space-y-6 overflow-y-auto">
      <!-- 基本信息区域 -->
      <div class="space-y-4">
        <div class="text-xs font-bold text-gray-700 mb-3 flex items-center">
          <i class="fa-solid fa-info-circle mr-2 text-blue-600"></i>基本信息
        </div>
        
        <!-- 公司全称 -->
        <div class="form-group">
          <label class="form-label">公司全称 <span class="text-red-600">*</span></label>
          <input 
            v-model="formData.companyName"
            type="text" 
            class="form-input"
            placeholder="请输入公司全称"
          />
        </div>

        <!-- 公司地址 -->
        <div class="form-group">
          <label class="form-label">公司地址</label>
          <input 
            v-model="formData.companyAddress"
            type="text" 
            class="form-input"
            placeholder="请输入公司地址"
          />
        </div>

        <!-- 公司联系电话 -->
        <div class="form-group">
          <label class="form-label">公司联系电话</label>
          <input 
            v-model="formData.companyPhone"
            type="tel" 
            class="form-input"
            placeholder="请输入公司联系电话"
          />
        </div>

        <!-- 公司传真 -->
        <div class="form-group">
          <label class="form-label">公司传真</label>
          <input 
            v-model="formData.companyFax"
            type="text" 
            class="form-input"
            placeholder="请输入公司传真"
          />
        </div>

        <!-- 公司官网 -->
        <div class="form-group">
          <label class="form-label">公司官网</label>
          <input 
            v-model="formData.companyWebsite"
            type="url" 
            class="form-input"
            placeholder="https://example.com"
          />
        </div>
      </div>

      <!-- 服务信息区域 -->
      <div class="space-y-4">
        <div class="text-xs font-bold text-gray-700 mb-3 flex items-center">
          <i class="fa-solid fa-headset mr-2 text-purple-600"></i>服务信息
        </div>

        <!-- 服务400电话 -->
        <div class="form-group">
          <label class="form-label">服务400电话</label>
          <input 
            v-model="formData.service400Phone"
            type="tel" 
            class="form-input"
            placeholder="400-xxx-xxxx"
          />
        </div>

        <!-- 服务邮箱 -->
        <div class="form-group">
          <label class="form-label">服务邮箱</label>
          <input 
            v-model="formData.serviceEmail"
            type="email" 
            class="form-input"
            placeholder="service@example.com"
          />
        </div>

        <!-- 服务公众号二维码 -->
        <div class="form-group">
          <label class="form-label">服务公众号二维码</label>
          <div class="flex items-start space-x-4">
            <div class="image-upload-container">
              <div 
                v-if="formData.serviceQRCode" 
                class="image-preview group"
                @click="previewImage(formData.serviceQRCode)">
                <img :src="formData.serviceQRCode" alt="服务公众号二维码" />
                <div class="image-overlay">
                  <i class="fa-solid fa-eye"></i>
                </div>
              </div>
              <div v-else class="image-upload-placeholder" @click="triggerFileUpload('serviceQRCode')">
                <i class="fa-solid fa-image text-2xl text-gray-400 mb-2"></i>
                <span class="text-xs text-gray-500">点击上传二维码</span>
              </div>
              <input 
                ref="serviceQRCodeInput"
                type="file" 
                accept="image/*"
                @change="handleImageUpload($event, 'serviceQRCode')"
                class="hidden"
              />
            </div>
            <button 
              v-if="formData.serviceQRCode"
              @click="removeImage('serviceQRCode')"
              class="text-red-600 hover:text-red-700 text-xs mt-2">
              <i class="fa-solid fa-trash mr-1"></i>删除
            </button>
          </div>
        </div>

        <!-- 自有APP二维码-安卓&苹果系统 -->
        <div class="form-group">
          <label class="form-label">自有APP二维码-安卓&苹果系统</label>
          <div class="grid grid-cols-2 gap-4">
            <!-- 安卓二维码 -->
            <div>
              <div class="text-xs text-gray-600 mb-2">安卓系统</div>
              <div class="flex items-start space-x-4">
                <div class="image-upload-container">
                  <div 
                    v-if="formData.appQRCodeAndroid" 
                    class="image-preview group"
                    @click="previewImage(formData.appQRCodeAndroid)">
                    <img :src="formData.appQRCodeAndroid" alt="安卓APP二维码" />
                    <div class="image-overlay">
                      <i class="fa-solid fa-eye"></i>
                    </div>
                  </div>
                  <div v-else class="image-upload-placeholder" @click="triggerFileUpload('appQRCodeAndroid')">
                    <i class="fa-solid fa-image text-xl text-gray-400 mb-1"></i>
                    <span class="text-[10px] text-gray-500">上传安卓二维码</span>
                  </div>
                  <input 
                    ref="appQRCodeAndroidInput"
                    type="file" 
                    accept="image/*"
                    @change="handleImageUpload($event, 'appQRCodeAndroid')"
                    class="hidden"
                  />
                </div>
                <button 
                  v-if="formData.appQRCodeAndroid"
                  @click="removeImage('appQRCodeAndroid')"
                  class="text-red-600 hover:text-red-700 text-xs mt-2">
                  <i class="fa-solid fa-trash mr-1"></i>
                </button>
              </div>
            </div>
            <!-- 苹果二维码 -->
            <div>
              <div class="text-xs text-gray-600 mb-2">苹果系统</div>
              <div class="flex items-start space-x-4">
                <div class="image-upload-container">
                  <div 
                    v-if="formData.appQRCodeIOS" 
                    class="image-preview group"
                    @click="previewImage(formData.appQRCodeIOS)">
                    <img :src="formData.appQRCodeIOS" alt="苹果APP二维码" />
                    <div class="image-overlay">
                      <i class="fa-solid fa-eye"></i>
                    </div>
                  </div>
                  <div v-else class="image-upload-placeholder" @click="triggerFileUpload('appQRCodeIOS')">
                    <i class="fa-solid fa-image text-xl text-gray-400 mb-1"></i>
                    <span class="text-[10px] text-gray-500">上传苹果二维码</span>
                  </div>
                  <input 
                    ref="appQRCodeIOSInput"
                    type="file" 
                    accept="image/*"
                    @change="handleImageUpload($event, 'appQRCodeIOS')"
                    class="hidden"
                  />
                </div>
                <button 
                  v-if="formData.appQRCodeIOS"
                  @click="removeImage('appQRCodeIOS')"
                  class="text-red-600 hover:text-red-700 text-xs mt-2">
                  <i class="fa-solid fa-trash mr-1"></i>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 产品信息区域 -->
      <div class="space-y-4">
        <div class="text-xs font-bold text-gray-700 mb-3 flex items-center">
          <i class="fa-solid fa-box mr-2 text-orange-600"></i>产品信息
        </div>

        <!-- 产品名称要求 -->
        <div class="form-group">
          <label class="form-label">产品名称要求</label>
          <textarea 
            v-model="formData.productNameRequirement"
            class="form-textarea"
            rows="3"
            placeholder="请输入产品名称要求"
          ></textarea>
        </div>

        <!-- 监控WEB、APP -->
        <div class="form-group">
          <label class="form-label">监控WEB、APP</label>
          <div class="flex flex-wrap gap-3">
            <label class="flex items-center cursor-pointer">
              <input 
                type="checkbox" 
                v-model="formData.monitorWeb"
                class="form-checkbox"
              />
              <span class="text-xs text-gray-700 ml-2">监控WEB</span>
            </label>
            <label class="flex items-center cursor-pointer">
              <input 
                type="checkbox" 
                v-model="formData.monitorApp"
                class="form-checkbox"
              />
              <span class="text-xs text-gray-700 ml-2">监控APP</span>
            </label>
          </div>
        </div>

        <!-- 公司logo -->
        <div class="form-group">
          <label class="form-label">公司logo</label>
          <div class="flex items-start space-x-4">
            <div class="image-upload-container logo-container">
              <div 
                v-if="formData.companyLogo" 
                class="image-preview group"
                @click="previewImage(formData.companyLogo)">
                <img :src="formData.companyLogo" alt="公司logo" />
                <div class="image-overlay">
                  <i class="fa-solid fa-eye"></i>
                </div>
              </div>
              <div v-else class="image-upload-placeholder" @click="triggerFileUpload('companyLogo')">
                <i class="fa-solid fa-image text-2xl text-gray-400 mb-2"></i>
                <span class="text-xs text-gray-500">点击上传Logo</span>
              </div>
              <input 
                ref="companyLogoInput"
                type="file" 
                accept="image/*"
                @change="handleImageUpload($event, 'companyLogo')"
                class="hidden"
              />
            </div>
            <button 
              v-if="formData.companyLogo"
              @click="removeImage('companyLogo')"
              class="text-red-600 hover:text-red-700 text-xs mt-2">
              <i class="fa-solid fa-trash mr-1"></i>删除
            </button>
          </div>
        </div>

        <!-- 上盖颜色 -->
        <div class="form-group">
          <label class="form-label">上盖颜色</label>
          <div class="flex items-center space-x-4">
            <input 
              v-model="formData.coverColor"
              type="color" 
              class="color-picker"
            />
            <input 
              v-model="formData.coverColor"
              type="text" 
              class="form-input flex-1"
              placeholder="#000000"
              pattern="^#[0-9A-Fa-f]{6}$"
            />
            <div 
              class="color-preview"
              :style="{ backgroundColor: formData.coverColor }"
            ></div>
          </div>
        </div>
      </div>
    </div>

    <!-- 图片预览模态框 -->
    <div 
      v-if="previewImageUrl"
      class="fixed inset-0 z-50 bg-black/80 flex items-center justify-center backdrop-blur-sm"
      @click="previewImageUrl = null">
      <div class="max-w-4xl max-h-[90vh] p-4" @click.stop>
        <img :src="previewImageUrl" alt="预览" class="max-w-full max-h-[90vh] rounded" />
        <button 
          @click="previewImageUrl = null"
          class="absolute top-4 right-4 text-white hover:text-gray-300 text-2xl">
          <i class="fa-solid fa-xmark"></i>
        </button>
      </div>
    </div>

    <!-- 导入模板弹窗 -->
    <div 
      v-if="showImportModal"
      class="fixed inset-0 z-50 bg-black/50 flex items-center justify-center backdrop-blur-sm"
      @click="showImportModal = false">
      <div 
        class="bg-white rounded-lg shadow-xl w-[600px] max-h-[80vh] flex flex-col"
        @click.stop>
        <!-- 弹窗标题 -->
        <div class="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <h3 class="text-lg font-semibold text-gray-800">
            <i class="fa-solid fa-database mr-2 text-blue-600"></i>选择模板
          </h3>
          <button 
            @click="showImportModal = false"
            class="text-gray-400 hover:text-gray-600 transition-colors">
            <i class="fa-solid fa-xmark text-xl"></i>
          </button>
        </div>
        
        <!-- 模板列表 -->
        <div class="flex-1 overflow-y-auto px-6 py-4">
          <div v-if="isLoadingTemplates" class="text-center py-8 text-gray-500">
            <i class="fa-solid fa-spinner fa-spin text-4xl mb-2 text-blue-600"></i>
            <p>正在加载模板...</p>
          </div>
          <div v-else-if="templates.length === 0" class="text-center py-8 text-gray-500">
            <i class="fa-solid fa-inbox text-4xl mb-2 opacity-50"></i>
            <p>暂无模板数据</p>
          </div>
          <div v-else class="space-y-3">
            <div 
              v-for="template in templates" 
              :key="template.id"
              @click="selectTemplate(template)"
              class="p-4 border border-gray-200 rounded-lg cursor-pointer hover:border-blue-500 hover:bg-blue-50 transition-all"
              :class="{ 'border-blue-500 bg-blue-50': selectedTemplateId === template.id }">
              <div class="flex items-start justify-between">
                <div class="flex-1">
                  <div class="flex items-center mb-2">
                    <h4 class="text-sm font-semibold text-gray-800 mr-2">{{ template.name }}</h4>
                    <span class="text-xs text-gray-500 bg-gray-100 px-2 py-0.5 rounded">{{ template.category }}</span>
                  </div>
                  <p class="text-xs text-gray-600 mb-2">{{ template.description }}</p>
                  <div class="flex items-center text-xs text-gray-500">
                    <i class="fa-solid fa-calendar mr-1"></i>
                    <span>更新时间：{{ template.updateTime }}</span>
                  </div>
                </div>
                <div class="ml-4">
                  <i 
                    class="fa-solid fa-check-circle text-blue-600 text-xl"
                    v-if="selectedTemplateId === template.id"></i>
                  <i 
                    class="fa-regular fa-circle text-gray-300 text-xl"
                    v-else></i>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <!-- 弹窗底部操作 -->
        <div class="px-6 py-4 border-t border-gray-200 flex justify-end space-x-2">
          <button 
            @click="showImportModal = false"
            class="px-4 py-2 text-xs text-gray-700 hover:text-gray-900 border border-gray-300 rounded hover:bg-gray-100 transition-colors">
            取消
          </button>
          <button 
            @click="importTemplate"
            :disabled="!selectedTemplateId || isImporting"
            class="px-4 py-2 text-xs font-bold text-white bg-blue-600 hover:bg-blue-700 rounded transition-colors shadow-sm disabled:bg-gray-300 disabled:cursor-not-allowed">
            <i class="fa-solid fa-download mr-1" v-if="!isImporting"></i>
            <i class="fa-solid fa-spinner fa-spin mr-1" v-else></i>
            {{ isImporting ? '正在导入...' : '导入选中模板' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'

const props = defineProps({
  item: {
    type: Object,
    default: () => ({})
  }
})

// 表单数据
const formData = reactive({
  companyName: '',
  companyAddress: '',
  companyPhone: '',
  companyFax: '',
  companyWebsite: '',
  service400Phone: '',
  serviceEmail: '',
  serviceQRCode: '',
  appQRCodeAndroid: '',
  appQRCodeIOS: '',
  productNameRequirement: '',
  monitorWeb: false,
  monitorApp: false,
  companyLogo: '',
  coverColor: '#000000'
})

// 文件输入引用
const serviceQRCodeInput = ref(null)
const appQRCodeAndroidInput = ref(null)
const appQRCodeIOSInput = ref(null)
const companyLogoInput = ref(null)

// 图片预览
const previewImageUrl = ref(null)

// 最后更新时间
const lastUpdateTime = ref('')

// API 基础 URL（可根据环境配置调整）
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5010'

// 导入模板相关
const showImportModal = ref(false)
const selectedTemplateId = ref(null)
const templates = ref([])
const isLoadingTemplates = ref(false)
const isImporting = ref(false)

// 触发文件上传
function triggerFileUpload(field) {
  const inputMap = {
    serviceQRCode: serviceQRCodeInput,
    appQRCodeAndroid: appQRCodeAndroidInput,
    appQRCodeIOS: appQRCodeIOSInput,
    companyLogo: companyLogoInput
  }
  
  const input = inputMap[field]?.value
  if (input) {
    input.click()
  }
}

// 处理图片上传
function handleImageUpload(event, field) {
  const file = event.target.files[0]
  if (!file) return

  // 验证文件类型
  if (!file.type.startsWith('image/')) {
    alert('请选择图片文件')
    return
  }

  // 验证文件大小（限制为5MB）
  if (file.size > 5 * 1024 * 1024) {
    alert('图片大小不能超过5MB')
    return
  }

  // 读取文件并转换为base64
  const reader = new FileReader()
  reader.onload = (e) => {
    formData[field] = e.target.result
    updateLastUpdateTime()
  }
  reader.readAsDataURL(file)
  
  // 重置input，允许重复选择同一文件
  event.target.value = ''
}

// 删除图片
function removeImage(field) {
  formData[field] = ''
  updateLastUpdateTime()
}

// 预览图片
function previewImage(url) {
  previewImageUrl.value = url
}

// 打开导入模板弹窗
function openImportModal() {
  // TODO: 从数据库加载模板列表
  // 这里暂时使用模拟数据
  loadTemplatesFromDatabase()
  showImportModal.value = true
  selectedTemplateId.value = null
}

// 从数据库加载模板列表
async function loadTemplatesFromDatabase() {
  isLoadingTemplates.value = true
  try {
    // 调用后端API查询 odm_company_info 表的数据
    const response = await fetch(`${API_BASE_URL}/api/query`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        table_name: 'odm_company_info',
        where_sql: 'is_valid = 1' // 只查询有效记录
      })
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const result = await response.json()
    
    if (!result.success) {
      throw new Error(result.message || '查询失败')
    }

    // 将数据库记录转换为模板格式
    templates.value = result.data.map((record, index) => {
      // 格式化更新时间
      const updateTime = record.update_time 
        ? new Date(record.update_time).toLocaleString('zh-CN', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
          })
        : '未知'

      // 解析 cover_color_card 或 cover_color_plate 获取颜色
      // 如果存储的是颜色值，直接使用；如果是路径，使用默认颜色
      let coverColor = '#000000'
      if (record.cover_color_card) {
        // 尝试从色卡路径中提取颜色，或使用默认值
        coverColor = record.cover_color_card.startsWith('#') 
          ? record.cover_color_card 
          : '#000000'
      } else if (record.cover_color_plate) {
        coverColor = record.cover_color_plate.startsWith('#') 
          ? record.cover_color_plate 
          : '#000000'
      }

      // 判断监控功能（根据 app 和 cloud 字段）
      const monitorApp = !!record.app
      const monitorWeb = !!record.cloud

      return {
        id: record.id,
        odmName: record.odm_name || '', // 保存 odm_name 用于后续查询
        name: record.company_name || record.odm_name || `模板 ${index + 1}`,
        category: record.odm_code || '标准',
        description: record.company_name 
          ? `${record.company_name} - ${record.odm_name || ''}`.trim()
          : 'ODM公司信息模板',
        updateTime: updateTime,
        data: {
          companyName: record.company_name || '',
          companyAddress: record.company_address || '',
          companyPhone: record.company_phone || '',
          companyFax: record.company_fax || '',
          companyWebsite: record.company_website || '',
          service400Phone: record.service_400_phone || '',
          serviceEmail: record.service_email || '',
          productNameRequirement: record.product_model_rule || '',
          monitorWeb: monitorWeb,
          monitorApp: monitorApp,
          coverColor: coverColor
        }
      }
    })

    console.log(`成功加载 ${templates.value.length} 个模板`)
  } catch (error) {
    console.error('加载模板列表失败:', error)
    alert(`加载模板列表失败: ${error.message}`)
    // 如果加载失败，使用空数组
    templates.value = []
  } finally {
    isLoadingTemplates.value = false
  }
}

// 选择模板
function selectTemplate(template) {
  selectedTemplateId.value = template.id
}

// 导入模板
async function importTemplate() {
  if (!selectedTemplateId.value) {
    alert('请先选择一个模板')
    return
  }
  
  const template = templates.value.find(t => t.id === selectedTemplateId.value)
  if (!template) {
    alert('模板不存在')
    return
  }
  
  // 确认导入
  if (!confirm(`确定要导入模板"${template.name}"吗？这将覆盖当前表单数据。`)) {
    return
  }

  // 如果没有 odm_name，使用已加载的数据
  if (!template.odmName) {
    Object.assign(formData, {
      ...template.data,
      // 图片字段不导入，保持为空
      serviceQRCode: '',
      appQRCodeAndroid: '',
      appQRCodeIOS: '',
      companyLogo: ''
    })
    updateLastUpdateTime()
    showImportModal.value = false
    alert('模板导入成功！')
    return
  }

  // 基于 odm_name 查询数据库获取完整数据
  isImporting.value = true
  try {
    // 转义单引号防止 SQL 注入（SQL 标准：单引号用两个单引号转义）
    const escapedOdmName = template.odmName.replace(/'/g, "''")
    // 构建 WHERE 条件：使用 odm_name 查询，并确保记录有效
    const whereSql = `odm_name = '${escapedOdmName}' AND is_valid = 1`
    
    const response = await fetch(`${API_BASE_URL}/api/query`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        table_name: 'odm_company_info',
        where_sql: whereSql
      })
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const result = await response.json()
    
    if (!result.success) {
      throw new Error(result.message || '查询失败')
    }

    if (!result.data || result.data.length === 0) {
      alert(`未找到 odm_name 为 "${template.odmName}" 的记录`)
      return
    }

    // 获取第一条匹配的记录（应该只有一条，因为 odm_name 应该是唯一的）
    const record = result.data[0]

    // 解析 cover_color_card 或 cover_color_plate 获取颜色
    let coverColor = '#000000'
    if (record.cover_color_card) {
      coverColor = record.cover_color_card.startsWith('#') 
        ? record.cover_color_card 
        : '#000000'
    } else if (record.cover_color_plate) {
      coverColor = record.cover_color_plate.startsWith('#') 
        ? record.cover_color_plate 
        : '#000000'
    }

    // 判断监控功能
    const monitorApp = !!record.app
    const monitorWeb = !!record.cloud

    // 导入完整数据到表单
    Object.assign(formData, {
      companyName: record.company_name || '',
      companyAddress: record.company_address || '',
      companyPhone: record.company_phone || '',
      companyFax: record.company_fax || '',
      companyWebsite: record.company_website || '',
      service400Phone: record.service_400_phone || '',
      serviceEmail: record.service_email || '',
      productNameRequirement: record.product_model_rule || '',
      monitorWeb: monitorWeb,
      monitorApp: monitorApp,
      coverColor: coverColor,
      // 图片字段不导入，保持为空（因为这些是文件路径，需要单独处理）
      serviceQRCode: '',
      appQRCodeAndroid: '',
      appQRCodeIOS: '',
      companyLogo: ''
    })
    
    updateLastUpdateTime()
    showImportModal.value = false
    alert('模板导入成功！')
    
  } catch (error) {
    console.error('导入模板失败:', error)
    alert(`导入模板失败: ${error.message}`)
  } finally {
    isImporting.value = false
  }
}

// 更新表单到数据库
async function updateForm() {
  // 验证必填字段
  if (!formData.companyName.trim()) {
    alert('请填写公司全称')
    return
  }

  try {
    // TODO: 调用数据库API更新数据
    // const response = await fetch('/api/product-form', {
    //   method: 'PUT',
    //   headers: {
    //     'Content-Type': 'application/json',
    //   },
    //   body: JSON.stringify({
    //     instanceId: props.item?.instanceId,
    //     formData: formData
    //   })
    // })
    // 
    // if (!response.ok) {
    //   throw new Error('更新失败')
    // }
    
    // 模拟更新
    console.log('更新表单数据到数据库（待实现）:', formData)
    console.log('实例ID:', props.item?.instanceId)
    
    // 更新本地存储
    const key = `productForm_${props.item?.instanceId || 'default'}`
    localStorage.setItem(key, JSON.stringify(formData))
    
    updateLastUpdateTime()
    alert('更新成功！')
    
    // 可以触发事件通知父组件
    // emit('update', formData)
  } catch (error) {
    console.error('更新失败:', error)
    alert('更新失败，请稍后重试')
  }
}

// 重置表单（保留此函数，可能在其他地方使用）
function resetForm() {
  if (confirm('确定要重置所有表单数据吗？')) {
    Object.keys(formData).forEach(key => {
      if (typeof formData[key] === 'boolean') {
        formData[key] = false
      } else if (key === 'coverColor') {
        formData[key] = '#000000'
      } else {
        formData[key] = ''
      }
    })
    updateLastUpdateTime()
  }
}

// 更新最后更新时间
function updateLastUpdateTime() {
  const now = new Date()
  lastUpdateTime.value = now.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 初始化时加载已保存的数据（如果有）
onMounted(() => {
  // 可以从 localStorage 或 props.item 中加载数据
  const savedData = localStorage.getItem(`productForm_${props.item?.instanceId || 'default'}`)
  if (savedData) {
    try {
      const parsed = JSON.parse(savedData)
      Object.assign(formData, parsed)
    } catch (e) {
      console.error('加载数据失败:', e)
    }
  }
  
  updateLastUpdateTime()
  
  // 监听表单变化，自动保存到 localStorage
  // 这里可以使用 watch 或 watchEffect 来实现自动保存
})

// 监听表单变化，自动保存
watch(() => formData, (newData) => {
  const key = `productForm_${props.item?.instanceId || 'default'}`
  localStorage.setItem(key, JSON.stringify(newData))
}, { deep: true })
</script>

<style scoped>
/* 表单样式 */
.form-group {
  @apply mb-4;
}

.form-label {
  @apply block text-xs font-semibold text-gray-700 mb-2;
}

.form-input {
  @apply w-full px-3 py-2 bg-white border border-gray-300 rounded text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-colors;
}

.form-textarea {
  @apply w-full px-3 py-2 bg-white border border-gray-300 rounded text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-colors resize-none;
}

.form-checkbox {
  @apply w-4 h-4 text-blue-600 bg-white border-gray-300 rounded focus:ring-blue-500 focus:ring-2;
}

/* 图片上传样式 */
.image-upload-container {
  @apply relative;
}

.image-upload-placeholder {
  @apply w-32 h-32 border-2 border-dashed border-gray-300 rounded flex flex-col items-center justify-center cursor-pointer hover:border-blue-500 hover:bg-gray-50 transition-colors;
}

.image-preview {
  @apply w-32 h-32 rounded border border-gray-300 overflow-hidden cursor-pointer relative;
}

.image-preview img {
  @apply w-full h-full object-cover;
}

.image-overlay {
  @apply absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 flex items-center justify-center transition-opacity;
}

.image-overlay i {
  @apply text-white text-xl;
}

.logo-container .image-upload-placeholder,
.logo-container .image-preview {
  @apply w-40 h-40;
}

/* 颜色选择器样式 */
.color-picker {
  @apply w-12 h-10 border border-gray-300 rounded cursor-pointer bg-white;
}

.color-preview {
  @apply w-10 h-10 border border-gray-300 rounded;
}

/* 自定义复选框样式 */
input[type="checkbox"]:checked {
  @apply bg-blue-600 border-blue-600;
}

input[type="checkbox"] {
  appearance: none;
  -webkit-appearance: none;
  @apply border-2 border-gray-300 rounded;
}

input[type="checkbox"]:checked::before {
  content: '✓';
  @apply text-white text-xs flex items-center justify-center;
  display: flex;
  width: 100%;
  height: 100%;
  align-items: center;
  justify-content: center;
}
</style>
