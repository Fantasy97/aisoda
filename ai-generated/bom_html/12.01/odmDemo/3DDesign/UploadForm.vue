<template>
  <Dialog v-model="dialogVisible" :title="dialogTitle" width="50%">
    <el-form ref="formRef" v-loading="formLoading" label-width="100px">
      <el-form-item label="上传模型" prop="imagePathPanel">
        <el-upload
          ref="uploadRefPanel"
          v-model:file-list="fileListPanel"
          action="#"
          :auto-upload="true"
          :data="dataImagePanel"
          :disabled="formLoading"
          :on-error="submitFormError"
          :on-success="glbSuccess"
          :on-exceed="handleExceedPanel"
          :http-request="httpRequestOss"
          accept=".glb, .gltf"
          :before-upload="beforeUpload"
          v-loading="formLoading"
          :show-file-list="false"
          drag
        >
          <i class="el-icon-upload"></i>
          <div class="el-upload__text"> 将文件拖到此处，或 <em>点击上传</em></div>
          <template #tip>
            <div class="el-upload__tip" style="color: red">
              提示：仅允许导入 "glb, gltf" 格式文件
            </div>
          </template>
        </el-upload>
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="cancelForm">关闭</el-button>
    </template>
  </Dialog>

  <Dialog v-model="dialogVisible2" :title="dialogTitle2" width="50%">
    <el-form ref="formRef" v-loading="formLoading" label-width="100px">
      <el-form-item label="上传svg" prop="imagePathPanel">
        <el-upload
          ref="uploadRefPanel"
          v-model:file-list="fileListPanel"
          action="#"
          :auto-upload="true"
          :data="dataImagePanel"
          :disabled="formLoading"
          :on-error="submitFormError"
          :on-success="svgSuccess"
          :on-exceed="handleExceedPanel"
          :http-request="httpRequestOss"
          accept=".svg"
          :before-upload="beforeUpload2"
          v-loading="formLoading"
          :show-file-list="false"
          drag
        >
          <i class="el-icon-upload"></i>
          <div class="el-upload__text"> 将文件拖到此处，或 <em>点击上传</em></div>
          <template #tip>
            <div class="el-upload__tip" style="color: red"> 提示：仅允许上传 "svg" 格式文件 </div>
          </template>
        </el-upload>
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="cancelForm">关闭</el-button>
    </template>
  </Dialog>
</template>
<script lang="ts" setup>
import { useUpload } from '@/views/aiManage/uploadFile/useUpload'
import { useUploadStoreWithOut } from '@/store/modules/upload'

defineOptions({ name: 'DocumentForm' })

const { t } = useI18n() // 国际化
const message = useMessage() // 消息弹窗
const dialogVisible = ref(false) // 弹窗的是否展示
const dialogVisible2 = ref(false) // 弹窗的是否展示
const dialogTitle = ref('') // 弹窗的标题
const dialogTitle2 = ref('') // 弹窗的标题
const formLoading = ref(false) // 表单的加载中：1）修改时的数据加载；2）提交的按钮禁用
const formRef = ref() // 表单 Ref

const fileListPanel = ref([]) // 文件列表
const dataImagePanel = ref({ path: '' })
const uploadRef = ref()
const uploadRefPanel = ref()
const uploadStore = useUploadStoreWithOut()
uploadStore.folder = 'odm-custom'

const { httpRequestOss } = useUpload()

// 上传之前
const beforeUpload = (file) => {
  console.log('beforeUpload', file)
  formLoading.value = true
  // 使用 endsWith 方法判断是否以 ".glb" 结尾 file.type 为空串所以用name判断
  const isGlbFile = file.name.endsWith('.glb')
  if (!isGlbFile) {
    message.error('上传文件只能是glb格式!')
    formLoading.value = false
    return false
  }
  return true
}

const beforeUpload2 = (file) => {
  formLoading.value = true
  // 使用 endsWith 方法判断是否以 ".glb" 结尾 file.type 为空串所以用name判断
  const isGlbFile = file.name.endsWith('.svg')
  if (!isGlbFile) {
    message.error('上传文件只能是svg格式!')
    formLoading.value = false
    return false
  }
  return true
}
// 上传glb 成功
const glbSuccess = (e) => {
  formLoading.value = false
  unref(uploadRefPanel)?.clearFiles()
  // 清除该字段的校验
  unref(formRef.value)?.clearValidate('imagePathPanel')
  // 提示成功，并刷新
  message.success(t('cropper.uploadSuccess'))
  emit('success', e.data, '3D')
  cancelForm()
}

// 上传glb 成功
const svgSuccess = (e) => {
  formLoading.value = false
  unref(uploadRefPanel)?.clearFiles()
  // 清除该字段的校验
  unref(formRef.value)?.clearValidate('imagePathPanel')
  // 提示成功，并刷新
  message.success(t('cropper.uploadSuccess'))
  emit('success', e.data, 'svg')
  cancelForm()
}

/** 文件数超出提示 */
const handleExceedPanel = (): void => {
  message.error('最多只能上传一个文件！')
  formLoading.value = false
}

/** 上传错误提示 */
const submitFormError = (): void => {
  message.error('上传失败，请您重新上传！')
  formLoading.value = false
}

/** 打开弹窗 */
const open = async (type: string) => {
  if (type == '3D') {
    dialogVisible.value = true
    dialogTitle.value = '上传模型'
  } else {
    dialogVisible2.value = true
    dialogTitle2.value = '上传svg'
  }
  resetForm()
}
defineExpose({ open }) // 提供 open 方法，用于打开弹窗

/** 提交表单 */
const emit = defineEmits(['success', 'imageSize']) // 定义 success 事件，用于操作成功后的回调

const cancelForm = async () => {
  dialogVisible.value = false
  dialogVisible2.value = false
  resetForm()
}

/** 重置表单 */
const resetForm = () => {
  // formRef.value?.resetFields()
  // 重置上传状态和文件
  formLoading.value = false
  uploadRef.value?.clearFiles()
}
</script>

<style lang="scss" scoped>
.avatar-uploader {
  width: 200px;
  height: 150px;
  display: block;
  margin-left: 20px;
}

.preview-area {
  display: flex;
  margin-left: 5px;
  .tag {
    margin-right: 5px;
    border: none;
  }
}
.color-preview {
  width: 30px;
  height: 30px;
  margin-right: 5px;
  border-radius: 50%;
}

.color-wrap {
  display: flex;
  align-items: center;
}
</style>
