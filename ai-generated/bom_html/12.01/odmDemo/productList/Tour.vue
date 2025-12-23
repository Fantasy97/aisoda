<template>
  <div>
    <el-tour
      :model-value="modelValue"
      :show-close="false"
      :scroll-into-view-options="true"
      @change="handleChange"
      @finish="handleFinish"
      @update:model-value="handleModelValueChange"
    >
      <el-tour-step
        v-for="(item, index) in props.data"
        :key="index"
        :target="item.target"
        :title="item.title ? item.title : `第${currentStep}步`"
        :description="item.description"
        :placement="item.placement"
      />
      <template #indicators> </template>
    </el-tour>
  </div>
</template>

<script lang="ts" setup>
import { ref, computed } from 'vue'

const props = defineProps({
  data: Array,
  // 接收父组件传来的 modelValue 参数
  modelValue: Boolean
})
const emits = defineEmits(['change', 'prev', 'next', 'skip', 'update:modelValue'])

// 当前步数，从0开始
const currentStep = ref(0)

// 动态修改下一步按钮名称
const nextBtnName = computed(() => {
  let name = ''
  if (!currentStep.value) {
    name = '下一步'
  } else if (currentStep.value === props.data.length - 1) {
    name = '完成'
  } else {
    name = '下一步'
  }
  return name
})

// 步数切换时触发
const handleChange = (step) => {
  console.log('handleChange', step)
  currentStep.value = step
  emits('change', step)
}

const handleFinish = () => {
  console.log('finish')
}

// 点击跳过按钮时触发
const handleSkip = () => {
  emits('skip')
}

// 点击上一步按钮时触发
const handlePrevClick = () => {
  emits('prev')
}

// 点击下一步按钮时触发
const handleNextClick = () => {
  currentStep.value++
  emits('next', currentStep.value)
}

// 当 modelValue 状态发生变化时触发
const handleModelValueChange = (newValue: boolean) => {
  emits('update:modelValue', newValue)
}
</script>
