# SBOM管理系统

一个基于Flask和HTML的物料清单(BOM)管理系统，支持BOM数据转换、差异文件处理、BOM生成和对比分析功能。

## 功能特性

### 数据管理
- **BOM数据转换**: 将Excel格式的BOM数据转换为标准格式
- **差异文件处理**: 处理Excel格式的差异文件，转换为JSON格式
- **BOM生成**: 根据型号和产品编号生成BOM数据

### 对比分析
- **物料差异对比**: 对比两个BOM版本的差异
- **可视化显示**: 高亮显示数量差异的物料
- **Excel导出**: 下载生成的BOM Excel文件

## 项目结构

```
sbom_web/
├── src/
│   ├── backend/
│   │   ├── app.py              # Flask后端主程序
│   │   └── tools/              # 工具模块
│   │       ├── convert_bom.py  # BOM转换工具
│   │       ├── convert_diff.py # 差异文件处理工具
│   │       ├── create_bom.py   # BOM生成工具
│   │       └── format_bom.py   # BOM格式化工具
│   └── frontend/
│       └── index.html          # 前端界面
├── data/                       # 数据目录
│   ├── input/                  # 输入文件临时存储
│   ├── output/                 # 输出文件临时存储
│   └── processed/              # 处理后的数据
│       ├── bom/                # BOM数据
│       │   ├── TA/             # TA型号BOM
│       │   └── SP/             # SP型号BOM
│       └── diff/               # 差异数据
│           ├── TA/             # TA型号差异
│           └── SP/             # SP型号差异
└── README.md
```

## 安装和运行

### 环境要求
- Python 3.7+
- Flask
- pandas
- openpyxl
- flask-cors

### 安装依赖
```bash
pip install flask pandas openpyxl flask-cors
```

### 启动后端服务
```bash
cd src/backend
python app.py
```
服务将在 http://localhost:5000 启动

### 访问前端
在浏览器中打开 `src/frontend/index.html`

## API接口

### 数据管理接口
- `POST /convert_bom` - BOM数据转换
- `POST /convert_diff` - 差异文件处理  
- `POST /create_bom` - BOM生成
- `GET /get_product_codes` - 获取产品编号列表

### 对比分析接口
- `GET /get_bom_files` - 获取BOM文件列表
- `POST /compare_bom` - 对比BOM文件
- `POST /download_excel` - 下载Excel文件

## 使用说明

### 数据管理页签

1. **BOM数据转换**
   - 选择Excel文件(.xlsx/.xls)
   - 设置起始表索引(默认0)
   - 点击"转换BOM"

2. **差异文件处理**
   - 选择差异Excel文件
   - 点击"处理差异文件"

3. **BOM生成**
   - 选择型号(TA/SP)
   - 选择产品编号
   - 可选择生成JS数据格式
   - 点击"生成BOM"

### 对比分析页签

1. **物料差异对比**
   - 选择型号(TA/SP)
   - 选择基础版本JSON文件
   - 选择生成版本JSON文件
   - 点击"开始对比"查看差异
   - 点击"下载生成BOM"导出Excel

## 数据格式

### JSON数据结构
```json
{
  "category1": [
    {
      "MPART.NO": "物料编号",
      "MPART.NAME": "物料名称", 
      "MBOM.BNUM": "数量"
    }
  ]
}
```

### Excel输出格式
- 列A: MPART.NO (物料编号)
- 列B: MBOM.BNUM (数量)

## 注意事项

1. 支持的文件格式: .xlsx, .xls, .json
2. 临时文件会在处理完成后自动清理
3. 确保数据目录结构正确
4. 型号目前支持TA和SP两种

## 故障排除

### 常见问题
- **文件上传失败**: 检查文件格式和大小
- **JSON解析错误**: 确认服务器返回正确的JSON格式
- **文件不存在**: 检查数据目录结构和文件路径
- **权限错误**: 确保有足够的文件读写权限

### 日志查看
后端日志会显示在控制台，前端错误可通过浏览器开发者工具查看。