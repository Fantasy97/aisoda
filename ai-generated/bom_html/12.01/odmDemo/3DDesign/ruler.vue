<template>
  <canvas ref="widthways" :style="getRuleStyle" style="flex: none"></canvas>
</template>

<script lang="ts" setup>
import { onMounted, ref, computed, watch } from 'vue'
import type { CSSProperties } from 'vue'

const widthways = ref<HTMLCanvasElement>()

const props = defineProps<{
  options: {
    offsetX: number
    offsetY: number
    dragOffsetX: number
    dragOffsetY: number
    scale: number
  }
  mode: 'horizontal' | 'vertical'
  drawPositionX: number
  drawPositionY: number
  blockWidth: number
  blockHeight: number
}>()

const getRuleStyle = computed<CSSProperties>(() => {
  return {
    width: props.mode === 'horizontal' ? 'calc(100% - 340px)' : '20px',
    height: props.mode === 'horizontal' ? '20px' : '100%',
    backgroundColor: 'white',
    zIndex: 996,
    display: 'block',
    cursor: props.mode === 'horizontal' ? 'row-resize' : 'col-resize'
  }
})

function getFixed(sparsity: number) {
  const pointIdx = String(sparsity).indexOf('.')
  const len = String(sparsity).length
  return pointIdx < 0 ? 0 : len - pointIdx - 1
}

function isCloseToInteger(num: number) {
  return Math.abs(num - Math.round(num)) < 0.0000001
}

watch(
  () => [
    props.options,
    props.drawPositionX,
    props.drawPositionY,
    props.blockWidth,
    props.blockHeight
  ],
  () => {
    renderWidthWays()
  },
  { deep: true }
)

function renderWidthWays() {
  const canvas = widthways.value
  if (!canvas) {
    return
  }
  const { width, height } = canvas.getBoundingClientRect()
  const dpi = window.devicePixelRatio || 2
  canvas.width = width * dpi
  canvas.height = height * dpi
  canvas.style.width = width + 'px'
  canvas.style.height = height + 'px'
  let { width: w, height: h } = canvas
  w /= dpi
  h /= dpi
  const ctx = canvas.getContext('2d')!
  ctx.scale(dpi, dpi)
  ctx.clearRect(0, 0, w, h)
  ctx.save()
  ctx.lineWidth = 1
  ctx.strokeStyle = '#d9d9d9'
  ctx.fillStyle = '#232323'
  ctx.font = '12px serif'
  ctx.beginPath()

  const { offsetX, offsetY, scale } = props.options
  const offset = props.mode === 'horizontal' ? offsetX : offsetY

  // 绘制指定宽度的背景色块到指定位置
  const backgroundColor = '#5692EE' // 背景色
  const textColor = '#000000' // 数值颜色
  const drawPositionX = props.drawPositionX
  const drawPositionY = props.drawPositionY
  const blockWidth = props.blockWidth / dpi // 考虑 DPI 缩放
  const blockHeight = props.blockHeight / dpi // 考虑 DPI 缩放

  if (props.mode === 'horizontal') {
    ctx.fillStyle = backgroundColor
    // x: 矩形左上角的 x 坐标。
    // y: 矩形左上角的 y 坐标。
    // width: 矩形的宽度。
    // height: 矩形的高度。
    ctx.fillRect(drawPositionX, 0, blockWidth, h)
  } else {
    ctx.fillStyle = backgroundColor
    ctx.fillRect(0, drawPositionY, w, blockHeight)
  }

  // 间隔 例如 0 - 50
  const sparsity = 50
  // 间隔内有多少小格
  const part = 10
  const pixelPerUnit = scale * sparsity
  // 每小格多少像素
  const gap = pixelPerUnit / part
  // getFixed 函数的作用是计算一个数的小数部分有几位，即这个数的精度
  const fixed = getFixed(sparsity)
  let index = offset % gap > 0 ? gap - (offset % gap) : -offset % gap

  ctx.strokeStyle = '#d9d9d9' // 设置刻度线颜色
  ctx.fillStyle = textColor // 设置数值颜色

  if (props.mode === 'horizontal') {
    ctx.translate(props.options.dragOffsetX, 0)
    do {
      const num = ((offset + index) / pixelPerUnit) * sparsity
      if (isCloseToInteger(num / sparsity)) {
        ctx.moveTo(index, h * 0.5)
        ctx.lineTo(index, h)
        const text = num.toFixed(fixed)
        const textWidth = ctx.measureText(text).width
        ctx.fillText(text, index - textWidth / 2, 10)
      } else {
        ctx.moveTo(index, h * 0.7)
        ctx.lineTo(index, h)
      }
      index += gap
    } while (index < w)
  } else {
    ctx.translate(0, props.options.dragOffsetY)
    do {
      const num = ((offset + index) / pixelPerUnit) * sparsity
      if (isCloseToInteger(num / sparsity)) {
        ctx.moveTo(w * 0.5, index)
        ctx.lineTo(w, index)
        const text = num.toFixed(fixed)
        ctx.save()
        ctx.rotate((-90 * Math.PI) / 180)
        const textWidth = ctx.measureText(text).width
        ctx.fillText(text, -(index + textWidth / 2), 12)
        ctx.rotate((0 * Math.PI) / 180)
        ctx.restore()
      } else {
        ctx.moveTo(w * 0.7, index)
        ctx.lineTo(w, index)
      }
      index += gap
    } while (index < h)
  }
  ctx.closePath()
  ctx.stroke()
  ctx.restore()
}

onMounted(() => {
  renderWidthWays()
})
</script>
