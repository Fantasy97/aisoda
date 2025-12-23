# 通用数据库表 CRUD API 设计方案

## 一、当前数据库实现分析

### 1.1 现有实现
- **数据库类型**: MySQL
- **连接库**: PyMySQL
- **数据库类**: `Database` 类封装了基础的数据库操作
- **现有方法**:
  - `execute_query()` - 执行查询，返回多条记录
  - `execute_one()` - 执行查询，返回单条记录
  - `execute_update()` - 执行更新/插入/删除
  - `execute_many()` - 批量执行SQL
  - `get_tables()` - 获取所有表名
  - `get_table_columns()` - 获取表结构信息
  - `test_connection()` - 测试连接

### 1.2 数据库表结构特点
- 所有表都有通用字段：`id`（主键自增）、`creator`、`is_valid`、`create_time`、`updater`、`update_time`
- 主要业务表：
  - `odm_bom_mapping` - 型号映射表
  - `odm_bom_record` - BOM记录表
  - `odm_bom_record_log` - BOM记录日志表
  - `odm_company_info` - 公司信息表
  - `odm_request_order` - 请求订单表
  - `odm_request_order_log` - 请求订单日志表

---

## 二、设计方案概述

### 2.1 设计目标
1. **通用性**: 通过POST请求，前端可以操作任意指定的数据库表
2. **安全性**: 通过表名白名单机制，防止SQL注入和未授权访问
3. **易用性**: 统一的请求/响应格式，支持分页、排序、过滤等高级功能
4. **可扩展性**: 易于添加新的表或扩展功能

### 2.2 技术选型
- **Web框架**: FastAPI（推荐）或 Flask
  - FastAPI优势：自动生成API文档、类型检查、异步支持、性能好
  - Flask优势：轻量级、简单易用
- **数据验证**: Pydantic（FastAPI自带）或 Marshmallow（Flask）
- **CORS**: 支持跨域请求

### 2.3 架构设计

```
前端 (Vue)
    ↓ POST请求
API层 (FastAPI/Flask)
    ↓ 参数验证、表名白名单检查
服务层 (CrudService)
    ↓ 业务逻辑处理
数据访问层 (Database)
    ↓ SQL执行
MySQL数据库
```

---

## 三、API 端点设计

### 3.1 基础路径
- **开发环境**: `http://localhost:8000`
- **API前缀**: `/api/crud`

### 3.2 端点列表

| 操作 | 端点 | 方法 | 说明 |
|------|------|------|------|
| 创建单条记录 | `/api/crud/create` | POST | 插入一条新记录 |
| 批量创建记录 | `/api/crud/batch_create` | POST | 批量插入多条记录 |
| 根据ID查询 | `/api/crud/get` | POST | 根据主键ID查询单条记录 |
| 列表查询 | `/api/crud/list` | POST | 分页查询多条记录，支持过滤和排序 |
| 更新记录 | `/api/crud/update` | POST | 根据ID更新记录 |
| 删除记录 | `/api/crud/delete` | POST | 根据ID删除记录 |
| 批量删除 | `/api/crud/batch_delete` | POST | 批量删除多条记录 |
| 获取表列表 | `/api/tables` | GET | 获取允许操作的表名列表 |
| 获取表信息 | `/api/table/{table_name}/info` | GET | 获取指定表的结构信息 |

---

## 四、POST 请求规范

### 4.1 统一请求格式

所有POST请求使用 `application/json` 格式，Content-Type: `application/json`

### 4.2 创建单条记录 - `/api/crud/create`

**请求体**:
```json
{
  "table_name": "odm_bom_mapping",
  "data": {
    "product_model": "MODEL-001",
    "latest_bom": "BOM-001",
    "product_series": "Series-A",
    "device_type": "Type-1",
    "creator": "admin",
    "is_valid": 1
  }
}
```

**字段说明**:
- `table_name` (string, 必填): 表名，必须在白名单中
- `data` (object, 必填): 要插入的数据，键为字段名，值为字段值
  - 不需要包含 `id` 字段（自增主键会自动生成）
  - 不需要包含 `create_time`、`update_time`（数据库自动处理）

**响应示例**:
```json
{
  "success": true,
  "message": "创建记录成功",
  "data": {
    "id": 123,
    "product_model": "MODEL-001",
    "latest_bom": "BOM-001",
    "product_series": "Series-A",
    "device_type": "Type-1",
    "creator": "admin",
    "is_valid": 1,
    "create_time": "2025-01-15 10:30:00",
    "update_time": "2025-01-15 10:30:00"
  }
}
```

---

### 4.3 批量创建记录 - `/api/crud/batch_create`

