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
      <el-form-item label="公司名称" prop="name">
        <el-input
          v-model="queryParams.name"
          placeholder="请输入公司名称"
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
        <el-button type="primary" plain @click="openForm('create')">
          <Icon icon="ep:plus" class="mr-5px" />
          新增
        </el-button>
      </el-form-item>
    </el-form>
  </ContentWrap>

  <!-- 列表 -->
  <ContentWrap>
    <el-table v-loading="loading" :data="list">
      <el-table-column
        label="公司名称"
        align="center"
        prop="company"
        :show-overflow-tooltip="true"
      />
      <el-table-column label="简称" align="center" prop="shortName" :show-overflow-tooltip="true" />
      <el-table-column
        label="公司地址"
        align="center"
        prop="address"
        :show-overflow-tooltip="true"
      />

      <el-table-column
        label="服务热线"
        align="center"
        prop="hotline"
        :show-overflow-tooltip="true"
      />
      <el-table-column
        label="邮箱"
        align="center"
        prop="email"
        :show-overflow-tooltip="true"
        width="180"
      />

      <el-table-column
        label="网址"
        align="center"
        prop="url"
        :show-overflow-tooltip="true"
        width="180"
      />

      <el-table-column
        label="传真"
        align="center"
        prop="fax"
        :show-overflow-tooltip="true"
        width="180"
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
          <el-button link type="primary" @click="openForm('update', scope.row.id)">编辑</el-button>
          <el-button
            v-hasPermi="['odm:import-data-record:delete']"
            link
            type="danger"
            @click="handleDelete(scope.row.id)"
            >删除</el-button
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
</template>
<script lang="ts" setup>
import { dateFormatter } from '@/utils/formatTime'
import * as OdmApi from '@/api/odm'
import { ref } from 'vue'
import { useRouter } from 'vue-router'

defineOptions({ name: 'BasicInfoDemo' })

const router = useRouter()

const message = useMessage() // 消息弹窗
const { t } = useI18n() // 国际化

const loading = ref(false) // 列表的加载中
const total = ref(0) // 列表的总页数
const list = ref([
  {
    company: '爱士惟科技股份有限公司',
    shortName: '爱士惟',
    address: '上海市黄浦区南车站路600弄18号',
    hotline: '021-131313131',
    email: '1313131@163.com',
    url: 'https://solar.huawei.com/cn?utm_medium=cpc&utm_source=baidu&utm_campaign=2024sem&utm_content=brand&utm_term=%E7%88%B1%E5%A3%AB%E6%83%9F',
    fax: 12312313,
    createTime: 1716369355000,
    QRCodeFileList: undefined,
    logoFileList: undefined
  }
]) // 列表的数据

const queryParams = reactive({
  pageNo: 1,
  pageSize: 10,
  name: undefined,
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

const openForm = () => {
  router.push({
    name: 'AddDemo'
  })
}

/** 删除按钮操作 */
const handleDelete = async (id: number) => {
  try {
    // 删除的二次确认
    await message.delConfirm()
    // 发起删除
    await OdmApi.deleteInfo(id)
    message.success(t('common.delSuccess'))
    // 刷新列表
    await getList()
  } catch {}
}

/** 初始化 **/
onMounted(async () => {
  // await getList()
})
</script>
