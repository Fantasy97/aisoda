# 综合信息查询系统 - 前端交互文档

## 项目概述

本项目是一个综合信息查询系统，包含企业信息搜索和历史数据管理功能。前端采用原生HTML/CSS/JavaScript开发，为后续迁移Vue做好准备。

## 页面结构

### 1. 主查询页面 (`index.html`)
- **功能**：企业信息搜索和结果展示
- **路径**：`/frontend/index.html`

### 2. 历史数据页面 (`history.html`)
- **功能**：历史文档管理和查看
- **路径**：`/frontend/history.html`

## 功能模块详解

### 主查询页面功能

#### 1.1 搜索功能
**当前状态**：✅ 使用模拟数据
**位置**：`js/app.js` - `handleSearch()` 方法

```javascript
// 当前模拟实现
handleSearch() {
    const query = searchInput.value.trim();
    // 模拟API调用
    setTimeout(() => {
        const results = this.performSearch(query);
        this.updateSearchInfo(results.length, randomTime);
    }, 800);
}
```

**需要后端接口**：
```
POST /api/search
Content-Type: application/json

Request Body:
{
    "query": "搜索关键词",
    "page": 1,
    "pageSize": 10
}

Response:
{
    "success": true,
    "data": {
        "results": [
            {
                "id": "企业ID",
                "name": "企业名称",
                "source": "数据来源",
                "type": "specialized|cultural"
            }
        ],
        "total": 总数量,
        "searchTime": 0.23
    }
}
```

#### 1.2 搜索结果展示
**当前状态**：✅ 使用模拟数据
**位置**：`js/app.js` - `getMockSearchResults()` 方法

**模拟数据结构**：
```javascript
const mockResults = [
    {
        name: '豪士博科技股份有限公司',
        source: '专精特新小巨人,建设信息',
        type: 'specialized'
    },
    {
        name: '豪士博科技股份有限公司(南京)',
        source: '市文创资金项目',
        type: 'cultural'
    }
];
```

#### 1.3 复制功能
**当前状态**：✅ 已完成，无需后端
**位置**：`js/app.js` - `copyCompanyName()` 方法

#### 1.4 快捷查询按钮
**当前状态**：✅ 前端完成，后端需要支持
**位置**：`js/app.js` - `handleQuickSearch()` 方法

**预设查询词**：
- 科技公司
- 有限公司  
- 股份公司
- 文创企业
- 专精特新
- 小巨人

### 历史数据页面功能

#### 2.1 文档卡片展示
**当前状态**：✅ 使用静态数据
**位置**：`history.html` - 静态HTML结构

**需要后端接口**：
```
GET /api/documents

Response:
{
    "success": true,
    "data": [
        {
            "id": "文档ID",
            "title": "文档标题",
            "type": "specialized|cultural",
            "uploadTime": "2024-06-02",
            "usageCount": 103000,
            "icon": "图标类型",
            "preview": "预览信息"
        }
    ]
}
```

#### 2.2 文档详情弹窗
**当前状态**：✅ 使用模拟数据
**位置**：`js/history.js` - `getSpecializedContent()` 和 `getCulturalContent()` 方法

**专精特新小巨人详情接口**：
```
GET /api/documents/{id}/specialized

Response:
{
    "success": true,
    "data": {
        "companyName": "企业名称",
        "registrationLocation": "注册地址",
        "employeeData": [
            {
                "year": "2021",
                "count": 151,
                "description": "2021年全职员工人数量"
            }
        ]
    }
}
```

**会议记录详情接口**：
```
GET /api/documents/{id}/meeting

Response:
{
    "success": true,
    "data": {
        "meetingInfo": {
            "title": "会议主题",
            "time": "会议时间",
            "location": "会议地点",
            "host": "主持人"
        },
        "agenda": ["议程项目1", "议程项目2"],
        "decisions": {
            "approvedProjects": 15,
            "totalAmount": "2,500万元",
            "nextMeetingTime": "2024-07-15"
        }
    }
}
```

#### 2.3 新建文档功能
**当前状态**：🚧 预留接口，待开发
**位置**：`js/history.js` - `addNewDocument()` 方法

**需要后端接口**：
```
POST /api/documents/create
Content-Type: application/json

Request Body:
{
    "title": "文档标题",
    "type": "document|meeting",
    "template": "模板类型"
}

Response:
{
    "success": true,
    "data": {
        "documentId": "新文档ID",
        "editUrl": "编辑页面URL"
    }
}
```

## 导航和路由

### 页面跳转
**当前实现**：使用 `window.location.href` 进行页面跳转

```javascript
// 主页 -> 历史数据页
onclick="window.location.href='history.html'"

// 历史数据页 -> 主页  
onclick="window.location.href='index.html'"
```

**建议**：后续可改为单页应用(SPA)路由

## 数据模拟详情

### 主查询页面模拟数据

#### 搜索结果模拟
**文件**：`js/app.js`
**方法**：`getMockSearchResults(query)`

```javascript
const companies = [
    {
        name: '豪士博科技股份有限公司',
        source: '专精特新小巨人,建设信息', 
        type: 'specialized'
    },
    {
        name: '豪士博科技股份有限公司(南京)',
        source: '市文创资金项目',
        type: 'cultural'  
    },
    // 动态生成更多结果...
];
```

