<template>
  <div>
    <el-row :gutter="20">
      <el-col :span="18" id="enterpriseInfo">
        <ContentWrap>
          <div class="tip custom-block">企业信息</div>
          <el-form
            class="mt-15px"
            :model="basicInfo"
            ref="queryFormRef"
            :inline="false"
            :rules="rules"
            label-width="88px"
          >
            <el-form-item label="公司名称" prop="company">
              <el-input
                v-model="basicInfo.company"
                placeholder="请输入公司名称"
                clearable
                class="!w-700px"
              />
            </el-form-item>
            <el-form-item label="简称" prop="shortName">
              <el-input
                v-model="basicInfo.shortName"
                placeholder="请输入简称"
                clearable
                class="!w-700px"
              />
            </el-form-item>
            <el-form-item label="公司地址" prop="address">
              <el-input
                v-model="basicInfo.address"
                placeholder="请输入公司地址"
                clearable
                class="!w-700px"
              />
            </el-form-item>
            <el-form-item label="服务热线" prop="hotline">
              <el-input
                v-model="basicInfo.hotline"
                placeholder="请输入服务热线"
                clearable
                class="!w-700px"
              />
            </el-form-item>
            <el-form-item label="邮箱" prop="email">
              <el-input
                v-model="basicInfo.email"
                placeholder="请输入邮箱"
                clearable
                class="!w-700px"
              />
            </el-form-item>
            <el-form-item label="网址" prop="url">
              <el-input
                v-model="basicInfo.url"
                placeholder="请输入网址"
                clearable
                class="!w-700px"
              />
            </el-form-item>
            <el-form-item label="传真" prop="fax">
              <el-input
                v-model="basicInfo.fax"
                placeholder="请输入传真"
                clearable
                class="!w-700px"
              />
            </el-form-item>
            <el-form-item label="二维码" prop="QRCodeFileList">
              <el-image
                v-if="qrImage"
                style="width: 100px; height: 100px; margin: 0 50px 0 10px"
                :src="qrImage"
                :zoom-rate="1.2"
                :max-scale="7"
                :min-scale="0.2"
                :initial-index="4"
                :preview-src-list="[qrImage]"
                fit="cover"
              />
              <el-upload
                ref="uploadRefImage"
                v-model:file-list="basicInfo.QRCodeFileList"
                action="#"
                :auto-upload="false"
                :data="dataImage"
                :disabled="formLoading"
                :on-change="handleFileChangeQRCode"
                :on-error="submitFormError"
                :on-success="submitFormSuccess"
                :on-exceed="handleExceed"
                :http-request="httpRequest"
                accept=".jpg, .jpeg, .png"
                :before-upload="beforeUploadImage"
                v-loading="formLoading"
                :show-file-list="false"
                drag
              >
                <i class="el-icon-upload"></i>
                <div class="el-upload__text"> 将文件拖到此处，或 <em>点击上传</em></div>
                <template #tip>
                  <div class="el-upload__tip" style="color: red">
                    支持JPG/PNG/JPEG格式的图片大小＜5M
                  </div>
                </template>
              </el-upload>
            </el-form-item>
            <el-form-item label="Logo管理" prop="logoDefault">
              <div class="logo-default">
                <el-radio size="large" :label="1" v-model="radioValue">默认</el-radio>
                <el-image
                  style="width: 100px; height: 100px"
                  :src="defaultUrl"
                  :preview-src-list="[defaultUrl]"
                />
              </div>
            </el-form-item>
            <el-form-item prop="logoFileList">
              <div class="logo-manage">
                <el-radio size="large" :label="2" v-model="radioValue">logo管理</el-radio>
                <div class="manage">
                  <el-image
                    v-if="logoImage"
                    style="width: 100px; height: 100px; margin: 0 50px 0 10px"
                    :src="logoImage"
                    :zoom-rate="1.2"
                    :max-scale="7"
                    :min-scale="0.2"
                    :initial-index="4"
                    :preview-src-list="[logoImage]"
                    fit="cover"
                  />
                  <el-upload
                    ref="uploadRefImage"
                    v-model:file-list="basicInfo.logoFileList"
                    action="#"
                    :auto-upload="false"
                    :data="dataImage"
                    :disabled="formLoading"
                    :on-change="handleFileChangeLogo"
                    :on-error="submitFormError"
                    :on-success="submitFormSuccess"
                    :on-exceed="handleExceed"
                    :http-request="httpRequest"
                    accept=".jpg, .jpeg, .png"
                    :before-upload="beforeUploadImage"
                    v-loading="formLoading"
                    :show-file-list="false"
                    drag
                  >
                    <i class="el-icon-upload"></i>
                    <div class="el-upload__text"> 将文件拖到此处，或 <em>点击上传</em></div>
                    <template #tip>
                      <div class="el-upload__tip" style="color: red">
                        支持JPG/PNG/JPEG格式的图片大小＜5M
                      </div>
                    </template>
                  </el-upload>
                </div>
              </div>
            </el-form-item>
            <el-form-item>
              <el-button id="submit" type="primary" plain @click="submitForm(queryFormRef)">
                提交
              </el-button>
            </el-form-item>
          </el-form>
        </ContentWrap></el-col
      >
      <el-col :span="6" id="salesInfo">
        <ContentWrap>
          <div class="tip custom-block">AISWEI 联系人</div>
          <el-form class="mt-15px" :model="basicInfo" :inline="true" label-width="68px">
            <el-form-item label="销售" prop="templateCode">
              <el-select v-model="contact.sell" placeholder="请选择销售" class="!w-150px">
                <el-option
                  v-for="item in sellOptions"
                  :key="item.value"
                  :label="item.label"
                  :value="item.value"
                />
              </el-select>
            </el-form-item>
            <el-form-item label="电话" prop="sellTel">
              <el-input
                v-model="contact.sellTel"
                placeholder="请输入电话"
                clearable
                class="!w-150px"
              />
            </el-form-item>
            <el-form-item label="技术支持" prop="support">
              <el-select v-model="contact.support" placeholder="请选择销售" class="!w-150px">
                <el-option
                  v-for="item in supportOptions"
                  :key="item.value"
                  :label="item.label"
                  :value="item.value"
                />
              </el-select>
            </el-form-item>
            <el-form-item label="电话" prop="supportTel">
              <el-input
                v-model="contact.supportTel"
                placeholder="请输入电话"
                clearable
                class="!w-150px"
              />
            </el-form-item>
          </el-form>
        </ContentWrap>
      </el-col>
    </el-row>
  </div>
  <Tour v-model="tourOpen" :data="EIOptions2" @change="tourChange" />
