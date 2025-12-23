<template>
  <div class="confirmation-page">
    <ContentWrap>
      <el-result
        icon="success"
        title="设计已经提交成功，请耐心等待审核完成。"
        sub-title="预计审核时间为3-5个工作日。"
      />
    </ContentWrap>

    <el-button plain round @click="plmCheck">模拟PLM审核</el-button>
  </div>
</template>
<script setup>
import { useRouter } from 'vue-router'
import { useOdmStoreWithOut } from '@/store/modules/odm'

const odmStore = useOdmStoreWithOut()

// 获取路由实例
const router = useRouter()

const plmCheck = () => {
  router.push({
    name: 'ProductListDemo'
  })
  odmStore.productStatus = '量产'
}
</script>
