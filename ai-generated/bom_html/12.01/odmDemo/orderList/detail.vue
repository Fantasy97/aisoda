<template>
  <Dialog v-model="dialogVisible" :title="dialogTitle" width="50%">
    <el-form
      ref="formRef"
      v-loading="formLoading"
      :model="formData"
      :rules="formRules"
      label-width="100px"
    >
      <el-form-item v-if="formType === 'readonly'" label="公司ID" prop="companyId">
        <el-input
          v-model="formData.companyId"
          placeholder="请输入公司ID"
          :disabled="formType === 'readonly'"
          clearable
        />
      </el-form-item>
      <el-form-item v-if="formType === 'readonly'" label="产品ID" prop="productId">
        <el-input
          v-model="formData.productId"
          placeholder="请输入产品ID"
          :disabled="formType === 'readonly'"
          clearable
        />
      </el-form-item>
      <el-form-item v-if="formType === 'readonly'" label="状态" prop="status">
        <el-input
          v-model="formData.status"
          placeholder="状态"
          :disabled="formType === 'readonly'"
          clearable
        />
      </el-form-item>
      <el-form-item v-if="formType === 'readonly'" label="数量" prop="num">
        <el-input
          v-model="formData.num"
          placeholder="数量"
          :disabled="formType === 'readonly'"
          clearable
        />
      </el-form-item>
      <el-form-item v-if="formType === 'readonly'" label="折扣" prop="discount">
        <el-input
          v-model="formData.discount"
          placeholder="折扣"
          :disabled="formType === 'readonly'"
          clearable
        />
      </el-form-item>
      <el-form-item v-if="formType === 'readonly'" label="金额" prop="money">
        <el-input
          v-model="formData.money"
          placeholder="金额"
          :disabled="formType === 'readonly'"
          clearable
        />
      </el-form-item>
      <el-form-item v-if="formType === 'readonly'" label="创建时间" prop="time">
        <el-input
          v-model="formData.time"
          placeholder="创建时间"
          :disabled="formType === 'readonly'"
          clearable
        />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button v-if="formType !== 'readonly'" @click="cancelForm">取 消</el-button>
      <el-button v-if="formType === 'readonly'" @click="cancelForm">关 闭</el-button>
    </template>
  </Dialog>
</template>
<script lang="ts" setup>
import * as ChannelInfoApi from '@/api/aiManage/channelInfo'

defineOptions({ name: 'OrderDetail' })

const { t } = useI18n() // 国际化
const dialogVisible = ref(false) // 弹窗的是否展示
const dialogTitle = ref('') // 弹窗的标题
const formLoading = ref(false) // 表单的加载中：1）修改时的数据加载；2）提交的按钮禁用
const formType = ref('') // 表单的类型：create - 新增；update - 修改
const formData = ref({
  id: undefined,
  companyId: undefined,
  productId: undefined,
  status: undefined,
  num: undefined,
  discount: undefined,
  money: undefined,
  time: undefined
})
const formRules = reactive({})
const formRef = ref() // 表单 Ref

const fileList = ref([]) // 文件列表
const uploadRef = ref()

// 使用 watch 进行深度监听
watch(
  dialogVisible,
  (newValue) => {
    if (!newValue) {
      fileList.value.length = 0
      resetForm()
    }
  },
  {
    // 是否深度监听（监听对象内部属性的变化）
    deep: false,
    // 是否在初始化时立即执行一次回调
    immediate: false
  }
)

/** 打开弹窗 */
const open = async (type: string, id?: number) => {
  dialogVisible.value = true
  dialogTitle.value = t('action.' + type)
  formType.value = type
  resetForm()
  // 修改时，设置数据
  if (id) {
    formLoading.value = true
    try {
      formData.value = await ChannelInfoApi.getInfoForId(id)
    } finally {
      formLoading.value = false
    }
  }
}
defineExpose({ open }) // 提供 open 方法，用于打开弹窗

/** 提交表单 */
const emit = defineEmits(['success']) // 定义 success 事件，用于操作成功后的回调

const cancelForm = async () => {
  dialogVisible.value = false
  resetForm()
}

/** 重置表单 */
const resetForm = () => {
  formData.value = {
    id: undefined,
    companyId: undefined,
    productId: undefined,
    status: undefined,
    num: undefined,
    discount: undefined,
    money: undefined,
    time: undefined
  }
  formRef.value?.resetFields()
  // 重置上传状态和文件
  formLoading.value = false
  uploadRef.value?.clearFiles()
}
</script>