**请求体**:
```json
{
  "table_name": "odm_bom_mapping",
  "data_list": [
    {
      "product_model": "MODEL-001",
      "latest_bom": "BOM-001",
      "product_series": "Series-A"
    },
    {
      "product_model": "MODEL-002",
      "latest_bom": "BOM-002",
      "product_series": "Series-B"
    }
  ]
}
```

**字段说明**:
- `table_name` (string, 必填): 表名
- `data_list` (array, 必填): 要插入的数据列表，每个元素是一个对象

**响应示例**:
```json
{
  "success": true,
  "message": "批量创建成功，共创建 2 条记录",
  "data": {
    "success_count": 2,
    "inserted_ids": [123, 124]
  }
}
```

---

### 4.4 根据ID查询 - `/api/crud/get`

**请求体**:
```json
{
  "table_name": "odm_bom_mapping",
  "record_id": 123,
  "id_field": "id"
}
```

**字段说明**:
- `table_name` (string, 必填): 表名
- `record_id` (any, 必填): 记录ID值（可以是数字或字符串）
- `id_field` (string, 可选): ID字段名，默认为 `"id"`

**响应示例**:
```json
{
  "success": true,
  "message": "获取记录成功",
  "data": {
    "id": 123,
    "product_model": "MODEL-001",
    "latest_bom": "BOM-001",
    "product_series": "Series-A",
    "device_type": "Type-1",
    "creator": "admin",
    "is_valid": 1,
    "create_time": "2025-01-15 10:30:00",
    "update_time": "2025-01-15 10:30:00"
  }
}
```

**记录不存在时**:
```json
{
  "success": false,
  "message": "记录不存在",
  "data": null
}
```

---

### 4.5 列表查询 - `/api/crud/list`

**请求体**:
```json
{
  "table_name": "odm_bom_mapping",
  "filters": {
    "is_valid": 1,
    "product_model": "MODEL-001",
    "create_time": {
      "$gte": "2025-01-01 00:00:00",
      "$lte": "2025-01-31 23:59:59"
    }
  },
  "order_by": "create_time DESC",
  "page": 1,
  "page_size": 20
}
```

**字段说明**:
- `table_name` (string, 必填): 表名
- `filters` (object, 可选): 查询条件
  - **简单等值查询**: `{"field": "value"}` → `WHERE field = 'value'`
  - **IN查询**: `{"field": [value1, value2]}` → `WHERE field IN (value1, value2)`
  - **比较操作符**:
    - `{"field": {"$gt": value}}` → `WHERE field > value` (大于)
    - `{"field": {"$gte": value}}` → `WHERE field >= value` (大于等于)
    - `{"field": {"$lt": value}}` → `WHERE field < value` (小于)
    - `{"field": {"$lte": value}}` → `WHERE field <= value` (小于等于)
    - `{"field": {"$ne": value}}` → `WHERE field != value` (不等于)
    - `{"field": {"$like": "%value%"}}` → `WHERE field LIKE '%value%'` (模糊查询)
- `order_by` (string, 可选): 排序字段，格式 `"字段名 ASC"` 或 `"字段名 DESC"`
  - 示例: `"create_time DESC"`, `"id ASC"`
- `page` (integer, 可选): 页码，从1开始，默认1
- `page_size` (integer, 可选): 每页条数，默认20，最大1000

**响应示例**:
```json
{
  "success": true,
  "message": "查询记录成功",
  "data": {
    "data": [
      {
        "id": 123,
        "product_model": "MODEL-001",
        "latest_bom": "BOM-001",
        "create_time": "2025-01-15 10:30:00"
      },
      {
        "id": 124,
        "product_model": "MODEL-002",
        "latest_bom": "BOM-002",
        "create_time": "2025-01-14 09:20:00"
      }
    ],
    "total": 50,
    "page": 1,
    "page_size": 20,
    "total_pages": 3
  }
}
```

**过滤条件示例**:

1. **等值查询**:
```json
{
  "filters": {
    "is_valid": 1,
    "product_model": "MODEL-001"
  }
}
```

2. **IN查询**:
```json
{
  "filters": {
    "product_model": ["MODEL-001", "MODEL-002", "MODEL-003"]
  }
}
```

3. **范围查询**:
```json
{
  "filters": {
    "create_time": {
      "$gte": "2025-01-01 00:00:00",
      "$lte": "2025-01-31 23:59:59"
    }
  }
}
```

4. **模糊查询**:
```json
{
  "filters": {
    "product_model": {
      "$like": "%MODEL%"
    }
  }
}
```

5. **组合查询**:
```json
{
  "filters": {
    "is_valid": 1,
    "product_model": {
      "$like": "%MODEL%"
    },
    "create_time": {
      "$gte": "2025-01-01 00:00:00"
    }
  }
}
```

