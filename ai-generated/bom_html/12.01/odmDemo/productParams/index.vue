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
      <div class="model-wrap" id="target-one">
        <div class="product-model">
          <div class="title model-title">产品型号</div>
          <el-radio value="all">全部</el-radio>
          <el-checkbox-group v-model="checkboxGroup" size="small">
            <el-checkbox
              :label="item.label"
              border
              v-for="(item, index) in checkboxOptionsComp"
              :key="index"
              @change="checkboxChange"
            />
          </el-checkbox-group>
        </div>
        <div class="params-select mt-10px">
          <div class="title model-title">筛选配置</div>
          <el-checkbox-group v-model="paramsSelectGroup" size="small">
            <el-checkbox
              :label="item.label"
              border
              v-for="(item, index) in paramsSelectOptions"
              :key="index"
              @change="paramsSelectChange"
            />
          </el-checkbox-group>
        </div>
      </div>
      <el-divider />
      <div class="config-wrap" id="target-two">
        <el-table
          :data="resDataComp"
          style="width: 100%"
          stripe
          row-key="label"
          border
          max-height="600"
          :span-method="spanMethod"
        >
          <el-table-column
            v-for="(item, index) in columns"
            :key="index"
            :prop="item.prop"
            :label="item.label"
            :fixed="item.fixed"
            :width="item.width"
          >
            <template #default="{ row }">
              <span v-if="item.prop === 'label'">{{ row.label }}</span>
              <div v-for="(item2, index2) in row.seriesArr" :key="index2" class="series-arr">
                <span
                  v-if="
                    item.prop != 'label' && item.label === item2.seriesName && !item2.optionsArr
                  "
                  >{{ item2.value }}
                </span>
                <div
                  v-for="(item3, index3) in item2.optionsArr"
                  :key="index3"
                  class="options-arr mr-10px"
                >
                  <el-checkbox
                    class="mr-10px!"
                    v-if="
                      item.prop != 'label' &&
                      item.label === item2.seriesName &&
                      row.isOptional &&
                      item3.isOptional
                    "
                    v-model="item3.isChecked"
                    size="large"
                  />
                  <span v-if="item.prop != 'label' && item.label === item2.seriesName">{{
                    item3.name
                  }}</span>
                </div>
              </div>
            </template>
          </el-table-column>
        </el-table>

        <div class="mt-50px">修改产品系列或型号名称：</div>
        <el-form
          ref="formRef"
          style="max-width: 600px"
          :model="form"
          status-icon
          label-width="auto"
          id="target-three"
        >
          <el-form-item label="系列名" prop="name" class="mt-20px">
            <div class="model-name">
              <div>{{ product.name }}</div>
              <el-input
                v-model="form.productName"
                placeholder="请输入新的系列名"
                autocomplete="off"
                class="!w-240px"
                clearable
              />
            </div>
          </el-form-item>

          <el-form-item
            :label="`型号${index + 1}`"
            :prop="'domains.' + index + '.value'"
            v-for="(item, index) in form.domains"
            :key="index"
            class="mt-20px"
          >
            <div class="model-name">
              <div>{{ item.originalName }}</div>
              <el-input
                v-model="item.newName"
                placeholder="请输入新的型号名"
                autocomplete="off"
                class="!w-240px"
                clearable
              />
            </div>
          </el-form-item>
        </el-form>
      </div>
      <div class="btn-wrap">
        <el-button type="primary" round @click="submitForm(formRef)">提交</el-button>
      </div>
    </div>
  </ContentWrap>
  <Tour v-model="tourOpen" :data="productParams" />
</template>
<script lang="ts" setup>
import { useRouter } from 'vue-router'
import { useOdmStoreWithOut } from '@/store/modules/odm'
import { resData2 } from '@/views/odmDemo/productParams/res.data1'
import Steps from '@/views/odmDemo/productList/steps.vue'
import Tour from '@/views/odmDemo/productList/Tour.vue'
import { productParams } from '@/views/odmDemo/productList/tour.json'

const odmStore = useOdmStoreWithOut()
defineOptions({ name: 'ProductParamsDemo' })
const router = useRouter()
const active = ref(0)

const product = reactive({
  name: 'ASW S 系列（6-10kW）',
  url: 'https://aiswei.oss-cn-hangzhou.aliyuncs.com/uat/odm-custom/2528221725418268265.png?Expires=2040951068&OSSAccessKeyId=LTAI5t8LAfU5VdgxF6NnVu2w&Signature=lGPVfRq%2BiiH85Cw5kuR8aOFs0DY%3D'
})
const checkboxGroup = ref([])
let checkboxOptions = ref([])

