<template>
  <ContentWrap>
    <Steps :currentStep="active" />
  </ContentWrap>
  <ContentWrap id="query-wrap">
    <div class="query-wrap">
      <div class="query-title">储能：</div>
      <el-checkbox-group v-model="checkboxGroup" size="small">
        <el-checkbox
          :label="item.label"
          border
          v-for="(item, index) in checkboxOptions"
          :key="index"
          @change="checkboxChange(item)"
        >
          {{ item.label }}
        </el-checkbox>
      </el-checkbox-group>
      <div class="query-title power-rate">功率：</div>
      <div class="slider-demo-block">
        <el-slider v-model="sliderValue" range :max="100" :marks="marks" @change="sliderChange" />
      </div>
    </div>
  </ContentWrap>
  <ContentWrap id="target-two">
    <div v-if="filteredProducts.length" style="display: flex">
      <div
        class="product-container"
        v-for="(item, index) in filteredProducts"
        :key="index"
        @click="selectProduct(index)"
        :class="{ selected: item.isSelected }"
      >
        <div v-if="item.isSelected" class="checkmark">
          <img src="@/assets/svgs/odm/checkmark.svg" alt="Checkmark" class="check-svg" />
        </div>
        <div class="name">{{ item.name }}</div>
        <div class="status-wrap" v-if="item.status == '折扣'">
          <el-icon class="icon"><Discount /></el-icon>
          <div class="status-text">折扣：立减20%</div>
        </div>
        <div v-else class="status-no"></div>

        <el-image class="product-img" :src="item.url" />
        <div class="more">
          <el-dropdown trigger="click" @command="handleCommand">
            <el-icon class="icon"><MoreFilled /></el-icon>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item
                  :command="item2.value"
                  :icon="icons[item2.icon]"
                  v-for="(item2, index2) in moreOperaOptions"
                  :key="index2"
                  >{{ item2.label }}</el-dropdown-item
                >
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </div>
    </div>
    <el-empty v-else :image-size="150" description="暂无数据" />
  </ContentWrap>
  <div class="btn-wrap">
    <el-button type="primary" round @click="nextPage" id="target-three">下一页</el-button>
    <el-button plain round>取消</el-button>
  </div>
  <Tour v-model="tourOpen" :data="templateSelect" />
</template>

<script lang="ts" setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import Steps from '@/views/odmDemo/productList/steps.vue'
import { useOdmStoreWithOut } from '@/store/modules/odm'
import Tour from '@/views/odmDemo/productList/Tour.vue'
import { templateSelect } from '@/views/odmDemo/productList/tour.json'
import { Tickets, MoreFilled, Plus, CirclePlus, Discount, Document } from '@element-plus/icons-vue'

defineOptions({ name: 'TemplateSelectDemo' })

const active = ref(0)
const checkboxGroup = ref<string[]>([])
const selectedProduct = ref<number | null>(null)
const router = useRouter()
const odmStore = useOdmStoreWithOut()

const checkboxOptions = reactive([
  {
    label: '储能',
    value: '1'
  },
  {
    label: '并网',
    value: '2'
  },
  {
    label: '一体机',
    value: '3'
  }
])

const sliderValue = ref([0, 100])

const tourOpen = ref(false)
const openDemo = () => {
  tourOpen.value = true
}

const marks = reactive({
  0: '0kw',
  100: '100kw',
  50: {
    style: {
      color: '#1989FA'
    },
    label: '50kw'
  }
})

const nextPage = () => {
  router.push({
    name: 'ProductParamsDemo'
  })
  tourOpen.value = false
}

const sliderChange = (val) => {
  console.log(val)
  filteredProducts.value = computeFilteredProducts()
}

const checkboxChange = (item) => {
  console.log(item.value)
  console.log(checkboxGroup.value)
  filteredProducts.value = computeFilteredProducts()
}

