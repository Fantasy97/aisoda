# 桌宠Demo实现计划

## 项目概述
创建一个前端桌宠demo，展示4个核心功能模块，每个功能都是独立的交互式演示。

## 功能模块规划

### 1. 帮我联系 - 新建群组功能
**功能描述：** 类似微信的群组创建界面，用户可以创建新群组并添加成员

**实现要点：**
- 创建群组对话框/弹窗
- 群组名称输入
- 成员选择/添加功能
- 群组创建成功反馈
- 参考 `wechat-chat.html` 的样式风格

**技术实现：**
- HTML: 模态对话框结构
- CSS: 微信风格UI设计
- JavaScript: 表单处理、成员管理、创建逻辑

**文件：** `contact-group.html`, `contact-group.css`, `contact-group.js`

---

### 2. 给我总结 - 拖拽桌宠图标功能
**功能描述：** 可拖拽的桌宠图标，拖到指定位置后触发总结功能

**实现要点：**
- 可拖拽的桌宠图标（使用SVG或emoji）
- 拖拽交互（HTML5 Drag & Drop API）
- 目标区域高亮提示
- 拖拽到目标位置后的反馈动画
- 显示总结内容（可以是文本或卡片）

**技术实现：**
- HTML: 拖拽元素和目标区域
- CSS: 拖拽动画、目标区域样式
- JavaScript: 拖拽事件处理、位置检测、总结展示

**文件：** `drag-summary.html`, `drag-summary.css`, `drag-summary.js`

---

### 3. 教我做事 - 语音互动说明文档
**功能描述：** 语音交互式文档，可以语音提问和获取说明

**实现要点：**
- 语音输入按钮（Web Speech API）
- 语音识别和文本转换
- 文档内容展示区域
- 关键词匹配和内容检索
- 语音合成播放说明（TTS）
- 交互式文档导航

**技术实现：**
- HTML: 语音控制界面、文档展示区
- CSS: 语音波形动画、文档样式
- JavaScript: Web Speech API (SpeechRecognition, SpeechSynthesis)

**文件：** `voice-guide.html`, `voice-guide.css`, `voice-guide.js`

---

### 4. 替我干活 - 自动操作演示
**功能描述：** 自动变换鼠标指针并模拟界面操作

**实现要点：**
- 自动切换鼠标指针样式
- 模拟鼠标移动轨迹
- 自动点击按钮/元素
- 操作步骤可视化展示
- 操作日志/步骤说明

**技术实现：**
- HTML: 操作演示区域、控制按钮
- CSS: 指针样式、操作动画
- JavaScript: 指针切换、鼠标模拟、操作序列

**文件：** `auto-work.html`, `auto-work.css`, `auto-work.js`

---

## 主入口页面

创建一个主页面整合所有4个功能模块：

**文件：** `desktop-pet-demo.html`, `desktop-pet-demo.css`, `desktop-pet-demo.js`

**布局设计：**
- 顶部标题和说明
- 4个功能卡片，每个卡片可点击进入对应功能
- 统一的导航和返回按钮
- 统一的视觉风格

---

## 技术栈
- HTML5
- CSS3 (动画、渐变、毛玻璃效果)
- Vanilla JavaScript (ES6+)
- Web APIs:
  - Drag & Drop API
  - Web Speech API (SpeechRecognition, SpeechSynthesis)
  - 鼠标事件模拟

## 文件结构
```
front/
├── desktop-pet-demo.html          # 主入口页面
├── desktop-pet-demo.css           # 主页面样式
├── desktop-pet-demo.js            # 主页面逻辑
├── contact-group.html             # 功能1: 新建群组
├── contact-group.css
├── contact-group.js
├── drag-summary.html              # 功能2: 拖拽总结
├── drag-summary.css
├── drag-summary.js
├── voice-guide.html               # 功能3: 语音互动
├── voice-guide.css
├── voice-guide.js
├── auto-work.html                 # 功能4: 自动操作
├── auto-work.css
└── auto-work.js
```

## 开发顺序
1. 创建主入口页面框架
2. 实现功能1: 新建群组
3. 实现功能2: 拖拽总结
4. 实现功能3: 语音互动
5. 实现功能4: 自动操作
6. 整合和优化

## UI设计风格
- 参考现有 `cursor-changer.html` 的渐变背景和卡片设计
- 参考 `wechat-chat.html` 的聊天界面风格
- 统一使用现代化的毛玻璃效果（backdrop-filter）
- 统一的动画过渡效果
- 响应式设计，适配不同屏幕