---

### 4.6 更新记录 - `/api/crud/update`

**请求体**:
```json
{
  "table_name": "odm_bom_mapping",
  "record_id": 123,
  "data": {
    "product_model": "MODEL-001-UPDATED",
    "latest_bom": "BOM-001-NEW",
    "updater": "admin"
  },
  "id_field": "id"
}
```

**字段说明**:
- `table_name` (string, 必填): 表名
- `record_id` (any, 必填): 记录ID
- `data` (object, 必填): 要更新的字段，只包含需要更新的字段
  - 不需要包含 `id` 字段（主键不能更新）
  - 不需要包含 `create_time`（创建时间不变）
  - `update_time` 由数据库自动更新
- `id_field` (string, 可选): ID字段名，默认为 `"id"`

**响应示例**:
```json
{
  "success": true,
  "message": "更新记录成功",
  "data": {
    "id": 123,
    "product_model": "MODEL-001-UPDATED",
    "latest_bom": "BOM-001-NEW",
    "updater": "admin",
    "update_time": "2025-01-15 11:00:00"
  }
}
```

**记录不存在时**:
```json
{
  "success": false,
  "message": "记录不存在或更新失败",
  "data": null
}
```

---

### 4.7 删除记录 - `/api/crud/delete`

**请求体**:
```json
{
  "table_name": "odm_bom_mapping",
  "record_id": 123,
  "id_field": "id"
}
```

**字段说明**:
- `table_name` (string, 必填): 表名
- `record_id` (any, 必填): 记录ID
- `id_field` (string, 可选): ID字段名，默认为 `"id"`

**响应示例**:
```json
{
  "success": true,
  "message": "删除记录成功",
  "data": null
}
```

**记录不存在时**:
```json
{
  "success": false,
  "message": "记录不存在或删除失败",
  "data": null
}
```

---

### 4.8 批量删除 - `/api/crud/batch_delete`

**请求体**:
```json
{
  "table_name": "odm_bom_mapping",
  "record_ids": [123, 124, 125],
  "id_field": "id"
}
```

**字段说明**:
- `table_name` (string, 必填): 表名
- `record_ids` (array, 必填): 要删除的记录ID列表
- `id_field` (string, 可选): ID字段名，默认为 `"id"`

**响应示例**:
```json
{
  "success": true,
  "message": "批量删除成功，共删除 3 条记录",
  "data": {
    "success_count": 3,
    "total_count": 3
  }
}
```

---

## 五、统一响应格式

### 5.1 成功响应
```json
{
  "success": true,
  "message": "操作成功描述",
  "data": { /* 具体数据 */ }
}
```

### 5.2 失败响应
```json
{
  "success": false,
  "message": "错误描述信息",
  "data": null
}
```

### 5.3 HTTP状态码
- `200 OK`: 请求成功
- `400 Bad Request`: 请求参数错误（表名不在白名单、参数格式错误等）
- `404 Not Found`: 资源不存在（记录不存在等）
- `500 Internal Server Error`: 服务器内部错误（数据库连接失败、SQL执行错误等）

---

## 六、安全机制

### 6.1 表名白名单
- 维护一个允许操作的表名白名单
- 所有请求中的 `table_name` 必须在白名单中
- 防止SQL注入和未授权访问

**白名单配置示例**:
```python
ALLOWED_TABLES = {
    'odm_bom_mapping',
    'odm_bom_record',
    'odm_bom_record_log',
    'odm_company_info',
    'odm_request_order',
    'odm_request_order_log'
}
```

### 6.2 SQL注入防护
- 使用参数化查询，所有用户输入都通过参数传递
- 表名和字段名通过白名单验证，不使用用户输入直接拼接
- 字段值使用参数化绑定

### 6.3 输入验证
- 使用 Pydantic 或 Marshmallow 进行请求参数验证
- 验证字段类型、必填项、取值范围等
- 防止恶意数据输入

### 6.4 CORS配置
- 生产环境应配置具体的允许来源
- 开发环境可以允许所有来源（`*`）

---

## 七、错误处理

### 7.1 错误类型

| 错误类型 | HTTP状态码 | 说明 |
|---------|-----------|------|
| 表名不在白名单 | 400 | `table_name` 不在允许的操作列表中 |
| 参数验证失败 | 400 | 请求参数格式错误或缺少必填字段 |
| 记录不存在 | 404 | 查询的记录ID不存在 |
| 数据库连接失败 | 500 | 无法连接到数据库 |
| SQL执行错误 | 500 | SQL语句执行失败（字段不存在、类型不匹配等） |
| 未知错误 | 500 | 其他未预期的错误 |

