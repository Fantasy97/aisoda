<template>
  <ContentWrap class="container">
    <div class="product-wrap">
      <div
        v-show="productList.length"
        class="product-container"
        v-for="(item, index) in productList"
        :key="index"
        id=""
      >
        <div class="name">{{ item.name }}</div>
        <img
          v-if="item.status == '量产'"
          class="corner-mark"
          src="@/assets/svgs/odm/cornerMark.svg"
          alt="corner-mark"
        />
        <img
          v-if="item.status == '审核完成'"
          class="corner-mark"
          src="@/assets/svgs/odm/cornerMark2.svg"
          alt="corner-mark"
        />
        <img
          v-if="item.status != '量产' && item.status != '审核完成'"
          class="corner-mark"
          src="@/assets/svgs/odm/cornerMark3.svg"
          alt="corner-mark"
        />
        <el-popover placement="right" :width="400" trigger="click">
          <template #reference>
            <el-icon class="product-info"><InfoFilled /></el-icon>
          </template>
          <DetailInfo />
        </el-popover>
        <div class="status-text" :style="statusStyle(item)">{{ item.status }}</div>

        <el-image class="product-img" :src="item.url" />
        <div class="btn-group">
          <div class="order" @click="toOrderList">
            <span class="text">
              <el-icon style="margin-right: 2px"> <Tickets /></el-icon>
              订单
            </span>
          </div>

          <div v-if="item.status == '量产'" class="edit">
            <el-popover placement="right" :width="400" trigger="click">
              <template #reference>
                <span class="text">
                  <el-icon style="margin-right: 2px"><Van /></el-icon>
                  物流
                </span>
              </template>
              <Logistics />
            </el-popover>
          </div>
          <div class="look-doc" v-if="item.status == '量产'">
            <el-dropdown trigger="click" @command="handleCommand">
              <span class="text">
                <el-icon style="margin-right: 2px"><Tickets /></el-icon>
                文档下载
              </span>
              <template #dropdown>
                <el-dropdown-menu v-for="(item2, index2) in templateList" :key="index2">
                  <el-dropdown-item
                    :command="item3.templateWebPath"
                    :icon="Document"
                    v-for="(item3, index3) in item2.templateList"
                    :key="index3"
                    >{{ item3.templateName }}{{ index3 + 1 }}
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>
      </div>
      <div class="no-product">
        <div v-if="odmStore.companyStatus" class="add-btn" @click="addProduct" id="Add">
          <el-icon class="avatar-uploader-icon"><Plus /></el-icon>
        </div>
        <div v-if="!productList.length && odmStore.companyStatus" class="mt-20px"
          >暂无产品信息，请新增产品</div
        >
      </div>
    </div>
    <div v-if="!odmStore.companyStatus" class="no-product">
      <div class="add-btn" @click="addCompany" id="Add">
        <el-icon class="avatar-uploader-icon"><Plus /></el-icon>
      </div>
      <div class="mt-20px">暂无企业信息，请新增企业</div>
    </div>
  </ContentWrap>
  <el-button type="primary" @click="openDemoFun">开启引导模式</el-button>
  <el-button plain @click="closeDemoFun">关闭引导模式</el-button>
  <Tour
    v-if="!odmStore.companyStatus"
    v-model="tourOpen"
    :data="EIOptions"
    @skip="tourSkip"
    @change="tourChange"
    @next="nextChange"
  />
  <Tour
    v-if="odmStore.companyStatus"
    v-model="tourOpen"
    :data="productOptions"
    @skip="tourSkip"
    @change="tourChange"
    @next="nextChange"
  />
</template>
<script lang="ts" setup>
import { Tickets, Plus, Document, Van, InfoFilled } from '@element-plus/icons-vue'
import { useRouter, useRoute } from 'vue-router'
import { useOdmStoreWithOut } from '@/store/modules/odm'
import * as OdmApi from '@/api/odm'
import { ref, reactive, watch, onMounted } from 'vue'
import Logistics from '@/views/odmDemo/productList/logistics/index.vue'
import DetailInfo from '@/views/odmDemo/productList/productInfo/index.vue'
import Tour from '@/views/odmDemo/productList/Tour.vue'
import { EIOptions, productOptions } from '@/views/odmDemo/productList/tour.json'

const odmStore = useOdmStoreWithOut()

const route = useRoute()

defineOptions({ name: 'ProductListDemo' })

const loading = ref(false)
const templateList = ref([])

const active = ref(0)
const hasCompany = ref(true)
const router = useRouter()

const toOrderList = () => {
  router.push({
    name: 'OrderListDemo'
  })
}

