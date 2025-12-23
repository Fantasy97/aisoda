<template>
  <div class="logistics">
    <el-card shadow="hover">
      <div>
        <el-descriptions :column="1" border>
          <el-descriptions-item label="名称">{{ order.buyerName }}</el-descriptions-item>
          <el-descriptions-item label="地址">{{ order.buyerAddress }}</el-descriptions-item>
          <el-descriptions-item label="产品详情">
            <ul class="product-detail" v-for="(item, index) in order.items" :key="index">
              <li>名称：{{ item.productName }}</li>
              <li>数量：{{ item.quantity }}</li>
              <li>功率：{{ item.power }}</li>
              <li>订单状态：{{ item.productionStatus }}</li>
              <li>产品状态：{{ item.batch }}</li>
            </ul>
          </el-descriptions-item>
        </el-descriptions>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const order = ref({
  orderID: 'ORDER-20240826001',
  buyerName: '爱士惟',
  buyerAddress: '上海市黄浦区南车站路600弄18号',
  items: [
    {
      productID: 'PROD-001',
      productName: 'ASW6000-S',
      quantity: 1,
      power: '1MW', // 1 兆瓦
      productionStatus: '已下单', // 量产状态
      batch: '量产'
    },
    {
      productID: 'PROD-002',
      productName: 'ASW8000-S',
      quantity: 2,
      power: '1MW', // 1 兆瓦
      productionStatus: '已下单', // 量产状态
      batch: '量产'
    }
  ]
})

const logisticsData = ref(order.value.logistics)
</script>

<style scoped lang="scss">
.logistics {
  margin-top: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header span {
  font-size: 18px;
  font-weight: bold;
}

.product-detail {
  list-style-type: none;
}

/* 滚动条整体样式 */
.logistics-Info::-webkit-scrollbar {
  width: 10px; /* 宽度 */
}

/* 滚动条滑块样式 */
.logistics-Info::-webkit-scrollbar-thumb {
  background: #e6e5e5; /* 滑块颜色 */
  border-radius: 10px; /* 圆角 */
}

/* 滚动条滑块悬停样式 */
.logistics-Info::-webkit-scrollbar-thumb:hover {
  background: #c3c2c2; /* 悬停颜色 */
}

/* 滚动条轨道样式 */
.logistics-Info::-webkit-scrollbar-track {
  background: #f1f1f1; /* 轨道颜色 */
  border-radius: 10px; /* 圆角 */
}
</style>
