<template>
  <!-- 搜索 -->
  <ContentWrap>
    <el-form
      class="-mb-15px"
      :model="queryParams"
      ref="queryFormRef"
      :inline="true"
      label-width="88px"
    >
      <el-form-item label="公司ID" prop="odmEnterpriseId">
        <el-input
          v-model="queryParams.odmEnterpriseId"
          placeholder="请输入公司ID"
          clearable
          @keyup.enter="handleQuery"
          class="!w-240px"
        />
      </el-form-item>
      <el-form-item label="产品ID" prop="odmProductInfoId">
        <el-input
          v-model="queryParams.odmProductInfoId"
          placeholder="请输入产品ID"
          clearable
          @keyup.enter="handleQuery"
          class="!w-240px"
        />
      </el-form-item>
      <el-form-item label="创建时间" prop="createTime">
        <el-date-picker
          v-model="queryParams.createTime"
          value-format="YYYY-MM-DD HH:mm:ss"
          type="daterange"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          :default-time="[new Date('1 00:00:00'), new Date('1 23:59:59')]"
          class="!w-240px"
        />
      </el-form-item>
      <el-form-item>
        <el-button @click="handleQuery">
          <Icon icon="ep:search" class="mr-5px" />
          搜索
        </el-button>
        <el-button @click="resetQuery">
          <Icon icon="ep:refresh" class="mr-5px" />
          重置
        </el-button>
      </el-form-item>
    </el-form>
  </ContentWrap>

  <!-- 列表 -->
  <ContentWrap>
    <el-table v-loading="loading" :data="list">
      <el-table-column label="ID" align="center" prop="id" :show-overflow-tooltip="true" />
      <el-table-column
        label="公司ID"
        align="center"
        prop="odmEnterpriseId"
        :show-overflow-tooltip="true"
      />
      <el-table-column
        label="产品ID"
        align="center"
        prop="odmProductInfoId"
        :show-overflow-tooltip="true"
      />
      <el-table-column
        label="状态"
        align="center"
        prop="taskStatus"
        :show-overflow-tooltip="true"
      />
      <el-table-column
        label="数量"
        align="center"
        prop="taskQuantity"
        :show-overflow-tooltip="true"
        width="180"
      />
      <el-table-column
        label="折扣"
        align="center"
        prop="taskDiscount"
        :show-overflow-tooltip="true"
      />
      <el-table-column
        label="金额"
        align="center"
        prop="orderAmount"
        :show-overflow-tooltip="true"
      />
      <el-table-column
        label="创建时间"
        align="center"
        prop="createTime"
        width="180"
        :formatter="dateFormatter"
      />
      <el-table-column label="操作" align="center" min-width="110" fixed="right">
        <template #default="scope">
          <el-button link type="primary" @click="openForm('readonly', scope.row.id)"
            >查看</el-button
          >
        </template>
      </el-table-column>
    </el-table>
    <!-- 分页 -->
    <Pagination
      :total="total"
      v-model:page="queryParams.pageNo"
      v-model:limit="queryParams.pageSize"
      @pagination="getList"
    />
  </ContentWrap>
  <!-- 表单弹窗：添加/修改 -->
  <detail ref="formRef" @success="getList" />
</template>
<script lang="ts" setup>
import { dateFormatter } from '@/utils/formatTime'
import * as OdmApi from '@/api/odm'
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import detail from './detail.vue'

defineOptions({ name: 'OrderListDemo' })

const router = useRouter()

const loading = ref(false) // 列表的加载中
const total = ref(0) // 列表的总页数
const list = ref([
  {
    id: 1,
    odmEnterpriseId: 1,
    odmProductInfoId: 1,
    taskStatus: '已创建',
    taskQuantity: 2,
    taskDiscount: '立减20%',
    orderAmount: '1000',
    createTime: 1716369355000
  }
]) // 列表的数据

const queryParams = reactive({
  pageNo: 1,
  pageSize: 10,
  odmEnterpriseId: undefined,
  odmProductInfoId: undefined,
  createTime: undefined
})
const queryFormRef = ref() // 搜索的表单

/** 查询列表 */
const getList = async () => {
  loading.value = true
  try {
    const data = await OdmApi.getPage(queryParams)
    list.value = data.list
    total.value = data.total
  } finally {
    loading.value = false
  }
}

/** 搜索按钮操作 */
const handleQuery = () => {
  queryParams.pageNo = 1
  getList()
}

/** 重置按钮操作 */
const resetQuery = () => {
  queryFormRef.value.resetFields()
  handleQuery()
}

/** 添加/修改操作 */
const formRef = ref()
const openForm = (type: string, id?: number) => {
  formRef.value.open(type, id)
}
</script>