// 漫游式引导
const tourOpen = ref(false)
const openDemo = () => {
  tourOpen.value = true
}

const openDemoFun = () => {
  odmStore.isOpenDemo = true
  openDemo()
}

const closeDemoFun = () => {
  odmStore.isOpenDemo = false
}

const tourSkip = () => {
  tourOpen.value = false
}

watch(
  () => route.path,
  async (newPath, oldPath) => {
    console.log(`路由从 '${oldPath}' 跳转到了 '${newPath}'`)
    if (oldPath == '/odmDemo/docManageDemo' || oldPath == '/odmDemo/preOrderDemo') {
      productList.forEach((item) => {
        item.status = '量产'
      })
    } else if (oldPath == '/odmDemo/3DDesignDemo') {
      productList.forEach((item) => {
        item.status = '设计'
      })
    }
    if (oldPath == '/odmDemo/Add') {
      if (odmStore.isOpenDemo) {
        openDemo()
      }
    }
  },
  { deep: true }
)

// 产品列表
const productList = reactive([])

/** 获取word模板列表 */
const getList = async () => {
  loading.value = true

  try {
    const data = await OdmApi.getPageAll()
    templateList.value = data
  } finally {
    loading.value = false
  }
}

const handleCommand = (command: string | number | object) => {
  console.log(command)
  window.open(command)
}

const curStep = ref(0)
const tourChange = (step) => {
  console.log('step', step)
  curStep.value = step
}

const nextChange = (step) => {
  console.log(step)
  curStep.value = step
}

const addProduct = () => {
  router.push({
    name: 'TemplateSelectDemo'
  })
  tourOpen.value = false
}

const addCompany = () => {
  router.push({
    name: 'AddDemo'
  })
  tourOpen.value = false
}

// 下单 下单之前先走订单确认
const placeAnOrder = (item) => {
  router.push({
    name: 'PreOrderDemo'
  })
  odmStore.url3D = item.url
}

watch(
  () => [odmStore.productStatus, odmStore.companyStatus], // 返回一个数组
  (newValues, oldValues) => {
    const [newProductStatus, newCompanyStatus] = newValues
    const [oldProductStatus, oldCompanyStatus] = oldValues

    console.log(`newProductStatus from "${oldProductStatus}" to "${newProductStatus}"`)
    console.log(`newCompanyStatus from "${oldCompanyStatus}" to "${newCompanyStatus}"`)

    // 在这里执行你需要的操作
    console.log(111111111, odmStore.productStatus)
    hasCompany.value = odmStore.companyStatus
    if (odmStore.productStatus == '设计') {
      productList.push({
        name: 'ASW S 系列（6-10kW）',
        status: '设计',
        url:
          odmStore.url3D ||
          'https://aiswei.oss-cn-hangzhou.aliyuncs.com/uat/odm-custom/4588861725239465281.png?Expires=2040772265&OSSAccessKeyId=LTAI5t8LAfU5VdgxF6NnVu2w&Signature=S8kjqn6TYxkql%2BePrALZOsSwgBI%3D'
      })
    } else if (odmStore.productStatus == '审核完成') {
      productList[0].status = '审核完成'
    } else if (odmStore.productStatus == '量产') {
      productList[0].status = '量产'
      active.value = 4
      productList[0].url = odmStore.url3D
    }
  },
  {
    deep: true // 由于我们监听的是数组，需要使用 deep 选项来深度监听数组中的每个元素
  }
)

onMounted(async () => {
  await getList()
})

// 计算属性，根据状态返回不同的背景颜色和文字颜色
const statusStyle = (item: any) => {
  let color = ''
  let bgColor = ''

  switch (item.status) {
    case '量产':
      color = '#0978FF'
      bgColor = 'rgba(86, 146, 238, 0.12)'
      break
    case '审核完成':
      color = '#1DD827'
      bgColor = 'rgba(29, 216, 39, 0.12)'
      break
    default:
      color = '#FF8E25'
      bgColor = 'rgba(255, 142, 37, 0.12)'
      break
  }

  return {
    color
    // backgroundColor: bgColor
  }
}
</script>

