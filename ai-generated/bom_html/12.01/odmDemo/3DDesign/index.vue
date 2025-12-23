<template>
  <ContentWrap class="mb-5px!">
    <Steps :currentStep="active" />
  </ContentWrap>
  <div class="outer-container" v-loading="loading" :element-loading-text="loadingText">
    <!-- 进度条 -->
    <div v-if="loadingProgress > 0 && loadingProgress != 100" class="progress">
      <el-progress :percentage="loadingProgress" :stroke-width="4" />
    </div>
    <!-- 标尺区 -->
    <ruler
      v-if="is2DDesign"
      :options="rulerOptions"
      mode="vertical"
      class="ruler-col"
      :drawPositionX="dragPositionX"
      :drawPositionY="dragPositionY"
      :blockWidth="dragRulerW"
      :blockHeight="dragRulerH"
    />
    <ruler
      v-if="is2DDesign"
      :options="rulerOptions"
      mode="horizontal"
      class="ruler-row"
      :drawPositionX="dragPositionX"
      :drawPositionY="dragPositionY"
      :blockWidth="dragRulerW"
      :blockHeight="dragRulerH"
    />
    <!-- 网格区 -->
    <div
      :class="{ wg: is2DDesign }"
      :style="{ width: windowWidth + 'px', height: windowHeight + 'px' }"
    ></div>
    <div class="top-btn" id="top-btn">
      <el-button type="primary" plain @click="d2Design">2D设计</el-button>
      <el-button type="primary" plain @click="d3Preview">3D预览</el-button>
    </div>
    <!-- 底部按钮区 -->
    <div class="bottom-btn">
      <div>
        <el-button type="primary" round @click="nextPage" id="target-five">下一步</el-button>
        <el-button type="success" plain @click="downloadModelAsImage" id="target-four"
          >下载模型为图片</el-button
        >
      </div>
      <div v-if="!is2DDesign" class="color-tips"
        >提示：3D模型应用不同的光照，材质等与2D设计颜色可能会有略微偏差</div
      >
      <div v-if="!is2DDesign" class="tips"
        >Ctrl+<img
          src="@/assets/svgs/odm/mouseLeft.svg"
          alt="MouseLeft"
          class="mouse-left"
        />移动模型</div
      >
    </div>
    <!-- 3D 预览区 -->
    <div
      v-show="!is2DDesign"
      ref="canvasContainer"
      class="canvas-container"
      id="canvas-container"
      :style="{ width: windowWidth + 'px', height: windowHeight + 'px' }"
    >
    </div>
    <!-- 2D 设计区 -->
    <div
      v-show="is2DDesign"
      ref="d2-container"
      class="d2-container"
      :style="{ width: windowWidth + 'px', height: windowHeight + 'px' }"
    >
      <div
        class="svg-container"
        ref="svgContainer"
        :style="{ width: modelWidth + 'px', height: modelHeight + 'px' }"
      >
        <vue-drag-resize-rotate
          :grid="[5, 5]"
          :x="0"
          :y="0"
          :min-width="dragMinW"
          :min-height="dragMinH"
          :w="dragW"
          :h="dragH"
          :rotatable="false"
          :resizable="true"
          :parent="true"
          :lock-aspect-ratio="true"
          :handles="['tl', 'tr', 'bl', 'br']"
          :scaleRatio="scaleRatio"
          @dragstop="onDragStop"
          @resizestop="onResizeStop"
          @dragging="onDrag"
          @deactivated="onDeactivated"
          @activated="onActivated"
        >
          <img
            id="myImg"
            ref="myImg"
            style="width: 100%"
            :src="logo"
            alt="myImg"
            data-html2canvas-ignore
          />
        </vue-drag-resize-rotate>
        <svg v-if="!isBox" ref="svgRef" :width="modelWidth + 'px'" :height="modelHeight + 'px'">
          <g>
            <rect
              :width="modelWidth + 'px'"
              :height="modelHeight + 'px'"
              :style="{ fill: colorSvgBackground }"
            />
          </g>
        </svg>
        <!-- svgContent开始 -->
        <div v-if="isBox && svgContent" ref="svgContentRef" v-html="svgContent"></div>
        <!-- svgContent结束 -->
      </div>
    </div>
    <!-- 右侧操作区 -->
    <div class="oper-wrap">
      <div>
        <div class="logo-label">logo：</div>
        <div class="logo-box">
          <el-image class="logo-img" :src="logo" />
        </div>
      </div>
      <div>
        <div class="mt-20px">选择模块名字：</div>
        <el-select
          class="mt-10px !w-240px"
          v-model="childName"
          placeholder="请选择或搜索要设计模块的名字"
          clearable
          filterable
          allow-create
          default-first-option
          @change="handleChange"
        >
          <el-option
            v-for="item in childNameOptions"
            :key="item.value"
            :label="item.label"
            :value="item.value"
          />
        </el-select>
      </div>
      <div>
        <div class="color-label2">选择背景色：</div>
        <!-- <div class="color-box">
          <div
            v-for="(item, index) in items"
            :key="index"
            class="color-text"
            :class="{ 'color-active': item.isActive }"
            @click="toggleActive(index)"
          >
            {{ item.text }}
          </div>
        </div> -->
        <div class="color-reco" id="target-two" ref="colorRef" @click="handleClickOutside">
          <div class="flex" style="align-items: center">
            <div class="color-label color-label3">推荐：</div>
            <div class="color-grid">
              <div
                v-for="(color, index) in colors"
                :key="index"
                class="color-block"
                :class="{ selected: color === colorsBlockSelected }"
                :style="{ backgroundColor: color }"
                @click="colorsFun(color)"
              >
                <img
                  v-if="color == colors[0]"
                  src="@/assets/imgs/odm/transparent.jpg"
                  alt="transparant"
                  style="width: 28px; height: 28px"
                />
              </div>
            </div>
          </div>
          <div class="flex" style="align-items: center">
            <div class="color-label color-label3">默认：</div>
            <div class="color-grid">
              <div
                v-for="(color, index) in colorsBasic"
                :key="index"
                class="color-block"
                :class="{ selected: color === colorsBlockSelected }"
                :style="{ backgroundColor: color }"
                @click="colorsFun(color)"
              ></div>
            </div>
          </div>
        </div>
      </div>
      <div class="advanced" id="target-three">
        <span>高级设置：</span>
        <colorPicker class="mt-15px" @change-color="changeColor" @clear-color="clearColor" />
      </div>
      <div class="upload-model">
        <div>
          <el-button type="primary" plain @click="openForm('3D')">
            <Icon icon="ep:plus" class="mr-5px" />
            上传模型
          </el-button>
          <el-button v-if="isBox" type="primary" plain @click="openForm('svg')">
            <Icon icon="ep:plus" class="mr-5px" />
            上传svg
          </el-button>
        </div>
        <div class="mt-10px">
          <el-button v-if="isBox" type="primary" plain @click="downloadEps">
            导出eps文件
          </el-button>
          <el-switch
            class="ml-12px"
            v-model="isBox"
            inline-prompt
            style="--el-switch-on-color: #13ce66; --el-switch-off-color: #409eff"
            active-text="2D包装设计"
            inactive-text="3D模型设计"
            @change="switchChange"
          />
        </div>
      </div>
    </div>
  </div>
  <!-- 引导提示组件 -->
  <Tour v-model="tourOpen" :data="design" />
  <UploadForm ref="formRef" @success="uploadSuccess" />
