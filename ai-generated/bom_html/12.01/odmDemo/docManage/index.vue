<template>
  <ContentWrap>
    <Steps :currentStep="active" />
  </ContentWrap>

  <ContentWrap v-if="!isShowConfirm">
    <el-form :model="form">
      <div>
        <div id="target-one">
          <el-form-item label="模板" :label-width="formLabelWidth" prop="templateCodeListArr">
            <div style="width: 100%">
              <div class="templatelist-arr" v-for="(item, index) in templateListArr" :key="index">
                <el-divider content-position="center">{{ item.templateName }}</el-divider>
                <div class="flex">
                  <div class="book-container">
                    <div
                      class="book-box"
                      v-for="(item2, index2) in item.templateList"
                      :key="index2"
                    >
                      <el-popover placement="bottom" :width="326" trigger="click">
                        <template #reference>
                          <div
                            class="book-thumbnail"
                            :class="{ 'book-thumbnail-two': item2.isSelected }"
                            @click="templatePathFun(item, item2)"
                          >
                            <el-image class="logo-img" :src="logo" alt="logo" />
                            <div class="name">{{ item2.templateName }}</div>
                            <div class="sub-name">{{ item2.subName }}</div>
                            <div class="inverter">
                              <el-image class="inverter-img" :src="odmStore.url3D || inverterImg" />
                            </div>
                          </div>
                        </template>
                        <div class="book-wrap">
                          <el-image class="logo-img" :src="logo" alt="logo" />
                          <div class="name">{{ item2.templateName }}</div>
                          <div class="sub-name">{{ item2.subName }}</div>
                          <div class="inverter">
                            <el-image class="inverter-img" :src="odmStore.url3D || inverterImg" />
                          </div>
                        </div>
                      </el-popover>
                    </div>
                  </div>
                  <el-divider direction="vertical" border-style="dashed" />
                  <div
                    v-show="item2.isSelected"
                    v-for="(item2, index2) in item.templateList"
                    :key="index2"
                  >
                    <el-form-item label="页眉" label-width="50">
                      <el-input
                        v-model="item2.pageHeader"
                        :placeholder="item2.templateName"
                        autocomplete="off"
                        class="!w-240px"
                        clearable
                      />
                    </el-form-item>
                    <el-form-item label="页脚" label-width="50" class="mt-15px">
                      <el-input
                        v-model="item2.pageFooter"
                        :placeholder="item2.templateName"
                        autocomplete="off"
                        class="!w-240px"
                        clearable
                      />
                    </el-form-item>
                  </div>
                </div>
              </div>
            </div>
          </el-form-item>
        </div>
      </div>
    </el-form>
    <div class="btn-wrap">
      <el-button type="primary" round @click="nextPage" id="target-two">下一步</el-button>
    </div>
    <div ref="preview"></div>
  </ContentWrap>
  <designConfirm v-if="isShowConfirm" />
  <Tour v-model="tourOpen" :data="docManage" />
</template>
<script lang="ts" setup>
import { useOdmStoreWithOut } from '@/store/modules/odm'
import * as OdmApi from '@/api/odm'
import designConfirm from './designConfirm.vue'
import Steps from '@/views/odmDemo/productList/steps.vue'
import Tour from '@/views/odmDemo/productList/Tour.vue'
import { docManage } from '@/views/odmDemo/productList/tour.json'
import manualCover from '@/assets/svgs/odm/manualCover.svg'

defineOptions({ name: 'DocManageDemo' })

const odmStore = useOdmStoreWithOut()

const preview = ref()

const active = ref(2)
const formLabelWidth = '100px'
const message = useMessage() // 消息弹窗
const isShowConfirm = ref(false)

const loading = ref(false)
const templateListArr = ref([])

// 预览文档 打开新窗口
const previewDocument = (url) => {
  // 检查URL是否有效
  if (!url) {
    message.error('无效的文档URL')
    return
  }

  // 打开新标签页预览文档
  window.open(url, '_blank')
}

// 漫游式引导
const tourOpen = ref(false)
const logo = ref(
  'https://aiswei.oss-cn-hangzhou.aliyuncs.com/dev/imageFile/7620271722931911450.png?Expires=2038464711&OSSAccessKeyId=LTAI5t8LAfU5VdgxF6NnVu2w&Signature=LJxTp4797ObJeA0hzPtwCHCIBuE%3D'
)
const inverterImg = ref(
  'https://aiswei.oss-cn-hangzhou.aliyuncs.com/uat/odm-custom/4588861725239465281.png?Expires=2040772265&OSSAccessKeyId=LTAI5t8LAfU5VdgxF6NnVu2w&Signature=S8kjqn6TYxkql%2BePrALZOsSwgBI%3D'
)

const openDemo = () => {
  tourOpen.value = true
}

const templatePathFun = async (item, item2) => {
  item.templateList.forEach((item3) => {
    if (item2.id === item3.id) {
      if (!item2.isSelected) {
        item3.isSelected = !item3.isSelected
      }
    } else {
      item3.isSelected = false // 取消选中其他元素
    }
  })
  console.log(item2.templateWebPath)
  // templateWebPath 预览的地址
  window.open(
    'https://view.officeapps.live.com/op/view.aspx?src=' + encodeURIComponent(item2.templateWebPath)
  ) //新建窗口打开链接预览
}