<style lang="scss" scoped>
.container {
  min-height: calc(100vh - 200px);
  height: calc(100% - 200px);
  .product-wrap {
    display: flex;
    flex-wrap: wrap;
    gap: 30px;
  }
}
.product-container {
  position: relative;
  width: 341px;
  height: 307px;
  background: #fcfdff;
  border-radius: 10px 10px 10px 10px;
  border: 1px solid #d6dff1;
  .name {
    font-family: 'Inter', Arial, sans-serif;
    font-weight: normal;
    font-size: 16px;
    color: #000000;
    line-height: 19px;
    text-align: left;
    font-style: normal;
    text-transform: none;

    padding: 0px 9px;
    border-left: 3px solid #409eff;
    margin-top: 19px;
    margin-left: 17px;
  }
  .corner-mark {
    width: 100px;
    position: absolute;
    top: 0;
    right: -2px;
  }
  .corner-jb {
    width: 40px;
    position: absolute;
    bottom: 30px;
    right: -3px;
  }
  .status-text {
    font-size: 14px;
    -webkit-transform: rotate(45deg); /* Chrome, Safari, Opera */
    -ms-transform: rotate(45deg); /* IE 9 */
    transform: rotate(45deg); /* Standard syntax */
    position: absolute;
    top: 28px;
    right: 22px;
    color: #0978ff;
  }
  .status-wrap {
    display: flex;
    align-items: center;
    margin-top: 11px;
    margin-left: 29px;
    .status {
      padding: 0 10px;
      height: 19px;
      line-height: 19px;
      background: rgba(86, 146, 238, 0.12);
      border-radius: 10px 10px 10px 10px;
      font-size: 12px;
      text-align: center;
    }
  }

  .product-img {
    width: 217px;
    height: 193px;
    border-radius: 0px 0px 0px 0px;
    margin: 0 auto;
    display: block;
    margin-top: 10px;
  }

  .btn-group {
    position: absolute;
    bottom: 20px;
    left: 0;
    display: flex;
    align-items: center;
    width: 100%;
    height: 20px;
    padding: 0 10px;
    box-sizing: border-box;
    .order {
      font-family: 'Inter', Arial, sans-serif;
      font-weight: 500;
      font-size: 14px;
      color: #435b8b;
      line-height: 16px;
      text-align: left;
      font-style: normal;
      text-transform: none;
      display: flex;
      align-items: center;
      margin-right: 30px;
      position: absolute;
      cursor: pointer;
      left: 105px;
      .text {
        margin-left: 4px;
        display: flex;
        align-items: center;
      }
    }
    .delivery {
      font-family: 'Inter', Arial, sans-serif;
      font-weight: 500;
      font-size: 14px;
      color: #435b8b;
      line-height: 16px;
      text-align: left;
      font-style: normal;
      text-transform: none;
      display: flex;
      align-items: center;
      .text {
        margin-left: 4px;
      }
    }
    .more {
      width: 28px;
      height: 28px;
      background: #e6f2ff;
      border-radius: 50px;
      display: flex;
      align-items: center;
      justify-content: center;
      margin-right: 12px;
      .icon {
        width: 14px;
        height: 14px;
        color: #2788fe;
      }
    }
    .more2 {
      position: absolute;
      right: 0;
      margin-right: 0;
    }
    .edit {
      cursor: pointer;
      font-family: 'Inter', Arial, sans-serif;
      font-weight: 500;
      font-size: 14px;
      color: #435b8b;
      line-height: 20px;
      text-align: left;
      font-style: normal;
      text-transform: none;
      display: flex;
      align-items: center;
      position: absolute;
      bottom: 0;
      right: 20px;
      top: 0;
      .text {
        margin-left: 4px;
        display: flex;
        align-items: center;
      }
    }
    .look-doc {
      position: absolute;
      bottom: 0;
      left: 20px;
      top: 0;
      .text {
        color: #435b8b;
        cursor: pointer;
        font-family: 'Inter', Arial, sans-serif;
        font-weight: 500;
        font-size: 14px;
        line-height: 20px;
        text-align: left;
        font-style: normal;
        text-transform: none;
        display: flex;
        align-items: center;
      }
    }
  }
}
.query-wrap {
  .query-title {
    margin-top: 25px;
    margin-bottom: 20px;
    font-family: 'Inter', Arial, sans-serif;
    font-weight: normal;
    font-size: 14px;
    color: #000000;
    line-height: 16px;
    text-align: left;
    font-style: normal;
    text-transform: none;
  }
}

.slider-demo-block {
  max-width: 600px;
  display: flex;
  align-items: center;
}
.slider-demo-block .el-slider {
  margin-top: 0;
  margin-left: 12px;
}
.no-product {
  display: flex;
  justify-content: center;
  flex-direction: column;
}

.add-btn {
  border: 1px dashed #2788fe;
  border-radius: 6px;
  cursor: pointer;
  width: 180px;
  height: 180px;
}

.el-icon.avatar-uploader-icon {
  font-size: 28px;
  color: #2788fe;
  width: 178px;
  height: 178px;
  text-align: center;
}

.product-info {
  position: absolute;
  bottom: 50px;
  right: 5px;
  color: #2788fe;
}
</style>