</template>

<script lang="ts" setup>
import { onMounted, ref, reactive, computed } from 'vue'
import * as THREE from 'three'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js'
import { GridHelper } from 'three/src/helpers/GridHelper.js'
import { PlaneHelper } from 'three/src/helpers/PlaneHelper.js'
import { useRouter } from 'vue-router'
import * as FileApi from '@/api/aiManage/file'
import { useOdmStoreWithOut } from '@/store/modules/odm'
import Steps from '@/views/odmDemo/productList/steps.vue'
import TWEEN from '@tweenjs/tween.js'
import ruler from './ruler.vue'
import colorPicker from './colorPicker/index.vue'
import Tour from '@/views/odmDemo/productList/Tour.vue'
import { design } from '@/views/odmDemo/productList/tour.json'
import BigNumber from 'bignumber.js'
import UploadForm from './UploadForm.vue'
import Panzoom from 'panzoom'
import * as OdmApi from '@/api/odm'

const odmStore = useOdmStoreWithOut()
const message = useMessage() // 消息弹窗

defineOptions({ name: '3DDesignDemo' })

const router = useRouter()
const canvasContainer = ref<HTMLDivElement | null>(null)
const modelLoaded = ref(false)
const loadingProgress = ref(0)
const loading = ref(false)
const loadingText = ref('由于文件较大，加载可能需要一些时间，请耐心等待。')
let scene: THREE.Scene | null = null
let camera: THREE.PerspectiveCamera | null = null
let renderer: THREE.WebGLRenderer | null = null
let model: THREE.Object3D<THREE.Event> | null = null
let controls: OrbitControls | null = null
let GridHelper: GridHelper | null = null
let PlaneHelper: PlaneHelper | null = null
let texturePlane: THREE.Mesh | null = null
const isFirstTime = ref(true)
const initPlaneX = ref(0) // 世界单位
const initPlaneY = ref(0)
const planePositionX = ref(0)
const planePositionY = ref(0)
const planePositionZ = ref(0)
const planeRotationX = ref(0) // 一个PI弧度是180度  -Math.PI / 2
const planeRotationY = ref(0)
const planeRotationZ = ref(0)
const planeScaleX = ref(1) // logo 缩放比
const active = ref(1)
const svgContainer = ref()
const myImg = ref()
const modelWidth = ref(668.0324966953864) // 单位 px
const modelHeight = ref(437.1433088269757) // 单位 px
const dragMinW = ref(10) // 单位 px
const dragMinH = ref(10) // 单位 px
const dragW = ref(50) // 单位 px  2D 设计上的logo 只在初始化设置 之后改动会跳动
const dragH = ref(50) // 单位 px  2D 设计上的logo
const dragSyncW = ref(50) // 同步拖拽和缩放方法中的宽高
const dragSyncH = ref(50)
const dragRulerW = ref(0) // 同步拖拽和缩放方法中的宽高
const dragRulerH = ref(0)
const dragPositionX = ref(0)
const dragPositionY = ref(0)
let d2PlaneW = ref(1) //    世界单位 3D 模型上的logo
let d2PlaneH = ref(1) //    世界单位 3D 模型上的logo
const modelScaleRatio = ref(1) // 模型缩放比例
const d2PlaneWRatio = ref(0)
const d2PlaneHRatio = ref(0)
const pxToMWRatio = ref(100) // px与世界单位转换因子 100
const pxToMHRatio = ref(100) // px与世界单位转换因子 100
const worldWidthPlane = ref(0)
const worldHeightPlane = ref(0)
const d2PlaneWAfter = ref(0)
const d2PlaneHAfter = ref(0)
const childNameOptions = ref([])
const childName = ref('000-320kw-665mm0001_4') // 4.glb  isCoordinateY=true  // 要渲染模型的哪个面的名字
// const childName = ref('500-002453-00') // 2.glb isCoordinateY=false
const isCoordinateY = ref(true) // 是否为Y坐标方向，坐标轴的方向判断
const glbUrl = ref(
  'https://aiswei.oss-cn-hangzhou.aliyuncs.com/dev/odm-custom/8602561728458622606.glb?Expires=2043991430&OSSAccessKeyId=LTAI5t8LAfU5VdgxF6NnVu2w&Signature=h6h%2FRQirUSoYuwAtrfzj%2BwDWFjU%3D'
) // 4.glb模型文件地址
// const glbUrl = ref('https://aiswei.oss-cn-hangzhou.aliyuncs.com/dev/odm-custom/7815151728458745097.glb?Expires=2043991557&OSSAccessKeyId=LTAI5t8LAfU5VdgxF6NnVu2w&Signature=d%2BderKsAUpx93l02aERIQxg01LM%3D') // 2.glb模型文件地址
// const glbUrl = ref('/models/4.glb') // 模型文件地址
const isAdjustToCenter = ref(false) // 是否将坐标原点调整到中心点
let panzoomSvg = ref()
let scaleRatio = ref(1)
let logoActive = ref(false)
let svgDoc = ref()
let isBox = ref(false) // 是否是2D包装盒设计
// 定义响应式变量
const indentValue = ref(580)
const windowWidth = ref(window.innerWidth - indentValue.value)
const windowHeight = ref(window.innerHeight)

const rulerOptions = reactive({
  offsetX: 0,
  offsetY: 0,
  dragOffsetX: 20, // 画布偏移量和尺子偏移量
  dragOffsetY: 20,
  scale: 1
})

const logo = ref(
  'https://aiswei.oss-cn-hangzhou.aliyuncs.com/dev/imageFile/7620271722931911450.png?Expires=2038464711&OSSAccessKeyId=LTAI5t8LAfU5VdgxF6NnVu2w&Signature=LJxTp4797ObJeA0hzPtwCHCIBuE%3D'
)