</template>
<script lang="ts" setup>
import * as OdmApi from '@/api/odm'
import { ref } from 'vue'
import { useUpload } from '@/views/aiManage/uploadFile/useUpload'
import type { FormInstance, FormRules } from 'element-plus'
import { useRouter, useRoute } from 'vue-router'
import { useOdmStoreWithOut } from '@/store/modules/odm'
import Tour from '@/views/odmDemo/productList/Tour.vue'
import { EIOptions2 } from '@/views/odmDemo/productList/tour.json'

const odmStore = useOdmStoreWithOut()
const route = useRoute()

defineOptions({ name: 'AddDemo' })
const fileListImage = ref([]) // 文件列表
const dataImage = ref({ path: '' })
const uploadRef = ref()
const uploadRefImage = ref()
const qrImage = ref('')
const logoImage = ref('')
const { httpRequest } = useUpload()
const formLoading = ref(false) // 表单的加载中
const radioValue = ref(1) // 默认选中第一个选项
const router = useRouter()

const message = useMessage() // 消息弹窗
const { t } = useI18n() // 国际化
const defaultUrl = 'https://fuss10.elemecdn.com/e/5d/4a731a90594a4af544c0c25941171jpeg.jpeg'

// 漫游式引导
const tourOpen = ref(false)
const openDemo = () => {
  tourOpen.value = true
}

const tourChange = (step) => {
  console.log('step', step)
}

const basicInfo = reactive({
  company: undefined,
  shortName: undefined,
  address: undefined,
  hotline: undefined,
  email: undefined,
  url: undefined,
  fax: undefined,
  QRCodeFileList: undefined,
  logoFileList: undefined
})

const contact = reactive({
  sell: undefined,
  sellTel: undefined,
  support: undefined,
  supportTel: undefined
})

const sellOptions = reactive([
  {
    label: '朱慧慧',
    value: 1
  }
])

const supportOptions = reactive([
  {
    label: '朱慧慧',
    value: 1
  }
])
const queryFormRef = ref() // 搜索的表单

/** 文件数超出提示 */
const handleExceed = (): void => {
  message.error('最多只能上传一个文件！')
  formLoading.value = false
}

