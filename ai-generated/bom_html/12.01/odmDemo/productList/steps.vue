<template>
  <el-steps
    class="steps-container"
    style="max-width: 100%"
    :active="currentStep"
    align-center
    finish-status="success"
    process-status="finish"
  >
    <el-step
      v-for="(step, index) in steps"
      :key="index"
      :title="step.title"
      :description="step.description"
    />
  </el-steps>
</template>

<script lang="ts" setup>
import { ref } from 'vue'

// 定义步骤数组
const steps = [
  { title: '产品选择', description: '选择基础设备模板/型号/功率' },
  { title: '面板定制', description: '可定制化编辑设备面板' },
  { title: '文档生成', description: '最终完成包装，标签，文档' },
  { title: '设计确认', description: '后台审核3-5工作日' },
  { title: '下单量产', description: '设备量产' }
]

// 定义当前活动的步骤
const active = ref(0)

// 如果需要从父组件传递当前活动的步骤，可以通过 props 定义
const props = defineProps({
  currentStep: {
    type: Number,
    default: 0
  }
})
</script>

<style scoped lang="scss">
.steps-container {
  /* 如果需要自定义样式，可以在这里添加 */
  :deep(.el-step.is-center .el-step__description) {
    padding-left: 10%;
    padding-right: 10%;
  }
}
</style>