// 漫游式引导
const tourOpen = ref(false)
const openDemo = () => {
  tourOpen.value = true
}

// 定义颜色数组
const colors = ref([
  'transparent',
  'rgb(231, 36, 37)',
  'rgb(80, 176, 255)',
  'rgb(159, 225, 112)',
  'rgb(242, 135, 2)'
])
const colorsBasic = ref([
  '#000000',
  'rgb(54, 216, 183)',
  'rgb(253, 115, 188)',
  'rgb(193, 152, 103)',
  'rgb(188, 204, 221)'
])

const svgContent = ref('')
const svgContentRef = ref()
const svgUrl = ref(
  'https://aiswei.oss-cn-hangzhou.aliyuncs.com/dev/odm-custom/5001851728724481285.svg?Expires=2044257281&OSSAccessKeyId=LTAI5t8LAfU5VdgxF6NnVu2w&Signature=aoLzMmxp%2BjAwaiJnjvjmFoA8g84%3D'
)

// 递归遍历 DOM 并修改属性
const traverseAndModify = (node) => {
  if (node.nodeType === Node.ELEMENT_NODE) {
    // 修改当前节点的 width 和 height 属性
    if (node.hasAttribute('width')) {
      node.setAttribute('width', `${modelWidth.value}`)
    }
    if (node.hasAttribute('height')) {
      node.setAttribute('height', `${modelHeight.value}`)
    }

    // 递归遍历子节点
    node.childNodes.forEach((childNode) => {
      traverseAndModify(childNode)
    })
  }
}
// 获取远程 svg 并 更改宽高
const fetchRemoteSVG = async () => {
  try {
    const response = await fetch(svgUrl.value)
    const svgContentRes = await response.text()

    // 使用 DOMParser 解析 SVG 内容
    const parser = new DOMParser()
    svgDoc.value = parser.parseFromString(svgContentRes, 'image/svg+xml')

    // 2. 遍历 SVG 元素
    traverseAndModify(svgDoc.value.documentElement)

    // 4. 修改 SVG 元素的 `viewBox` 和 `preserveAspectRatio`
    const svgElement = svgDoc.value.documentElement
    const viewBox = svgElement.getAttribute('viewBox')
    if (viewBox) {
      const [x, y] = viewBox.split(/\s+/).map(Number)
      svgElement.setAttribute('viewBox', `${x} ${y} ${modelWidth.value} ${modelHeight.value}`)
    }

    // 更新 SVG 内容
    svgContent.value = svgElement.outerHTML
  } catch (error) {
    console.error('Failed to load SVG:', error)
  }
}