#### 搜索统计模拟
```javascript
// 搜索时间：随机生成0.1-0.6秒
const searchTime = (Math.random() * 0.5 + 0.1).toFixed(2);

// 结果数量：基于模拟数据长度
const resultCount = mockResults.length;
```

### 历史数据页面模拟数据

#### 文档使用统计
**文件**：`history.html`
**位置**：静态HTML

```html
<!-- 业务经营周报 -->
<span class="usage-count">10.3 万人已使用</span>

<!-- 会议记录 -->  
<span class="usage-count">78.8 万人已使用</span>
```

#### 弹窗详情数据
**文件**：`js/history.js`

**专精特新详情**：
```javascript
getSpecializedContent() {
    return `
        企业名称: 豪士博科技股份有限公司
        注册地址: 上海市 市 市辖区 市（区） 黄浦区 县
        2021年员工: 151人
        2022年员工: 320人
    `;
}
```

**会议记录详情**：
```javascript  
getCulturalContent() {
    return `
        会议主题: 市文创资金项目评审会议
        会议时间: 2024年6月2日 14:00-16:00
        通过项目: 15个
        资助金额: 2,500万元
    `;
}
```

## 样式和交互

### CSS架构
```
frontend/css/
├── style.css      # 通用样式和主页样式
└── history.css    # 历史数据页面专用样式
```

### 响应式设计
- **桌面端**：≥1200px - 网格布局，最佳显示效果
- **平板端**：768px-1199px - 自适应网格，适当缩小
- **手机端**：≤767px - 单列布局，触摸优化

### 动画效果
- 卡片悬停：`transform: translateY(-2px)` + 阴影变化
- 弹窗显示：淡入 + 滑入动画
- 按钮交互：颜色渐变 + 轻微位移

## 技术栈

### 前端技术
- **HTML5**：语义化标签，无障碍支持
- **CSS3**：Grid布局，Flexbox，CSS变量
- **JavaScript ES6+**：类语法，箭头函数，模板字符串
- **SVG图标**：矢量图标，支持缩放

### 浏览器兼容性
- Chrome 60+
- Firefox 55+  
- Safari 12+
- Edge 79+

## Vue迁移准备

### 代码结构
已按Vue组件化思路组织：
```javascript
// 数据结构
const AppData = {
    searchQuery: '',
    searchResults: [],
    currentTab: 'contact',
    loading: false
};

// 方法结构  
const AppMethods = {
    handleSearch() { /* 搜索逻辑 */ },
    switchTab(tabName) { /* 切换逻辑 */ },
    showCompanyDetail(company) { /* 详情逻辑 */ }
};
```

### 组件划分建议
1. **SearchComponent** - 搜索功能
2. **ResultsComponent** - 结果展示  
3. **DocumentCardComponent** - 文档卡片
4. **ModalComponent** - 弹窗组件
5. **QuickSearchComponent** - 快捷查询

## 后端集成清单

### 必需接口

#### 搜索相关
- [ ] `POST /api/search` - 企业信息搜索
- [ ] `GET /api/search/suggestions` - 搜索建议（可选）

#### 文档管理  
- [ ] `GET /api/documents` - 获取文档列表
- [ ] `GET /api/documents/{id}` - 获取文档详情
- [ ] `POST /api/documents/create` - 创建新文档
- [ ] `PUT /api/documents/{id}` - 更新文档
- [ ] `DELETE /api/documents/{id}` - 删除文档

#### 统计数据
- [ ] `GET /api/statistics/usage` - 使用统计
- [ ] `GET /api/statistics/search` - 搜索统计

### 数据格式约定

#### 统一响应格式
```json
{
    "success": true|false,
    "message": "错误信息（可选）",
    "data": {}, 
    "timestamp": "2024-06-02T10:00:00Z"
}
```

#### 分页格式
```json
{
    "success": true,
    "data": {
        "items": [],
        "pagination": {
            "page": 1,
            "pageSize": 10, 
            "total": 100,
            "totalPages": 10
        }
    }
}
```

## 部署说明

### 静态资源
```
frontend/
├── index.html          # 主页
├── history.html        # 历史数据页
├── css/
│   ├── style.css      # 主样式
│   └── history.css    # 历史页样式
└── js/
    ├── app.js         # 主页逻辑
    └── history.js     # 历史页逻辑
```

### 服务器配置
- 支持HTML5 History API（如需SPA路由）
- 静态资源缓存策略
- GZIP压缩
- HTTPS支持

## 开发建议

### 接口开发优先级
1. **高优先级**：搜索接口、文档列表接口
2. **中优先级**：文档详情接口、统计接口  
3. **低优先级**：文档管理接口、高级功能

### 测试数据
建议后端提供测试数据集：
- 50+企业信息记录
- 10+历史文档记录
- 完整的企业详情数据
- 会议记录样本数据

### 错误处理
前端已预留错误处理机制，后端需要返回标准错误码：
- 200：成功
- 400：请求参数错误
- 401：未授权
- 404：资源不存在  
- 500：服务器内部错误

---

**文档版本**：v1.0  
**更新时间**：2024-06-02  
**维护人员**：前端开发团队