/** 处理上传的文件发生变化 */
const handleFileChangeQRCode = (file) => {
  console.log('file', file)
  dataImage.value.path = file.name
  // 清除该字段的校验
  unref(queryFormRef.value)?.clearValidate('QRCodeFileList')
  fileListImage.value = []
  if (file.raw.type.includes('image')) {
    qrImage.value = URL.createObjectURL(file.raw)
    return false // 返回 false 可以阻止文件上传
  }
}

/** 处理上传的文件发生变化 */
const handleFileChangeLogo = (file) => {
  console.log('file', file)
  dataImage.value.path = file.name
  // 清除该字段的校验
  unref(queryFormRef.value)?.clearValidate('logoFileList')
  fileListImage.value = []
  if (file.raw.type.includes('image')) {
    logoImage.value = URL.createObjectURL(file.raw)
    return false // 返回 false 可以阻止文件上传
  }
}

/** 文件上传成功处理 */
const emit = defineEmits(['success', 'next']) // 定义 success 事件，用于操作成功后的回调
const submitFormSuccess = () => {
  // 清理
  formLoading.value = false
  unref(uploadRef)?.clearFiles()
  unref(uploadRefImage)?.clearFiles()
  // 提示成功，并刷新
  message.success(t('cropper.uploadSuccess'))
  emit('success')
}

const beforeUploadImage = (file) => {
  formLoading.value = true // 开始上传前，设置loading状态为true

  const isImage = file.type.startsWith('image/')

  if (!isImage) {
    message.error('上传文件只能是图片格式!')
    formLoading.value = false
    return false
  }
  return true
}

/** 上传错误提示 */
const submitFormError = (): void => {
  formLoading.value = false
}

const submitForm = async (formEl: FormInstance | undefined) => {
  if (!formEl) return
  // await formEl.validate((valid, fields) => {
  //   if (valid) {
  //     console.log('submit!', basicInfo)
  //   } else {
  //     console.log('error submit!', fields)
  //   }
  // })
  router.push({
    name: 'ProductListDemo'
  })
  message.success('企业信息新增成功！')
  odmStore.companyStatus = true
  tourOpen.value = false
}

const openForm = async () => {
  formLoading.value = true
  const templateCodeList = ruleForm.templateCodeListArr.join(',')
  // 创建一个 FormData 实例
  const formData = new FormData()
  // 添加表单字段
  formData.append('name', ruleForm.name)
  formData.append('templateCodeList', templateCodeList)
  // 添加文件到 FormData
  fileListImage.value.forEach((file) => {
    formData.append('logo', file.raw) // 注意：这里假设 file 对象有一个 raw 属性，它包含 File 或 Blob 对象
  })
  fileList.value.forEach((file) => {
    formData.append('file', file.raw) // 注意：这里假设 file 对象有一个 raw 属性，它包含 File 或 Blob 对象
    formData.append('fileName', file.name)
  })
  // ... 添加其他表单字段
  OdmApi.createImportDataRecord(formData)
    .then((res) => {
      let { code, data } = res
      if (code == 0) {
        loading.value = false
        message.success('保存成功！')
        importDataId.value = data.id
        emit('next')
      }
    })
    .catch((err) => {
      loading.value = false
    })
}

const rules = reactive<FormRules>({
  company: [{ required: true, message: '请输入公司名称', trigger: 'blur' }],
  shortName: [{ required: true, message: '请输入简称', trigger: 'blur' }],
  address: [{ required: true, message: '请输入公司地址', trigger: 'blur' }],
  hotline: [{ required: true, message: '请输入服务热线', trigger: 'blur' }],
  email: [{ required: true, message: '请输入邮箱', trigger: 'blur' }],
  url: [{ required: true, message: '请输入网址', trigger: 'blur' }],
  fax: [{ required: true, message: '请输入传真', trigger: 'blur' }],
  QRCodeFileList: [{ required: true, message: '请上传二维码', trigger: 'change' }],
  logoFileList: [{ required: true, message: '请上传logo', trigger: 'change' }]
})

/** 初始化 **/
onMounted(async () => {
  if (odmStore.isOpenDemo) {
    openDemo()
  }
})
</script>

<style lang="scss" scoped>
.custom-block.tip {
  padding: 0px 16px;
  border-left: 4px solid #409eff;
  margin: 20px 0;
}
.logo-default {
  display: flex;
  flex-direction: column;
}
.logo-manage {
  display: flex;
  flex-direction: column;
  .manage {
    display: flex;
  }
}
</style>