// 修改2d 包装盒设计的填充色
const modifySvgFill = async (color) => {
  try {
    if (!svgDoc.value) {
      message.warning('请先上传svg')
      return
    }
    if (color == 'transparent') {
      fetchRemoteSVG() // 重新获取恢复初始颜色
      return
    }
    const svgElements = svgDoc.value.querySelectorAll('*')
    svgElements.forEach((element) => {
      if (element.hasAttribute('fill')) {
        element.setAttribute('fill', color)
      }
    })

    // 获取 <style> 标签
    const styleElement = document.querySelector('svg defs style')
    // 获取样式内容
    let cssText = styleElement.textContent
    // 替换样式内容
    cssText = cssText.replace(
      /fill:\s*(#[\da-fA-F]{6}|rgb\(\d{1,3},\s*\d{1,3},\s*\d{1,3}\));/gi,
      `fill: ${color};`
    )

    // 更新样式内容
    styleElement.textContent = cssText

    svgContent.value = svgDoc.value.documentElement.outerHTML
  } catch (error) {
    console.error('Failed to load and modify SVG:', error)
  }
}
// 将 svg 和 jpg 合并成  svg
const createCompositeSVG = async () => {
  try {
    // 加载 JPG 图像并转换为 Base64 编码
    const jpgResponse = await fetch(logo.value)
    const jpgBlob = await jpgResponse.blob()
    const jpgBase64 = await new Promise((resolve, reject) => {
      const reader = new FileReader()
      reader.onloadend = () => resolve(reader.result)
      reader.onerror = reject
      reader.readAsDataURL(jpgBlob)
    })

    if (!svgDoc.value) {
      message.warning('请先上传svg')
      return
    }
    const svgElement = svgDoc.value.documentElement
    // 检查 SVG 中是否已有 <image> 元素
    let imageElement = svgElement.querySelector('image')
    if (imageElement) {
      // 如果存在 <image> 元素，则修改其属性
      imageElement.setAttribute('x', `${dragPositionX.value - rulerOptions.dragOffsetX}`)
      imageElement.setAttribute('y', `${dragPositionY.value - rulerOptions.dragOffsetY}`)
      imageElement.setAttribute('width', `${dragSyncW.value}`)
      imageElement.setAttribute('height', `${dragSyncH.value}`)
      imageElement.setAttributeNS('http://www.w3.org/1999/xlink', 'xlink:href', jpgBase64)
    } else {
      // 如果不存在 <image> 元素，则创建并添加
      imageElement = svgElement.ownerDocument.createElementNS('http://www.w3.org/2000/svg', 'image')
      imageElement.setAttribute('x', `${dragPositionX.value - rulerOptions.dragOffsetX}`)
      imageElement.setAttribute('y', `${dragPositionY.value - rulerOptions.dragOffsetY}`)
      imageElement.setAttribute('width', `${dragSyncW.value}`)
      imageElement.setAttribute('height', `${dragSyncH.value}`)
      imageElement.setAttributeNS('http://www.w3.org/1999/xlink', 'xlink:href', jpgBase64)
      svgElement.appendChild(imageElement)
    }
    // 序列化 SVG 文件
    const serializer = new XMLSerializer()
    const modifiedSvgContent = serializer.serializeToString(svgElement)
    return modifiedSvgContent
  } catch (error) {
    console.error('Failed to create composite SVG:', error)
  }
}

const updateTexturePlanePosition = () => {
  if (texturePlane) {
    texturePlane.position.set(planePositionX.value, planePositionY.value, planePositionZ.value)
  }
}
const updateTexturePlaneRotation = () => {
  if (texturePlane) {
    texturePlane.rotation.set(planeRotationX.value, planeRotationY.value, planeRotationZ.value)
  }
}
const updateTexturePlaneScale = () => {
  if (texturePlane) {
    texturePlane.scale.set(planeScaleX.value, planeScaleX.value, planeScaleX.value)
  }
}

// 定义数据
const items = reactive([
  { text: '颜色', isActive: true }
  // { text: '纹理', isActive: false }
])

// 切换激活状态的方法
const toggleActive = (index) => {
  items.forEach((item, i) => {
    item.isActive = i === index
  })
}
// 高级设置
const changeColor = (color) => {
  console.log('color', color)
  if (!isBox.value) {
    colorChanged(color)
    return
  }
  modifySvgFill(color)
}

const switchChange = () => {
  getMaterialColors(model)
}

const clearColor = () => {
  if (!isBox.value) {
    colorChanged()
    return
  }
  modifySvgFill('transparent')
}

// 上传成功
const uploadSuccess = (url, type) => {
  if (type === '3D') {
    glbUrl.value = url
    removeFun() // 移除旧模型
    initScene() // 初始化场景
  } else {
    svgUrl.value = url
    // 动态加载远程 SVG 文件
    if (isBox.value) {
      fetchRemoteSVG()
    }
  }
}

// 打开上传
const formRef = ref()
const openForm = (type) => {
  formRef.value.open(type)
}

// 导出 eps 文件
const downloadEps = async () => {
  const mergeAfter = await createCompositeSVG()
  console.log(111111, mergeAfter)
  if (!mergeAfter) {
    return
  }
  // 创建 Blob 对象
  const svgBlob = new Blob([mergeAfter], { type: 'image/svg+xml' })
  // // 创建 File 对象
  const file = new File([svgBlob], 'example.svg', { type: 'image/svg+xml' })
  console.log('file', file)

  const formDataObj = new FormData()
  // 添加表单字段
  formDataObj.append('file', file)

  try {
    // 发送请求并等待响应
    OdmApi.odmSvgToEps(formDataObj).then((blob) => {
      console.log('Blob数据：', blob)
      const url = window.URL.createObjectURL(blob)
      let downloadLink = document.createElement('a')
      downloadLink.href = url
      downloadLink.download = 'downloaded-file.eps' // 设置下载时的文件名
      downloadLink.style.display = 'none'
      downloadLink.click()
      window.URL.revokeObjectURL(url) // 清理创建的对象URL
    })
  } catch (error) {
    console.error('Error:', error)
  }
}

const onDragResizeFun = (x, y, w, h) => {
  if (w && h) {
    d2PlaneWAfter.value = w / pxToMWRatio.value // 拖后宽度 / px与世界单位转换因子 100
    d2PlaneHAfter.value = h / pxToMHRatio.value // 拖后宽度 / px与世界单位转换因子 100
    // 缩放比 = 拖拽后宽度 / 拖拽前宽度(1) 世界单位
    planeScaleX.value = d2PlaneWAfter.value / d2PlaneW.value

    const initPlaneNumX = new BigNumber(initPlaneX.value).toNumber()
    const initPlaneNumY = new BigNumber(initPlaneY.value).toNumber()
    const planeX = initPlaneNumX + x / pxToMWRatio.value
    const planeY = initPlaneNumY - y / pxToMHRatio.value
    const planeZ = initPlaneNumY + y / pxToMHRatio.value
    if (isCoordinateY.value) {
      planePositionX.value = planeX + (d2PlaneWAfter.value - d2PlaneW.value) / 2
      planePositionY.value = planeY - (d2PlaneHAfter.value - d2PlaneH.value) / 2
    } else {
      planePositionX.value = planeX + (d2PlaneWAfter.value - d2PlaneW.value) / 2
      planePositionZ.value = planeZ + (d2PlaneHAfter.value - d2PlaneH.value) / 2
    }
  } else {
    const initPlaneNumX = new BigNumber(initPlaneX.value).toNumber()
    const initPlaneNumY = new BigNumber(initPlaneY.value).toNumber()
    const planeX = initPlaneNumX + x / pxToMWRatio.value
    const planeY = initPlaneNumY - y / pxToMHRatio.value
    const planeZ = initPlaneNumY + y / pxToMHRatio.value
    if (isCoordinateY.value) {
      planePositionX.value = planeX
      planePositionY.value = planeY
    } else {
      planePositionX.value = planeX
      planePositionZ.value = planeZ
    }
  }

  updateTexturePlanePosition()
  updateTexturePlaneRotation()
  updateTexturePlaneScale()
}

// 2D 拖拽改变 3D 位置
const onDragStop = (x, y) => {
  console.log('onDragStop', x, y)
  // let transformObj = panzoomSvg.value.getTransform()
  // scaleRatio.value = transformObj.scale
  dragPositionX.value = rulerOptions.dragOffsetX + x
  dragPositionY.value = rulerOptions.dragOffsetY + y
  dragRulerW.value = dragSyncW.value * window.devicePixelRatio * scaleRatio.value
  dragRulerH.value = dragSyncH.value * window.devicePixelRatio * scaleRatio.value
  onDragResizeFun(x, y, dragSyncW.value, dragSyncH.value)
}

const onDrag = (x, y) => {
  console.log('onDrag', x, y)
  // let transformObj = panzoomSvg.value.getTransform()
  // scaleRatio.value = transformObj.scale
  dragPositionX.value = rulerOptions.dragOffsetX + x
  dragPositionY.value = rulerOptions.dragOffsetY + y
  dragRulerW.value = dragSyncW.value * window.devicePixelRatio * scaleRatio.value
  dragRulerH.value = dragSyncH.value * window.devicePixelRatio * scaleRatio.value
}

const onDeactivated = () => {
  logoActive.value = false
  dragRulerW.value = 0
  dragRulerH.value = 0
}

const onActivated = () => {
  logoActive.value = true
}

const onResizeStop = (x, y, w, h) => {
  console.log('onResizeStop', x, y, w, h)
  // 加 20 为 空出标尺左上角的距离
  dragSyncW.value = w
  dragSyncH.value = h
  dragPositionX.value = rulerOptions.dragOffsetX + x
  dragPositionY.value = rulerOptions.dragOffsetY + y
  dragRulerW.value = w * window.devicePixelRatio * scaleRatio.value
  dragRulerH.value = h * window.devicePixelRatio * scaleRatio.value
  onDragResizeFun(x, y, dragSyncW.value, dragSyncH.value)
}

const colorRef = ref(null)
// 当点击页面其他地方时取消选中状态
const handleClickOutside = (event) => {
  if (!colorRef.value?.contains(event.target)) {
    colorsBlockSelected.value = null
    document.removeEventListener('click', handleClickOutside)
  }
}

// 初始化场景
const initScene = async () => {
  loading.value = true
  createCamera()
  createRenderer()
  createLight()
  createControls(camera)
  // 加载模型 顺序不能乱
  await loadModel()
  create2DPlane() // 创建2D平面
  pxToWorldRatioFun() // 计算世界坐标和像素坐标的转换比例
  initLogoPosition() // 初始化logo位置
  getMeshNames(model) // 获取模型内部网格的名字
  getMaterialColors(model) // 获取模型内部网格的颜色
  // box3HelperFun() // 创建辅助函数
}

const getMeshNames = (node) => {
  if (node instanceof THREE.Mesh) {
    if (node.name) {
      childNameOptions.value.push({ label: node.name, value: node.name })
    }
  }

  for (let child of node.children) {
    getMeshNames(child)
  }
}

const getMaterialColors = (node) => {
  if (node instanceof THREE.Mesh && node.name === childName.value) {
    // 获取网格的材质
    const material = node.material
    if (Array.isArray(material)) {
      material.forEach((mat) => {
        console.log('Material Color1:', mat.color)
        const hexColor = mat.color.getHexString()
        console.log('Hex Color1:', `#${hexColor}`)
        if (!isBox.value) {
          colors.value[0] = `#${hexColor}`
        } else {
          colors.value[0] = `transparent`
        }
      })
    } else {
      console.log('Material Color2:', material.color)
      const hexColor = material.color.getHexString()
      console.log('Hex Color2:', `#${hexColor}`)
      if (!isBox.value) {
        colors.value[0] = `#${hexColor}`
      } else {
        colors.value[0] = `transparent`
      }
    }
  }

  for (let child of node.children) {
    getMaterialColors(child)
  }
}

const handleChange = () => {
  getMaterialColors(model)
}

// 创建摄像机
const createCamera = () => {
  // 摄像机的宽高比应该与渲染器的宽高比一致
  camera = new THREE.PerspectiveCamera(
    30,
    (window.innerWidth - indentValue.value) / window.innerHeight,
    0.1,
    1000
  )
  camera.position.set(-7, 0, 15)
}
// 创建渲染器
const createRenderer = () => {
  renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, preserveDrawingBuffer: true })
  // 计算渲染器的宽度和高度，减去左边和右侧控制面板的宽度
  const rendererWidth = window.innerWidth - indentValue.value
  const rendererHeight = window.innerHeight
  renderer.setSize(rendererWidth, rendererHeight)
  renderer.setPixelRatio(window.devicePixelRatio)
  // 设置场景的清除颜色为透明（可选）
  renderer.setClearColor(0xffffff, 0) // 第二个参数是 alpha 值，0 表示完全透明
  if (canvasContainer.value) {
    canvasContainer.value.appendChild(renderer.domElement)
  }
  renderer.domElement.style.cursor = 'pointer'
  renderer.outputEncoding = THREE.sRGBEncoding // 设置渲染器输出编码
  renderer.physicallyCorrectLights = true // 启用物理上准确的光照模型
}
// 创建光照
const createLight = () => {
  scene = new THREE.Scene()
  // 创建环境光的一种方法
  const ambientLight = new THREE.AmbientLight(0xffffff, 2)
  scene.add(ambientLight)
  // 创建方向光的一种方法
  const directionalLight = new THREE.DirectionalLight(0xffffff, 2)
  directionalLight.position.set(1, 1, 1).normalize()
  scene.add(directionalLight)
}