const paramsSelectGroup = ref([])
const paramsSelectOptions = reactive([
  {
    label: '标配',
    value: '1'
  },
  {
    label: '选配',
    value: '2'
  }
])

const columns = ref([{ prop: 'label', label: '参数', width: '300', fixed: true }])

// 用于生成新的prop名称的函数
function generateNewPropName(index) {
  return `seriesName${index + 1}`
}

// 遍历并添加数据
const addColumnsFromSeriesArr = async (seriesArr) => {
  seriesArr.forEach((item, index) => {
    const propName = generateNewPropName(index)
    columns.value.push({
      prop: propName,
      label: item.seriesName,
      width: '300',
      fixed: false
    })
  })
}
const columnsFun = async () => {
  const seriesArr = resData2[0].children[0].seriesArr
  await addColumnsFromSeriesArr(seriesArr)
  return columns.value
}

// 更新复选框的状态
const updateCheckbox = (row, prop, value) => {
  row[`${prop}Checked`] = value
}

const formRef = ref()
const form = reactive({
  productName: '',
  domains: []
})

// 漫游式引导
const tourOpen = ref(false)
const openDemo = () => {
  tourOpen.value = true
}

const checkboxOptionsComp = computed(() => {
  const seriesArr = resData2[0].children[0].seriesArr
  checkboxOptions.value = seriesArr.map((item) => {
    return { label: item.seriesName, value: item.seriesName }
  })
  return checkboxOptions.value
})

/** 初始化 **/
onMounted(async () => {
  if (odmStore.isOpenDemo) {
    openDemo()
    checkboxGroup.value.push('ASW6000-S')
  }

  await columnsFun()
})

const submitForm = (formEl) => {
  router.push({
    name: '3DDesignDemo'
  })
  odmStore.productStatus = '设计'
  if (!formEl) return
  formEl.validate((valid) => {
    if (valid) {
      console.log('submit!', form)
    } else {
      console.log('error submit!')
    }
  })
}

const spanMethod = ({ row, columnIndex }) => {
  if (row.children && columnIndex == 1) {
    return {
      rowspan: 1,
      colspan: 3
    }
  } else {
    return {
      rowspan: 1,
      colspan: 1
    }
  }
}

function transformArray(arr) {
  console.log('arr', arr)
  const labelObj = { prop: 'label', label: '参数', width: '300', fixed: true }
  return arr.reduce((acc, item, index) => {
    if (index === 0) {
      acc.push(labelObj) // 只在第一个元素时添加 labelObj
    }
    acc.push({ prop: 'value', label: item, width: '300', fixed: false })
    return acc
  }, [])
}
// 产品型号复选框
const checkboxChange = () => {
  console.log(checkboxGroup.value)
  syncArrays()
  // 动态展示表格列
  if (checkboxGroup.value.length) {
    columns.value = transformArray(checkboxGroup.value)
  } else {
    const seriesArr = resData2[0].children[0].seriesArr
    const seriesNames = seriesArr.map((item) => item.seriesName)
    columns.value = transformArray(seriesNames)
  }
}

const paramsSelectChange = () => {
  console.log(paramsSelectGroup.value)
}

// 过滤出 isOptional: true 的项
const resDataComp = computed(() => {
  let result: any[] = []

  paramsSelectGroup.value.forEach((item) => {
    if (item === '标配') {
      result.push(
        ...resData2.map((section) => ({
          ...section,
          children: section.children.filter((child) => !child.isOptional)
        }))
      )
    } else if (item === '选配') {
      result.push(
        ...resData2
          .map((section) => ({
            ...section,
            children: section.children.filter((child) => child.isOptional)
          }))
          .filter((section) => section.children.length > 0)
      )
    }
  })
  if (paramsSelectGroup.value.length === 0 || paramsSelectGroup.value.length == 2) {
    result = [...resData2]
  }

  return result
})

// 创建一个函数用于转换 arr2 到 arr 的形式
const convertArr2ToArr = () => {
  return checkboxGroup.value.map((item) => ({
    originalName: String(item),
    newName: ''
  }))
}

// 更新 arr 基于 arr2 的值
const syncArrays = () => {
  form.domains = convertArr2ToArr()
}
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
    .product-model,
    .params-select {
      display: flex;
      align-items: center;
    }

    .model-title {
      margin-right: 50px;
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
  .model-name {
    display: flex;
    align-items: center;
    justify-content: space-between;
    min-width: 400px;
  }
  :deep(.el-table__placeholder) {
    width: 0;
  }

  .config-wrap {
    .el-checkbox {
      height: 0;
    }
  }

  :deep(.el-table__indent) {
    padding-left: 8px !important;
  }
  .series-arr {
    display: flex;
    align-items: center;
  }
  .options-arr {
    display: flex;
    align-items: center;
  }
}
</style>
