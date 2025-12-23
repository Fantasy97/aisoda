<template>
  <div class="logistics">
    <el-card shadow="hover">
      <template #header>
        <div class="card-header">
          <span>订单号</span>
          <el-tag>{{ order.orderID }}</el-tag>
        </div>
      </template>
      <div>
        <el-table :data="logisticsData" style="width: 100%; height: 300px" stripe>
          <el-table-column prop="status" label="状态" width="180" />
          <el-table-column prop="time" label="时间" width="180" :formatter="dateFormatter" />
        </el-table>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { dateFormatter } from '@/utils/formatTime'

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
  ],
  logistics: [
    {
      status: '订单创建',
      time: '2024-08-20T08:00:00Z'
    },
    {
      status: '商家确认订单',
      time: '2024-08-20T09:30:00Z'
    },
    {
      status: '准备发货',
      time: '2024-08-20T12:00:00Z'
    },
    {
      status: '已发货',
      time: '2024-08-20T14:00:00Z'
    },
    {
      status: '在途',
      time: '2024-08-22T08:00:00Z'
    },
    {
      status: '即将到达',
      time: '2024-08-23T10:00:00Z'
    },
    {
      status: '已送达',
      time: '2024-08-24T14:00:00Z'
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