// 创建控制器
const createControls = (camera) => {
  // 允许用户通过鼠标和键盘操作来旋转、平移和缩放摄像机
  controls = new OrbitControls(camera, renderer.domElement)
  controls.enablePan = true // 是否允许平移
  controls.enableZoom = true // 是否允许缩放
  controls.enableRotate = true // 是否允许旋转
  controls.autoRotate = false // 是否启用自动旋转
  controls.enableDamping = true // 启用阻尼
  controls.target = new THREE.Vector3(0, 0, 0) // 目标点
  controls.update() // 更新控制器
}

const colorsBlockSelected = ref(null) // 初始时没有选中的颜色
const colorSvgBackground = ref('transparent') // svg 背景色
const colorsFun = (color) => {
  document.addEventListener('click', handleClickOutside) // 点击颜色块外部的时候取消选中
  if (!isBox.value) {
    colorChanged(color)
    colorsBlockSelected.value = color
    colorSvgBackground.value = color
    return
  }

  if (isBox.value) {
    modifySvgFill(color)
  }
}

let is2DDesign = ref(false)
// 2D设计
function d2Design() {
  is2DDesign.value = true
}
// 3D预览
function d3Preview() {
  is2DDesign.value = false
  animateCamera()
  animate()
}

let isDownload = ref(false)
function downloadControls() {
  controls.enabled = true // 启用控制器
  is2DDesign.value = false
  isDownload.value = true
  animateCamera()
}

// 定义初始和目标位置
const initialPosition = { x: -7, y: 0, z: 15 }
const targetPosition = { x: 0, y: 0, z: 15 }
const downloadPosition = { x: -6, y: 0, z: 12 }

let tween
function animateCamera() {
  if (tween) {
    tween.stop()
  }
  if (isDownload.value) {
    tween = new TWEEN.Tween(camera.position)
      .to(downloadPosition, 1000) // 1 秒内完成动画
      .easing(TWEEN.Easing.Quadratic.Out) // 使用二次方缓动
      .onUpdate(() => {
        camera.lookAt(0, 0, 0) // 确保相机朝向场景中心
      })
      .start() // 开始动画
    isDownload.value = false
    controls.reset() // 重置控制器状态
    return
  }
  if (is2DDesign.value) {
    camera.position.set(-7, 0, 15)
    tween = new TWEEN.Tween(camera.position)
      .to(targetPosition, 1000) // 1 秒内完成动画
      .easing(TWEEN.Easing.Quadratic.Out) // 使用二次方缓动
      .onUpdate(() => {
        camera.lookAt(0, 0, 0) // 确保相机朝向场景中心
      })
      .start() // 开始动画
  } else {
    camera.position.set(0, 0, 15)
    tween = new TWEEN.Tween(camera.position)
      .to(initialPosition, 1000) // 1 秒内完成动画
      .easing(TWEEN.Easing.Quadratic.Out) // 使用二次方缓动
      .onUpdate(() => {
        camera.lookAt(0, 0, 0) // 确保相机朝向场景中心
      })
      .start() // 开始动画
  }
  controls.reset() // 重置控制器状态
}

// 加载模型
const loadModel = async () => {
  return new Promise((resolve) => {
    const loader = new GLTFLoader()
    loader.load(
      glbUrl.value,
      (gltf) => {
        resolve(gltf.scene)
        model = gltf.scene
        scene.add(model)
        modelLoaded.value = true
        camera.lookAt(model.position)
        animate()
      },
      (xhr) => {
        loadingProgress.value = (xhr.loaded / xhr.total) * 100
        loadingProgress.value = Math.floor(loadingProgress.value)
        if (loadingProgress.value == 100) {
          loading.value = false
        }
      },
      (error) => console.error(error)
    )
  })
}

