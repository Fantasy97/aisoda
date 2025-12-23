# 数据查询API服务

基于Flask的数据查询API服务，提供三个主要接口来调用data_query.py的功能。

## 安装依赖

```bash
pip install -r requirements.txt
```

## 启动服务

```bash
python app.py
```

服务将在 `http://localhost:5000` 启动

## 前端页面访问

启动服务后，可以通过以下地址访问前端页面：

- **信息搜索页面**: http://localhost:5000/
- **历史数据页面**: http://localhost:5000/history

前端页面已集成到Flask服务中，无需单独启动前端服务器。

## API接口

### 1. 数据查询接口

**POST** `/api/query`

查询数据，支持模糊匹配和上下文推荐。

**请求体：**
```json
{
    "keyword": "营业收入",
    "include_context": true,
    "case_sensitive": false
}
```

**响应：**
```json
{
    "success": true,
    "message": "找到 2 条结果",
    "data": [
        {
            "key": "营业收入",
            "value": "1000万元",
            "数据源": "example_data.json",
            "查询方式": "模糊匹配"
        }
    ]
}
```

### 2. 历史文件列表接口

**GET** `/api/history`

获取data/history目录下所有JSON文件的信息。

**响应：**
```json
{
    "success": true,
    "message": "找到 3 个文件",
    "data": [
        {
            "文件名": "2023_data.json",
            "记录数量": 150,
            "文件路径": "/path/to/data/history/2023_data.json"
        }
    ]
}
```

### 3. 文件内容获取接口

**GET** `/api/file/<filename>`

根据文件名获取data/history目录下的完整JSON内容。

**示例：** `GET /api/file/2023_data.json`

**响应：**
```json
{
    "success": true,
    "message": "成功读取文件: 2023_data.json",
    "file_info": {
        "文件名": "2023_data.json",
        "相对路径": "data/history/2023_data.json",
        "绝对路径": "/full/path/to/file",
        "记录数量": 150
    },
    "data": {
        // 文件的完整JSON内容
    }
}
```

### 4. 删除历史文件接口

**DELETE** `/api/history/<filename>`

删除data/history目录下的指定文件。

**示例：** `DELETE /api/history/example.json`

**响应：**
```json
{
    "success": true,
    "message": "文件 example.json 已成功删除"
}
```

**错误响应：**
```json
{
    "success": false,
    "message": "文件不存在: example.json"
}
```

### 5. Word文档解析接口

**POST** `/api/parse-word`

解析Word文档，提取文档结构和内容。

**请求体：**
```json
{
    "input_file": "path/to/document.docx",
    "output_path": "path/to/output.json"
}
```

**响应：**
```json
{
    "success": true,
    "message": "文档解析成功",
    "data": {
        "document_structure": [
            {
                "type": "paragraph",
                "position": 0,
                "content": "文档内容",
                "paragraph_index": 0
            },
            {
                "type": "table",
                "position": 1,
                "table_index": 0,
                "structure": {
                    "rows": 3,
                    "columns": 4,
                    "cell_map": [...]
                }
            }
        ],
        "statistics": {
            "total_items": 10,
            "paragraphs": 8,
            "tables": 2
        },
        "output_file": "path/to/output.json"
    }
}
```

### 6. 健康检查接口

**GET** `/api/health`

检查API服务状态。

**响应：**
```json
{
    "success": true,
    "message": "API服务运行正常",
    "version": "1.0.0"
}
```

## 测试示例

### 使用curl测试

```bash
# 1. 健康检查
curl http://localhost:5000/api/health

# 2. 数据查询
curl -X POST http://localhost:5000/api/query \
  -H "Content-Type: application/json" \
  -d '{"keyword": "营业收入", "include_context": true}'

# 3. 获取历史文件列表
curl http://localhost:5000/api/history

# 4. 获取特定文件内容
curl http://localhost:5000/api/file/example.json

# 5. 删除历史文件
curl -X DELETE http://localhost:5000/api/history/example.json

# 6. Word文档解析
curl -X POST http://localhost:5000/api/parse-word \
  -H "Content-Type: application/json" \
  -d '{"input_file": "path/to/document.docx", "output_path": "output.json"}'
```

### 使用Python requests测试

```python
import requests
import json

base_url = "http://localhost:5000"

# 数据查询
response = requests.post(f"{base_url}/api/query", 
    json={"keyword": "营业收入", "include_context": True})
print(json.dumps(response.json(), ensure_ascii=False, indent=2))

# 获取历史文件
response = requests.get(f"{base_url}/api/history")
print(json.dumps(response.json(), ensure_ascii=False, indent=2))

# 获取文件内容
response = requests.get(f"{base_url}/api/file/example.json")
print(json.dumps(response.json(), ensure_ascii=False, indent=2))

# 删除历史文件
response = requests.delete(f"{base_url}/api/history/example.json")
print(json.dumps(response.json(), ensure_ascii=False, indent=2))

# Word文档解析
response = requests.post(f"{base_url}/api/parse-word", 
    json={"input_file": "path/to/document.docx", "output_path": "output.json"})
print(json.dumps(response.json(), ensure_ascii=False, indent=2))
```

## 错误处理

所有接口都会返回统一的错误格式：

```json
{
    "success": false,
    "message": "错误描述"
}
```

常见HTTP状态码：
- 200: 成功
- 400: 请求参数错误
- 404: 资源不存在
- 500: 服务器内部错误