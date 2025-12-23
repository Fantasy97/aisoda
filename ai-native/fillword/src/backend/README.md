# 智能Word表单填充API服务

基于Flask的智能Word表单填充服务，支持Word文档上传、解析、智能填充和下载。

## 🚀 快速开始

### 1. 安装依赖
```bash
# 进入后端目录
cd src/backend

# 安装Python依赖
pip install -r requirements.txt
```

### 2. 启动服务
```bash
# Windows用户
start.bat

# 或者直接运行
python run.py
```

### 3. 访问服务
打开浏览器访问: http://localhost:5000

### 4. 测试功能
```bash
python test_api.py
```

## 📋 功能特性

- **Word文档解析**: 支持.docx和.doc格式文档
- **智能填充**: 基于关键词匹配和上下文分析
- **批量处理**: 一次性处理文档中的所有空白单元格
- **Web界面**: 简洁的文件上传界面
- **RESTful API**: 完整的API接口支持

## 📋 API接口

### 1. 完整处理流程
```http
POST /api/upload
Content-Type: multipart/form-data

参数:
- file: Word文档文件 (.docx 或 .doc)

返回:
{
  "success": true,
  "message": "文档处理完成",
  "output_filename": "filled_document.docx",
  "statistics": {
    "total_processed": 10,
    "successful_fills": 8,
    "success_rate": 0.8
  },
  "download_url": "/api/download/filled_document.docx"
}
```

### 2. 仅解析文档
```http
POST /api/parse
Content-Type: multipart/form-data

参数:
- file: Word文档文件

返回:
{
  "success": true,
  "empty_cells_count": 5,
  "empty_cells": [...],
  "message": "解析完成，发现 5 个空白单元格"
}
```

### 3. 数据填充
```http
POST /api/fill
Content-Type: application/json

{
  "cells": [
    {
      "row": 1,
      "col": 2,
      "content": "",
      "relationship": ["企业名称"]
    }
  ]
}

返回:
{
  "success": true,
  "filled_data": [...],
  "message": "数据填充完成"
}
```

### 4. 单个查询
```http
POST /api/query
Content-Type: application/json

{
  "keyword": "企业名称"
}

返回:
{
  "success": true,
  "keyword": "企业名称",
  "result": "爱士惟科技有限公司",
  "message": "查询完成"
}
```

### 5. 文件下载
```http
GET /api/download/{filename}

返回: 文件下载
```

### 6. 健康检查
```http
GET /api/health

返回:
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00",
  "version": "1.0.0"
}
```

## 📁 目录结构

```
src/backend/
├── app.py                 # Flask主应用
├── run.py                 # 启动脚本
├── requirements.txt       # Python依赖
├── README.md             # 说明文档
├── tools/                # 工具模块
│   ├── config.json       # 配置文件
│   ├── example_data.json # 示例数据
│   ├── intelligent_form_filler_api.py  # 智能填充API
│   ├── word_form_filler.py             # Word填充工具
│   └── word_parser.py                  # Word解析工具
├── uploads/              # 上传文件目录
└── outputs/              # 输出文件目录
```

## ⚙️ 配置说明

配置文件位于 `tools/config.json`，主要配置项：

- **data_source**: 数据源配置
- **matching**: 匹配算法配置
- **processing**: 处理策略配置
- **api**: 外部API配置（可选）

## 🔧 使用示例

### Web界面使用
1. 访问 http://localhost:5000
2. 选择Word文档文件
3. 点击"上传并处理"
4. 等待处理完成
5. 下载填充后的文档

### API使用示例 (Python)
```python
import requests

# 上传并处理文档
with open('document.docx', 'rb') as f:
    files = {'file': f}
    response = requests.post('http://localhost:5000/api/upload', files=files)
    result = response.json()
    
if result['success']:
    # 下载处理后的文档
    download_url = f"http://localhost:5000{result['download_url']}"
    doc_response = requests.get(download_url)
    
    with open('filled_document.docx', 'wb') as f:
        f.write(doc_response.content)
```

## 🛠️ 开发说明

### 添加新的匹配规则
在 `tools/config.json` 中的 `matching.synonyms` 部分添加同义词映射：

```json
{
  "matching": {
    "synonyms": {
      "新字段": ["同义词1", "同义词2"]
    }
  }
}
```

### 扩展示例数据
在 `tools/example_data.json` 中添加更多的示例数据：

```json
{
  "新字段名": "对应的值",
  "另一个字段": "另一个值"
}
```

## 📝 注意事项

1. **文件大小限制**: 最大支持16MB的文档文件
2. **文件格式**: 支持.docx和.doc格式（.doc需要安装pywin32）
3. **相对路径**: 所有路径都使用相对于项目根目录的相对路径
4. **临时文件**: 处理过程中的临时文件会自动清理
5. **日志记录**: 所有操作都会记录到app.log文件中

## 🐛 故障排除

### 常见问题

1. **导入错误**: 确保所有依赖都已正确安装
2. **文件权限**: 确保uploads和outputs目录有写入权限
3. **.doc转换失败**: 需要安装pywin32并确保在Windows环境下运行
4. **内存不足**: 处理大文档时可能需要增加内存限制

### 日志查看
```bash
# 查看应用日志
tail -f app.log

# 查看详细错误信息
python app.py
```

## 📄 许可证

本项目采用MIT许可证。