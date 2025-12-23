# 法律法规日期验证器 (EHS Law Date Validator)

一个用于验证法律法规施行日期准确性的Web API服务，支持单个验证、批量验证和全量验证。

## 功能特性

- **单个法律验证**: 验证单个法律法规的施行日期
- **批量验证**: 同时验证多个法律法规
- **全量验证**: 验证JSON文件中的所有法律法规
- **多数据源支持**: 
  - 官方数据库 (flk.npc.gov.cn)
  - SearXNG搜索引擎
  - ChatAPI智能查询
- **详细报告**: 生成HTML、JSON和文本格式的验证报告
- **RESTful API**: 提供标准的HTTP API接口

## 项目结构

```
├── src/                    # 源代码
│   ├── backend/           # 后端代码
│   │   ├── app.py        # Flask应用主文件
│   │   ├── config/       # 配置文件
│   │   └── tools/        # 核心工具模块
│   └── frontend/         # 前端代码（预留）
├── data/                 # 数据文件
│   ├── input/           # 输入数据
│   ├── output/          # 输出结果
│   └── processed/       # 缓存和日志
├── tests/               # 测试文件
├── requirements.txt     # Python依赖
├── run_server.py       # 启动脚本
└── test_api.py         # API测试脚本
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 启动服务

```bash
python src/backend/app.py
```

服务将在 http://localhost:5000 启动

### 3. 访问API

- 健康检查: http://localhost:5000/api/health
- 前端界面: 打开 `src/frontend/index.html` 文件

## API接口

### 健康检查
```
GET /api/health
```

### 单个法律验证
```
POST /api/validate/single
Content-Type: application/json

{
  "法律、法规、标准及其他要求": "中华人民共和国环境保护法",
  "施行（修改）日期": "2015-01-01",
  "获取途径": "国家法律法规数据库",
  "序号": "001",
  "category": "环境保护",
  "subcategory": "基础法律"
}
```

### 批量验证
```
POST /api/validate/batch
Content-Type: application/json

{
  "laws": [
    {
      "法律、法规、标准及其他要求": "法律名称1",
      "施行（修改）日期": "2015-01-01",
      "获取途径": "来源1"
    },
    {
      "法律、法规、标准及其他要求": "法律名称2",
      "施行（修改）日期": "2016-01-01",
      "获取途径": "来源2"
    }
  ]
}
```

### 全量验证
```
POST /api/validate/all
```

## 配置说明

项目使用 `src/backend/config/paths.py` 进行路径配置管理，支持：

- 自动创建必要的目录结构
- 统一的文件路径管理
- 跨平台兼容性

## 验证逻辑

1. **官方数据库来源**: 仅使用官方数据库查询，确保权威性
2. **其他来源**: 优先使用官方数据库，失败时使用SearXNG和ChatAPI备用
3. **日期匹配规则**: 
   - 精确匹配
   - 搜索日期早于或等于原始日期也视为匹配

## 输出文件

验证完成后会生成以下文件：
- `law_validation_results_[timestamp].json` - 详细验证结果
- `law_validation_report_[timestamp].txt` - 文本格式报告  
- `law_validation_report_[timestamp].html` - HTML格式报告
- `not_found_laws.json` - 未找到的法规列表

## 开发和测试

项目包含完整的测试脚本和启动检查，确保：
- 项目目录结构正确
- 外部服务连接正常
- API接口功能完整