const productList = reactive([
  {
    energyStore: '储能',
    isSelected: false,
    name: 'ASW LT-G3 系列 (45kW)',
    status: '量产',
    statusText: '',
    url: 'https://aiswei.oss-cn-hangzhou.aliyuncs.com/uat/odm-custom/2528221725418268265.png?Expires=2040951068&OSSAccessKeyId=LTAI5t8LAfU5VdgxF6NnVu2w&Signature=lGPVfRq%2BiiH85Cw5kuR8aOFs0DY%3D'
  },
  {
    energyStore: '并网',
    isSelected: false,
    name: 'ASW LT-G3 系列 (50kW)',
    status: '审核完成',
    statusText: '',
    url: 'https://aiswei.oss-cn-hangzhou.aliyuncs.com/uat/odm-custom/2528221725418268265.png?Expires=2040951068&OSSAccessKeyId=LTAI5t8LAfU5VdgxF6NnVu2w&Signature=lGPVfRq%2BiiH85Cw5kuR8aOFs0DY%3D'
  },
  {
    energyStore: '一体机',
    isSelected: false,
    name: 'ASW LT-G3 系列 (60kW)',
    status: '折扣',
    statusText: '审核中/试制中/审核失败',
    url: 'https://aiswei.oss-cn-hangzhou.aliyuncs.com/uat/odm-custom/2528221725418268265.png?Expires=2040951068&OSSAccessKeyId=LTAI5t8LAfU5VdgxF6NnVu2w&Signature=lGPVfRq%2BiiH85Cw5kuR8aOFs0DY%3D'
  }
])

const filteredProducts = computed(() => computeFilteredProducts())

const selectProduct = (index: number) => {
  productList.forEach((item, i) => {
    if (i === index) {
      item.isSelected = true
      selectedProduct.value = index
    } else {
      item.isSelected = false
    }
  })
}

/** 初始化 **/
onMounted(async () => {
  if (odmStore.isOpenDemo) {
    openDemo()
  }
})

// 定义图标映射
const icons = {
  Tickets,
  MoreFilled,
  Plus,
  CirclePlus,
  Discount,
  Document
}

const moreOperaOptions = reactive([
  {
    label: '文档管理',
    value: 3,
    icon: 'Tickets'
  },
  {
    label: '基本信息',
    value: 4,
    icon: 'Document'
  }
])

const handleCommand = (command: string | number | object) => {
  console.log(command)
}

// 计算属性，用于过滤产品列表
const computeFilteredProducts = () => {
  // 获取查询范围
  const [min, max] = sliderValue.value

  // 过滤产品列表
  return productList.filter((product) => {
    // 提取功率值
    const power = parseInt(product.name.match(/\((\d+)kW\)/)?.[1], 10)

    // 检查是否在查询范围内并且是否包含特定功率值
    return (
      !isNaN(power) &&
      (power === 45 || power === 50 || power === 60) &&
      power >= min &&
      power <= max &&
      (checkboxGroup.value.length === 0 || checkboxGroup.value.includes(product.energyStore))
    )
  })
}
</script>

<style lang="scss" scoped>
.product-container {
  position: relative;
  margin-right: 53px;
  width: 341px;
  height: 307px;
  background: #fcfdff;
  border-radius: 10px 10px 10px 10px;
  border: 1px solid #d6dff1;
  overflow: hidden;
  cursor: pointer;
  .name {
   font-family: "Inter", Arial, sans-serif;
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
  .status-no {
    margin-top: 11px;
    margin-left: 29px;
    height: 16px;
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
    .icon {
      color: #ff8e25;
    }
    .status-text {
      margin-left: 8px;
     font-family: "Inter", Arial, sans-serif;
      font-weight: 400;
      font-size: 12px;
      color: #ff8e25;
      line-height: 14px;
      text-align: left;
      font-style: normal;
      text-transform: none;
    }
  }

  .product-img {
    width: 217px;
    height: 193px;
    border-radius: 0px 0px 0px 0px;
    margin: 0 auto;
    display: block;
    padding-top: 10px;
  }

  .more {
    width: 28px;
    height: 28px;
    background: #e6f2ff;
    border-radius: 50px;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-left: auto;
    position: absolute;
    top: 14px;
    right: 20px;
    .icon {
      width: 14px;
      height: 14px;
      color: #2788fe;
    }
  }
  .checkmark {
    position: absolute;
    right: 0;
    bottom: 0;
    width: 37px;
    height: 37px;
    background-image: linear-gradient(to bottom right, white 50%, #2788fe 50%);
    .check-svg {
      width: 50%;
      position: absolute;
      bottom: 1px;
      right: 1px;
    }
  }
}
.query-wrap {
  padding: 10px 0 20px 0;
  .query-title {
    margin-bottom: 20px;
   font-family: "Inter", Arial, sans-serif;
    font-weight: normal;
    font-size: 14px;
    color: #000000;
    line-height: 16px;
    text-align: left;
    font-style: normal;
    text-transform: none;
  }
  .power-rate {
    margin-top: 30px;
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
.selected {
  border-color: #2788fe !important; // 或者您想要的颜色
  border-radius: 10px 10px 0 10px;
}
</style>
