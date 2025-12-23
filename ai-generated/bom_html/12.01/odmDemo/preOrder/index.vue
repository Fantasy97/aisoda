<template>
  <ContentWrap>
    <Steps :currentStep="active" />
  </ContentWrap>
  <ContentWrap>
    <div class="container">
      <div class="product-wrap">
        <el-image class="product-img" :src="odmStore.url3D || product.url" />
        <div class="name">
          {{ product.name }}
        </div>
      </div>
      <el-divider />
      <div class="model-wrap">
        <div class="title model-title">产品型号</div>
        <div class="mr-30px model-box" v-for="(item, index) in checkboxOptions" :key="index">{{
          item.label
        }}</div>
      </div>
      <el-divider />
      <div class="config-wrap">
        <el-table
          :data="resData2"
          style="width: 100%"
          stripe
          row-key="label"
          border
          max-height="600"
        >
          <el-table-column
            v-for="(item, index) in columns"
            :key="index"
            :prop="item.prop"
            :label="item.label"
            :fixed="item.fixed"
            :width="item.width"
            :type="item.type"
          />
        </el-table>
        <el-form
          ref="ruleFormRef"
          style="max-width: 600px"
          :model="ruleForm"
          status-icon
          label-width="auto"
          class="demo-ruleForm"
        >
          <el-form-item
            label="数量"
            prop="name"
            class="mt-20px"
            v-for="(item, index) in checkboxOptions"
            :key="index"
          >
            <div class="mr-20px">{{ item.label }}</div>
            <el-input-number v-model="item.num" :min="0" @change="numChange" />
          </el-form-item>
          <el-form-item label="总和" prop="name" class="mt-20px">
            <div>{{ totalNum }}</div>
          </el-form-item>
        </el-form>
      </div>
      <div class="btn-wrap">
        <el-button type="primary" round @click="submit">提交</el-button>
      </div>
    </div>
  </ContentWrap>
</template>
<script lang="ts" setup>
import { useRouter } from 'vue-router'
import { useOdmStoreWithOut } from '@/store/modules/odm'
import Steps from '@/views/odmDemo/productList/steps.vue'
import { ElMessageBox } from 'element-plus'

const odmStore = useOdmStoreWithOut()
defineOptions({ name: 'PreOrderDemo' })
const router = useRouter()
const active = ref(4)
const ruleFormRef = ref()
const ruleForm = reactive({
  series: ''
})
const product = reactive({
  num: 0,
  name: 'ASW S 系列（6-10kW）',
  url: 'https://aiswei.oss-cn-hangzhou.aliyuncs.com/uat/odm-custom/4588861725239465281.png?Expires=2040772265&OSSAccessKeyId=LTAI5t8LAfU5VdgxF6NnVu2w&Signature=S8kjqn6TYxkql%2BePrALZOsSwgBI%3D'
})

const checkboxOptions = reactive([
  {
    label: 'SUN2000-2KTL-L1',
    value: 'SUN2000-2KTL-L1',
    num: 0
  },
  {
    label: 'SUN2000-3KTL-L1',
    value: 'SUN2000-3KTL-L1',
    num: 0
  },
  {
    label: 'SUN2000-4KTL-L1',
    value: 'SUN2000-4KTL-L1',
    num: 0
  }
])

// 计算总和
const totalNum = computed(() => {
  return checkboxOptions.reduce((total, item) => total + item.num, 0)
})

const columns = ref([
  { prop: 'label', label: '参数', width: '300', fixed: true },
  { prop: 'value', label: 'ASW6000-S', width: '300' },
  { prop: 'value2', label: 'ASW8000-S', width: '300' },
  { prop: 'value3', label: 'ASW10000-S', width: '300' }
])

const cellStyle = ({ columnIndex }) => {
  if (columnIndex === 0) {
    return { textAlign: 'left' } // 左侧单元格居左
  } else {
    return { textAlign: 'center' } // 右侧单元格居中
  }
}

const spanMethod = ({ row, columnIndex }) => {
  // 判断 value1、value2、value3 和 value4 是否相等
  const valuesAreEqual =
    row.value1 === row.value2 && row.value2 === row.value3 && row.value3 === row.value4

  if (valuesAreEqual && columnIndex == 1) {
    return {
      rowspan: 1,
      colspan: 4
    }
  } else if (valuesAreEqual && columnIndex != 1 && columnIndex != 0) {
    return {
      rowspan: 0,
      colspan: 0
    }
  } else {
    // 如果不相等，则不合并
    return {
      rowspan: 1,
      colspan: 1
    }
  }
}

const numChange = (value: number) => {
  console.log(value)
}

const submit = () => {
  showMessageBox()
  router.push({
    name: 'OrderListDemo'
  })
}

// 显示消息框
const timer = ref<number | null>(null)
const showMessageBox = () => {
  const closeMessageBox = () => {
    if (timer.value !== null) {
      clearTimeout(timer.value)
      timer.value = null
    }
    ElMessageBox.close()
  }

  ElMessageBox({
    message: '下单成功！',
    showCancelButton: false,
    beforeClose: closeMessageBox,
    center: false
  })

  // 设置定时器，在 5 秒后关闭消息框
  timer.value = window.setTimeout(closeMessageBox, 2000)
}

// 在组件卸载时清除定时器
onUnmounted(() => {
  if (timer.value !== null) {
    clearTimeout(timer.value)
  }
})
</script>

<style lang="scss" scoped>
.container {
  .product-wrap {
    display: flex;
    .product-img {
      width: 217px;
      height: 193px;
      border-radius: 0px 0px 0px 0px;
      margin-right: 20px;
    }
    .name {
      padding-top: 5px;
    }
  }
  .model-wrap {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    .model-title {
      margin-right: 50px;
    }
    .model-box {
      min-width: 100px;
      height: 30px;
      border: 1px solid #ccc;
      border-radius: 4px;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 0 8px;
      margin-bottom: 10px;
    }
  }
  .title,
  :deep(.el-collapse-item__header) {
    font-family: 'Inter', Arial, sans-serif;
    font-weight: normal;
    font-size: 16px;
    color: #000000;
    line-height: 19px;
    text-align: left;
    font-style: normal;
    text-transform: none;
  }
  .btn-wrap {
    margin-top: 100px;
  }
}
</style>