// 查找要更改颜色的网格名字
function findMeshByName(model, name) {
  // console.log('model', model.name, name)
  if (model instanceof THREE.Mesh && model.name === name) return model
  for (let i = 0; i < model.children.length; i++) {
    const child = findMeshByName(model.children[i], name)
    if (child) return child
  }
  return null
}
// 像素转换世界单位
const pxToWorldRatioFun = async () => {
  await modelScale()
  const targetMesh = findMeshByName(model, childName.value)
  // 获取模型的边界框
  const boundingBox = new THREE.Box3().setFromObject(targetMesh)
  const boundingBoxPlane = new THREE.Box3().setFromObject(texturePlane)
  // 获取包围盒在世界坐标系中的最小和最大点
  const min = boundingBox.min
  const max = boundingBox.max
  const minPlane = boundingBoxPlane.min
  const maxPlane = boundingBoxPlane.max

  // 计算世界空间中的宽度和高度
  const worldWidth = Math.abs(max.x - min.x)
  const worldHeight = Math.abs(max.y - min.y)
  const worldHeightZ = Math.abs(max.z - min.z)

  if (isCoordinateY.value) {
    worldWidthPlane.value = Math.abs(maxPlane.x - minPlane.x)
    worldHeightPlane.value = Math.abs(maxPlane.y - minPlane.y)
  } else {
    worldWidthPlane.value = Math.abs(maxPlane.x - minPlane.x)
    worldHeightPlane.value = Math.abs(maxPlane.z - minPlane.z)
  }

  // 计算模型左侧位置到世界原点的距离  x 轴中心点在面的中心这里可以计算去掉右边多余部分
  const distanceToLeft = Math.abs(min.x)

  console.log('模型左边到世界原点的距离:', distanceToLeft)

  modelWidth.value = distanceToLeft * 2 * pxToMWRatio.value
  modelHeight.value = isCoordinateY.value
    ? worldHeight * pxToMWRatio.value
    : worldHeightZ * pxToMWRatio.value

  d2PlaneWRatio.value = worldWidthPlane.value / (distanceToLeft * 2)
  d2PlaneHRatio.value = worldHeightPlane.value / (isCoordinateY.value ? worldHeight : worldHeightZ)
}

// 定义一个计算属性 d2PlaneW
d2PlaneW = computed(() => {
  return dragW.value / pxToMWRatio.value
})

// 定义计算属性 d2PlaneH
d2PlaneH = computed(() => {
  return dragH.value / pxToMHRatio.value
})

// 模型缩放
const modelScale = async () => {
  return new Promise((resolve) => {
    // 获取模型的边界框
    const boundingBox = new THREE.Box3().setFromObject(model)
    // 计算模型包围盒的尺寸
    const size = boundingBox.getSize(new THREE.Vector3()).length()
    // 计算缩放比例
    modelScaleRatio.value = Math.min(windowWidth.value, window.innerHeight) / size / 100

    model.scale.set(modelScaleRatio.value, modelScaleRatio.value, modelScaleRatio.value)
    texturePlane.scale.set(modelScaleRatio.value, modelScaleRatio.value, 1)

    resolve(model)
  })
}

// 初始化logo 在模型上的位置
const initLogoPosition = async () => {
  // 获取模型的边界框
  const boundingBox = new THREE.Box3().setFromObject(model)

  if (isAdjustToCenter.value) {
    // 计算模型的中心点
    const center = new THREE.Vector3()
    boundingBox.getCenter(center)
    // 计算模型中心点相对于世界坐标系的偏移量
    const offset = center.clone().negate()
    // 将模型的位置进行调整
    model.position.add(offset)
    console.log('调整后的模型位置:', model.position)
  } else {
    // 计算模型的中心点
    const center = new THREE.Vector3()
    boundingBox.getCenter(center)
    // 调整模型的位置
    model.position.set(0, -center.y, -center.z)
    console.log('调整后的模型位置:', model.position)
  }

  const boundingBoxNew = new THREE.Box3().setFromObject(model)

  // 计算模型包围盒的左上前方位置
  const boxMin = boundingBoxNew.min
  const boxMax = boundingBoxNew.max
  let topLeftFrontCorner = new THREE.Vector3()
  if (isCoordinateY.value) {
    topLeftFrontCorner = new THREE.Vector3(boxMin.x, boxMax.y, boxMax.z)
  } else {
    topLeftFrontCorner = new THREE.Vector3(boxMin.x, boxMax.y, boxMin.z)
  }

  // 将 `texturePlane` 移动到模型包围盒的左上前方位置
  texturePlane.position.copy(topLeftFrontCorner)

  // 仅在第一次调用时存储 `texturePlane.position.x` 主要用于把2D设计的(0, 0)点与3D模型的(0, 0, 0)同步
  console.log('texturePlane.position.x', texturePlane.position.x, texturePlane.position.z)
  if (isCoordinateY.value) {
    if (isFirstTime.value) {
      initPlaneX.value = texturePlane.position.x + d2PlaneW.value / 2 // 减去中心点到左上角的距离 (中心点如果在中心的话也就是一半)
      initPlaneY.value = texturePlane.position.y - d2PlaneH.value / 2
      isFirstTime.value = false
    }
    planePositionX.value = texturePlane.position.x + d2PlaneW.value / 2
    planePositionY.value = texturePlane.position.y - d2PlaneH.value / 2
    planePositionZ.value = texturePlane.position.z
  } else {
    if (isFirstTime.value) {
      initPlaneX.value = texturePlane.position.x + d2PlaneW.value / 2 // 减去中心点到左上角的距离 (中心点如果在中心的话也就是一半)
      initPlaneY.value = texturePlane.position.z + d2PlaneH.value / 2
      isFirstTime.value = false
    }
    planePositionX.value = texturePlane.position.x + d2PlaneW.value / 2
    planePositionY.value = texturePlane.position.y
    planePositionZ.value = texturePlane.position.z + d2PlaneH.value / 2
  }

  // 沿x轴旋转 90 度
  if (!isCoordinateY.value) {
    planeRotationX.value = -1.57
  }

  updateTexturePlanePosition()
  updateTexturePlaneRotation()
  updateTexturePlaneScale()
}