/** 获取word模板列表 */
const getList = async () => {
  loading.value = true

  try {
    const data = await OdmApi.getPageAll()
    templateListArr.value = data
    // 动态添加 pageHeader 和 pageFooter 属性
    templateListArr.value.forEach((item) => {
      item.templateList = item.templateList.map((template) => ({
        ...template,
        pageHeader: '',
        pageFooter: '',
        url: manualCover,
        subName: 'ASW6000-S/ASW8000-S/ASW10000-S',
        isSelected: false
      }))
      item.templateList[0].isSelected = true
    })

    console.log('templateListArr', templateListArr.value)
  } finally {
    loading.value = false
  }
}

const form = reactive({
  logo: 'https://aiswei.oss-cn-hangzhou.aliyuncs.com/dev/imageFile/7620271722931911450.png?Expires=2038464711&OSSAccessKeyId=LTAI5t8LAfU5VdgxF6NnVu2w&Signature=LJxTp4797ObJeA0hzPtwCHCIBuE%3D',
  templateCodeListArr: []
})

const nextPage = () => {
  isShowConfirm.value = true
  active.value = 3
  message.success('文档生成成功！')
  tourOpen.value = false
}

onMounted(async () => {
  await getList()

  if (odmStore.isOpenDemo) {
    openDemo()
  }
})
</script>

<style lang="scss" scoped>
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
  align-items: center;
  justify-content: center;
  flex-direction: column;
}
.template-select {
  min-width: 100px;
  min-height: 30px;
  background: #fff;
  border-radius: 5px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 20px;
  font-size: 14px;
  cursor: pointer;
  padding: 0 8px;
  border: 1px solid #dcdfdc;
}

.template-select.selected {
  border-color: #2788fe; /* 你可以选择任何颜色 */
  transition: border-color 0.3s ease;
}

.logo-box {
  width: 113px;
  height: 113px;
  background: #f5f6fa;
  border-radius: 11px 11px 11px 11px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.el-divider--vertical {
  height: 10em;
}
.book-thumbnail-two {
  border: 1px solid #98c3f7 !important;
}
.book-thumbnail {
  position: relative;
  width: 100px;
  height: 135.777px;
  border: 1px dashed #98c3f7;
  .logo-img {
    width: 13.333px;
    height: 13.333px;
    position: absolute;
    right: 11.666px;
    top: 11.666px;
  }
  .name {
    margin-top: 23.33px;
    margin-left: -1.3vw;
    font-size: 12px;
    line-height: 12px;
    font-weight: 540;
    color: #000;
    font-family: 'Inter', Arial, sans-serif;
    transform: scale(0.6);
    width: 10vw;
  }
  .sub-name {
    margin-top: 1px;
    margin-left: -7vw;
    font-size: 12px;
    line-height: 12px;
    transform: scale(0.3);
    width: 22vw;
  }
  .inverter {
    width: 100%;
    text-align: center;
    margin-top: 10px;
    .inverter-img {
      width: 70%;
    }
  }

  .book {
    width: 100px;
    transition: all 0.6s ease;
    border: 1px solid #98c3f7;
  }
  .book2 {
    margin-left: 20px;
  }
}
.book-thumbnail:hover {
  transform: translateY(-5px);
  box-shadow:
    2px 10px 15px -3px rgba(0, 0, 0, 0.2),
    4px 5px 6px -2px rgba(0, 0, 0, 0.1);
  transition: all 0.6s ease;
}
.book-wrap {
  position: relative;
  width: 300px;
  height: 407.33px;
  border: 1px solid #98c3f7;
  .logo-img {
    width: 40px;
    height: 40px;
    position: absolute;
    right: 35px;
    top: 35px;
  }
  .name {
    margin-top: 70px;
    margin-left: 30px;
    font-size: 16px;
    font-weight: 540;
    color: #000;
    font-family: 'Inter', Arial, sans-serif;
  }
  .sub-name {
    margin-top: 10px;
    margin-left: 30px;
    font-size: 8px;
  }
  .inverter {
    width: 100%;
    text-align: center;
    margin-top: 50px;
    .inverter-img {
      width: 70%;
    }
  }

  .book {
    width: 100px;
    transition: all 0.6s ease;
    border: 1px solid #98c3f7;
  }
  .book2 {
    margin-left: 20px;
  }
}
.book:hover {
  transform: translateY(-5px);
  box-shadow:
    2px 10px 15px -3px rgba(0, 0, 0, 0.2),
    4px 5px 6px -2px rgba(0, 0, 0, 0.1);
}
.book-container {
  width: 70%;
  display: flex;
  align-items: center;
  overflow-x: auto;
}
.book-box {
  display: flex;
  flex-direction: column;
  margin-right: 25px;
  .book {
    width: 100px;
    transition: all 0.6s ease;
    border: 1px solid #98c3f7;
  }
}
</style>