### 7.2 错误响应示例

**表名不在白名单**:
```json
{
  "success": false,
  "message": "表名 'unauthorized_table' 不在允许的操作列表中",
  "data": null
}
```

**参数验证失败**:
```json
{
  "success": false,
  "message": "请求参数错误: table_name 字段是必填的",
  "data": null
}
```

**记录不存在**:
```json
{
  "success": false,
  "message": "记录不存在",
  "data": null
}
```

**数据库错误**:
```json
{
  "success": false,
  "message": "数据库操作失败: Field 'unknown_field' doesn't exist",
  "data": null
}
```

---

## 八、辅助接口

### 8.1 获取表列表 - `GET /api/tables`

**请求**: 无参数

**响应**:
```json
{
  "success": true,
  "message": "获取表列表成功",
  "data": [
    "odm_bom_mapping",
    "odm_bom_record",
    "odm_bom_record_log",
    "odm_company_info",
    "odm_request_order",
    "odm_request_order_log"
  ]
}
```

### 8.2 获取表信息 - `GET /api/table/{table_name}/info`

**请求**: URL路径参数 `table_name`

**响应**:
```json
{
  "success": true,
  "message": "获取表信息成功",
  "data": {
    "table_name": "odm_bom_mapping",
    "columns": [
      {
        "Field": "id",
        "Type": "bigint(20)",
        "Null": "NO",
        "Key": "PRI",
        "Default": null,
        "Extra": "auto_increment"
      },
      {
        "Field": "product_model",
        "Type": "varchar(100)",
        "Null": "YES",
        "Key": "MUL",
        "Default": null,
        "Extra": ""
      }
      // ... 其他字段
    ],
    "primary_key": "id"
  }
}
```

---

## 九、实现建议

### 9.1 代码结构
```
src/backend/
├── db/
│   └── database.py          # 数据库操作类（已存在）
├── api/
│   ├── __init__.py
│   ├── app.py              # FastAPI应用主文件
│   ├── crud_service.py    # CRUD服务类
│   └── models.py          # Pydantic请求/响应模型
└── requirements.txt        # 依赖包列表
```

### 9.2 需要扩展的 Database 方法
- `get_primary_key(table_name)` - 获取表的主键字段名
- `insert(table_name, data)` - 插入记录
- `update_by_id(table_name, record_id, data, id_field)` - 根据ID更新
- `delete_by_id(table_name, record_id, id_field)` - 根据ID删除
- `find_by_id(table_name, record_id, id_field)` - 根据ID查询
- `find_all(table_name, where, order_by, limit, offset)` - 查询多条记录
- `count(table_name, where)` - 统计记录数

### 9.3 依赖包
```
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
pymysql>=1.1.0
pydantic>=2.0.0
```

---

## 十、使用示例

### 10.1 前端调用示例（JavaScript/Vue）

```javascript
// 创建记录
async function createRecord(tableName, data) {
  const response = await fetch('http://localhost:8000/api/crud/create', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      table_name: tableName,
      data: data
    })
  });
  return await response.json();
}

// 查询列表
async function listRecords(tableName, filters, page = 1, pageSize = 20) {
  const response = await fetch('http://localhost:8000/api/crud/list', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      table_name: tableName,
      filters: filters,
      page: page,
      page_size: pageSize,
      order_by: 'create_time DESC'
    })
  });
  return await response.json();
}

// 更新记录
async function updateRecord(tableName, recordId, data) {
  const response = await fetch('http://localhost:8000/api/crud/update', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      table_name: tableName,
      record_id: recordId,
      data: data
    })
  });
  return await response.json();
}

// 删除记录
async function deleteRecord(tableName, recordId) {
  const response = await fetch('http://localhost:8000/api/crud/delete', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      table_name: tableName,
      record_id: recordId
    })
  });
  return await response.json();
}
```

---

## 十一、总结

### 11.1 方案优势
1. **统一接口**: 所有表的CRUD操作使用相同的接口规范
2. **安全性高**: 表名白名单 + 参数化查询，有效防止SQL注入
3. **功能完善**: 支持分页、排序、复杂过滤、批量操作
4. **易于使用**: 清晰的请求/响应格式，前端调用简单
5. **可扩展**: 易于添加新表或扩展功能

### 11.2 注意事项
1. 生产环境需要配置具体的CORS允许来源
2. 考虑添加身份认证和权限控制
3. 对于敏感操作（如删除），可以考虑添加软删除或操作日志
4. 大数据量查询时，注意性能优化和索引使用
5. 建议添加请求频率限制，防止恶意请求

---

**文档版本**: v1.0  
**创建时间**: 2025-01-15  
**最后更新**: 2025-01-15