// 创建辅助对象
const box3HelperFun = () => {
  const targetMesh = findMeshByName(model, childName.value)
  // 创建一个包围盒辅助对象
  const box3Helper = new THREE.Box3Helper(new THREE.Box3().setFromObject(targetMesh), 0xff0000)
  scene.add(box3Helper)
  const box3Helper2 = new THREE.Box3Helper(new THREE.Box3().setFromObject(texturePlane), 0xff0000)
  scene.add(box3Helper2)
  // 创建一个网格辅助对象
  const gridHelper = new THREE.GridHelper(10, 10, 0x00ff00, 0x0000ff) // 大小为 10x10 单元格，每个单元格边长为 1，绿色线条，蓝色网格
  scene.add(gridHelper)
}

// 创建2D纹理平面
const create2DPlane = async () => {
  const textureLoader = new THREE.TextureLoader()
  const texture = textureLoader.load(logo.value)
  const planeGeometry = new THREE.PlaneGeometry(d2PlaneW.value, d2PlaneH.value)
  const planeMaterial = new THREE.MeshStandardMaterial({
    map: texture,
    side: THREE.DoubleSide,
    transparent: true,
    opacity: 1
  })
  planeMaterial.map.encoding = THREE.sRGBEncoding
  planeMaterial.map.colorSpace = THREE.SRGBColorSpace
  texturePlane = new THREE.Mesh(planeGeometry, planeMaterial)
  scene.add(texturePlane)
}

THREE.ColorManagement.enabled = true
const applyTexture = (material: THREE.Material, texture: THREE.Texture) => {
  if (material instanceof THREE.MeshStandardMaterial) {
    material.map = texture
    material.transparent = true
    material.alphaTest = 0.5 // 这个值可以根据遮罩纹理的具体情况调整
    // material.metalness = 0 // 金属度
    // material.roughness = 1 // 粗糙度
    material.map.encoding = THREE.sRGBEncoding
    material.map.colorSpace = THREE.SRGBColorSpace

    material.needsUpdate = true
  }
}

// 将颜色值 #a7baca 或 rgb(167,186,202) 转换为 0xA7BACA
const colorToHex = (color) => {
  // 去除颜色字符串的首尾空白
  color = color.trim()

  // 检查是否为 #RRGGBB 格式
  if (/^#[0-9A-Fa-f]{6}$/.test(color)) {
    // 直接返回去掉 '#' 的十六进制值，并加上 '0x' 前缀
    return '0x' + color.slice(1)
  }

  // 检查是否为 rgb(R, G, B) 格式
  const rgbMatch = color.match(/^rgb\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)$/)
  if (rgbMatch) {
    // 提取 R, G, B 值
    const r = parseInt(rgbMatch[1], 10)
    const g = parseInt(rgbMatch[2], 10)
    const b = parseInt(rgbMatch[3], 10)

    // 转换为十六进制字符串，并加上 '0x' 前缀
    const hex = ((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1).toUpperCase()
    return '0x' + hex
  }

  // 如果格式不匹配，返回 null 或抛出错误
  throw new Error('Invalid color format')
}

// 修改材质颜色
const changeColors = (newColor) => {
  const colorInt = colorToHex(newColor)
  const targetMesh = findMeshByName(model, childName.value)
  console.log('changeColors', colorInt)
  targetMesh.material.color.setHex(colorInt)
}

const colorChanged = (newColor?: string) => {
  if (!newColor) {
    newColor = colors.value[0]
  }
  colorSvgBackground.value = newColor
  changeColors(newColor)
}

const animate = () => {
  if (is2DDesign.value) return // 如果是2D设计暂停渲染优化性能
  TWEEN.update() //tween更新
  requestAnimationFrame(animate)
  if (modelLoaded.value && renderer && scene && camera) {
    renderer.render(scene, camera)
    controls?.update()
  }
}

// base64转file格式
const base64TOFile = (base64) => {
  let arr = base64.split(',')
  let mime = arr[0].match(/:(.*?);/)[1]
  let bstr = atob(arr[1])
  let n = bstr.length
  let u8arr = new Uint8Array(n)
  while (n--) {
    u8arr[n] = bstr.charCodeAt(n)
  }
  return new File([u8arr], new Date().getTime() + '.png', { type: mime })
}

const downloadModelAsImage = () => {
  downloadControls()
  setTimeout(() => {
    if (renderer) {
      // 渲染场景到canvas
      renderer.render(scene, camera)
      // 获取canvas的数据URL，并确保使用PNG格式以保留透明度
      const dataUrl = renderer.domElement.toDataURL('image/png', 1.0) // 参数1.0表示使用最高质量
      // 创建一个隐藏的a标签来下载图片
      const link = document.createElement('a')
      link.href = dataUrl
      link.download = 'model.png' // 文件名
      link.style.display = 'none'
      document.body.appendChild(link)
      // 触发点击事件
      link.click()
      // 清理
      document.body.removeChild(link)
    }
  }, 1500)
}

// 上传到OSS
const uploadFileToServer = async (blob) => {
  FileApi.uploadOss({
    file: blob,
    fileName: blob.name || 'custom.png',
    folder: 'odm-3D'
  })
    .then((res) => {
      let { code, data } = res
      if (code == 0) {
        odmStore.url3D = data
      }
    })
    .catch((err) => {
      console.log(err)
    })
}

const nextPage = () => {
  downloadControls()
  setTimeout(() => {
    if (renderer) {
      // 渲染场景到canvas
      renderer.render(scene, camera)
      // 获取canvas的数据URL，并确保使用PNG格式以保留透明度
      const dataUrl = renderer.domElement.toDataURL('image/png', 1.0) // 参数1.0表示使用最高质量
      const blob = base64TOFile(dataUrl)
      console.log(blob)
      uploadFileToServer(blob)
    }
    router.push({
      name: 'DocManageDemo'
    })
  }, 1500)
}

const onWindowResize = () => {
  console.log('onWindowResize')
  if (camera) {
    // 重新计算相机的aspect值
    const aspect = (window.innerWidth - indentValue.value) / window.innerHeight
    camera.aspect = aspect
    camera.updateProjectionMatrix()
  }
  if (renderer) {
    renderer.setSize(window.innerWidth - indentValue.value, window.innerHeight)
    renderer.setPixelRatio(window.devicePixelRatio)
  }

  windowWidth.value = window.innerWidth - indentValue.value
  windowHeight.value = window.innerHeight
}

const initPanZoom = () => {
  panzoomSvg.value = Panzoom(svgContainer.value, {
    // 禁用平移
    beforeMouseDown: function (e) {
      let shouldIgnore = !e.altKey
      return shouldIgnore
    },
    smoothScroll: true
  })

  panzoomSvg.value.on('zoom', function (e) {
    // x y scale
    let transformObj = panzoomSvg.value.getTransform()
    console.log('transformObj', transformObj)
    rulerOptions.dragOffsetX = transformObj.x + 20
    rulerOptions.dragOffsetY = transformObj.y + 20
    console.log(rulerOptions.dragOffsetX)
    scaleRatio.value = transformObj.scale
    dragPositionX.value = 0
    dragPositionY.value = 0
    dragPositionX.value = rulerOptions.dragOffsetX * window.devicePixelRatio
    dragPositionY.value = rulerOptions.dragOffsetY * window.devicePixelRatio
    if (logoActive.value) {
      dragRulerW.value = dragSyncW.value * transformObj.scale * window.devicePixelRatio
      dragRulerH.value = dragSyncH.value * transformObj.scale * window.devicePixelRatio
    }
  })
}

onMounted(() => {
  initScene()

  // 添加事件监听器
  window.addEventListener('resize', onWindowResize)

  if (odmStore.isOpenDemo) {
    openDemo()
  }

  // initPanZoom()
})

const removeFun = () => {
  window.removeEventListener('resize', onWindowResize)
  document.removeEventListener('click', handleClickOutside)
  unloadModel()
}
// 在组件卸载时释放事件
onUnmounted(() => {
  removeFun()
})

onBeforeRouteLeave((to, from, next) => {
  removeFun()
  next()
})

// 卸载模型
const unloadModel = () => {
  if (model) {
    model.traverse((node) => {
      if (node.isMesh) {
        node.geometry.dispose()
        node.material.dispose()
      }
    })
    // 移除模型
    scene.remove(model)
    model = null
  }
  disposeControls()
  disposeRenderer()
}
// 清理控制器
const disposeControls = () => {
  if (controls) {
    controls.dispose()
    controls = null
  }
}
// 清理渲染器
const disposeRenderer = () => {
  if (renderer && canvasContainer.value) {
    renderer.dispose()
    canvasContainer.value.removeChild(renderer.domElement)
  }
}
</script>
<style scoped lang="scss">
.outer-container {
  width: 100%;
  height: 100vh;
  position: relative;
  .wg {
    position: absolute;
    top: 55px;
    left: 0;
    z-index: 2;
    background-image: linear-gradient(90deg, transparent 0px, #eee 0px, transparent 1px),
      linear-gradient(0deg, transparent 0px, #eee 0px, transparent 1px);
    background-size: 5px 5px; // 每小格间隔大小
    pointer-events: none;
  }
  .canvas-container {
    position: absolute;
    top: 40px;
    left: 0;
    background: #e0dede;
  }
  .oper-wrap {
    position: absolute;
    top: 0;
    right: 0;
    width: 300px;
    height: 100vh;
    padding: 20px;
    background: #fff;
    overflow-y: auto; /* 如果需要滚动条 */
    .logo-label,
    .color-label {
      font-family: 'Inter', Arial, sans-serif;
      font-weight: 400;
      font-size: 15px;
      color: #323232;
      line-height: 18px;
      text-align: left;
      font-style: normal;
      text-transform: none;
    }
    .logo-box {
      width: 113px;
      height: 113px;
      background: #f5f6fa;
      border-radius: 11px 11px 11px 11px;
      margin-top: 10px;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    .logo-img {
      width: 98px;
      height: 98px;
      background: #ffffff;
      border-radius: 10px;
      border: 1px dashed #c7deff;
    }
    .color-label2 {
      margin-top: 20px;
    }
    .color-label3 {
      margin-top: 10px;
      width: 60px;
    }
    .color-box {
      width: 100%;
      height: 43px;
      border-radius: 4px;
      display: flex;
      align-items: center;
      margin-top: 26px;
      .color-text {
        width: 50%;
        height: calc(100% - 6px);
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 500;
        border: 2px solid #e9e9e9;
        border-radius: 4px;
        margin-left: 1px;
        margin-right: 1px;
        cursor: pointer;
      }
      .color-active {
        background: #fff;
      }
    }
    .color-reco {
      margin-top: 10px;
      .color-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(28px, 1fr));
        grid-gap: 5px;
        margin-top: 10px;
        width: 100%;
      }

      .color-block {
        width: 28px;
        height: 28px;
        border-radius: 5px;
        border: 1px solid #e9e9e9;
      }
      .selected {
        border-color: #2788fe; /* 选中时的边框颜色 */
      }
    }
    .advanced {
      margin-top: 20px;
      position: relative;
    }
    .upload-model {
      margin-top: 20px;
    }
    .btn-group {
      margin-top: 26px;
      .tips {
        font-size: 12px;
        color: #b8b8b8;
        margin-top: 20px;
      }
    }
  }
  .num-box {
    margin-top: 10px;
    font-size: 14px;
  }
  .bottom-btn {
    width: calc(100% - 360px);
    position: absolute;
    left: 0;
    bottom: -40px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    z-index: 9;
    padding: 10px;
    .tips {
      color: #aaa;
      font-size: 12px;
      display: flex;
      align-items: center;
    }
    .color-tips {
      color: #aaa;
      font-size: 12px;
    }
  }
  .colors-svg {
    width: 36px;
    height: 36px;
    cursor: pointer;
  }
  .mouse-left {
    width: 25px;
    height: 25px;
    cursor: pointer;
  }
  // :deep(.el-color-picker__trigger) {
  //   display: none; /* 隐藏默认的触发器 */
  // }
  .top-btn {
    position: absolute;
    left: 50%;
    top: 0;
    transform: translateX(-50%);
    margin-left: -180px;
  }
  .ruler-col {
    position: absolute;
    left: -20px;
    top: 55px;
  }
  .ruler-row {
    position: absolute;
    left: 0;
    top: 35px;
  }

  .d2-container {
    position: absolute;
    top: 55px;
    left: 0;
  }
  #main {
    width: 500px;
    height: 300px;
    border: 1px gray solid;
    position: absolute;
    left: 50%;
    top: 50%;
    transform: translate(-50%, -50%);
    margin-top: -50px;
  }

  .vue-drag-resize-rotate {
    border: none;
  }
  .svg-container {
    position: absolute;
    left: 20px;
    top: 20px;
  }
}
</style>

<style lang="scss">
.custom-color-picker-popover {
  inset: 480px auto auto 1110px !important;
}
.progress {
  max-width: 400px;
  position: relative;
  top: calc(50% + 70px);
  left: 50%;
  transform: translate(-50%, -50%);
  z-index: 999999;
}
.progress .el-progress--line {
  max-width: 400px;
}
</style>
