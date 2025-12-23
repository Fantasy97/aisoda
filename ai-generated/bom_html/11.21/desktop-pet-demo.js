// 功能页面映射
const featurePages = {
    'contact': 'contact-group.html',
    'summary': 'drag-summary.html',
    'guide': 'voice-guide.html',
    'work': 'auto-work.html'
};

// 功能名称映射
const featureNames = {
    'contact': '帮我联系',
    'summary': '给我总结',
    'guide': '教我做事',
    'work': '替我干活'
};

// DOM元素
let petIcon, petContainer, featuresContainer, closeBtn, petHint, mainContainer, canvasContainer;
let isExpanded = false;
let floatingWindowsContainer;
let windowZIndex = 1000;

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    petIcon = document.getElementById('petIcon');
    petContainer = document.getElementById('petContainer');
    featuresContainer = document.getElementById('featuresContainer');
    closeBtn = document.getElementById('closeBtn');
    petHint = document.getElementById('petHint');
    floatingWindowsContainer = document.getElementById('floatingWindowsContainer');
    mainContainer = document.querySelector('.container');
    canvasContainer = document.getElementById('canvasContainer');

    // 桌宠图标点击事件
    petIcon.addEventListener('click', toggleFeatures);
    petIcon.addEventListener('touchstart', toggleFeatures);

    // 关闭按钮点击事件
    closeBtn.addEventListener('click', closeFeatures);

    // 功能按钮点击事件
    const featureButtons = document.querySelectorAll('.feature-btn');
    featureButtons.forEach(btn => {
        const feature = btn.getAttribute('data-feature');
        
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            // 创建悬浮窗口而不是跳转页面
            createFloatingWindow(feature, btn);
        });

        // 键盘支持
        btn.setAttribute('tabindex', '0');
        btn.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                e.stopPropagation();
                createFloatingWindow(feature, btn);
            }
        });
    });

    // 点击外部区域关闭功能菜单
    document.addEventListener('click', (e) => {
        if (isExpanded && !featuresContainer.contains(e.target) && !petIcon.contains(e.target)) {
            closeFeatures();
        }
    });

    // ESC键关闭
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && isExpanded) {
            closeFeatures();
        }
    });
});

// 切换功能菜单显示/隐藏
function toggleFeatures() {
    if (isExpanded) {
        closeFeatures();
    } else {
        openFeatures();
    }
}

// 打开功能菜单
function openFeatures() {
    isExpanded = true;
    petContainer.classList.add('expanded');
    featuresContainer.classList.add('active');
    closeBtn.style.display = 'flex';
    petHint.style.opacity = '0';
    
    // 添加展开动画
    petIcon.style.animation = 'none';
    setTimeout(() => {
        petIcon.style.animation = 'float 3s ease-in-out infinite';
    }, 100);
}

// 关闭功能菜单
function closeFeatures() {
    isExpanded = false;
    petContainer.classList.remove('expanded');
    featuresContainer.classList.remove('active');
    closeBtn.style.display = 'none';
    petHint.style.opacity = '1';
}

// 创建悬浮窗口
function createFloatingWindow(feature, button) {
    const featureName = featureNames[feature];
    const featureIcon = button.querySelector('.btn-icon').textContent;
    
    // 创建窗口元素
    const window = document.createElement('div');
    window.className = 'floating-window';
    window.style.zIndex = windowZIndex++;
    
    // 计算窗口初始位置（优先在画布区域左上角）
    const windowWidth = 500;
    const windowHeight = 300;
    const padding = 20;
    
    // 优先位置：画布区域的左上角
    let left = padding;
    let top = padding;
    
    // 检查是否有其他窗口，如果有则错开位置
    const existingWindows = canvasContainer.querySelectorAll('.floating-window');
    if (existingWindows.length > 0) {
        // 计算偏移量，让新窗口稍微错开
        const offset = (existingWindows.length % 3) * 30; // 最多3个窗口错开
        left = padding + offset;
        top = padding + offset;
    }
    
    // 确保窗口不超出画布区域
    const canvasRect = canvasContainer.getBoundingClientRect();
    const maxLeft = canvasRect.width - windowWidth - padding;
    const maxTop = canvasRect.height - windowHeight - padding;
    
    left = Math.max(padding, Math.min(left, maxLeft));
    top = Math.max(padding, Math.min(top, maxTop));
    
    window.style.left = left + 'px';
    window.style.top = top + 'px';
    
    // 窗口内容
    const content = getWindowContent(feature);
    
    // 判断是否是聊天窗口
    const isChatWindow = feature === 'contact';
    const contentClass = isChatWindow ? 'chat-window' : '';
    
    window.innerHTML = `
        <div class="window-header">
            <div class="window-title">
                <span class="window-title-icon">${featureIcon}</span>
                <span>${featureName}</span>
            </div>
            <button class="window-close" aria-label="关闭">×</button>
        </div>
        <div class="window-content ${contentClass}">
            ${content}
        </div>
    `;
    
    // 添加到画布容器
    canvasContainer.appendChild(window);
    
    // 如果是聊天窗口，初始化聊天功能
    if (isChatWindow) {
        initChatWindow(window);
    }
    
    // 如果是鼠标指针窗口，初始化指针功能
    if (feature === 'work') {
        const cursorWindow = initCursorWindow(window);
        // 保存窗口引用以便关闭时清理
        window._cursorWindow = cursorWindow;
    }
    
    // 如果是总结窗口，初始化拖拽功能
    if (feature === 'summary') {
        initSummaryWindow(window);
    }
    
    // 如果是语音指导窗口，初始化语音功能
    if (feature === 'guide') {
        initVoiceGuideWindow(window);
    }
    
    // 实现拖动功能
    makeWindowDraggable(window);
    
    // 关闭按钮事件
    const closeBtn = window.querySelector('.window-close');
    closeBtn.addEventListener('click', () => {
        closeWindow(window);
    });
    
    // 点击窗口时提升层级
    window.addEventListener('mousedown', () => {
        window.style.zIndex = windowZIndex++;
    });
    
    // 添加出现动画
    setTimeout(() => {
        window.style.opacity = '1';
    }, 10);
}

// 获取窗口内容
function getWindowContent(feature) {
    const contents = {
        'contact': `
            <div class="chat-container">
                <div class="chat-header">
                    <div>
                        <div class="group-name">技术交流群</div>
                        <div class="member-count">(5)</div>
                    </div>
                    <div class="more-btn">⋯</div>
                </div>

                <div class="chat-messages" id="chatMessages">
                    <div class="system-message">今天</div>

                    <div class="message message-left">
                        <div class="avatar" style="background-color: #07c160;">张</div>
                        <div class="message-content">
                            <div class="username">张三</div>
                            <div class="bubble">大家好,最近在研究前端框架</div>
                        </div>
                    </div>

                    <div class="message message-left">
                        <div class="avatar" style="background-color: #1989fa;">李</div>
                        <div class="message-content">
                            <div class="username">李四</div>
                            <div class="bubble">Vue和React你更推荐哪个?</div>
                        </div>
                    </div>

                    <div class="message message-right">
                        <div class="avatar" style="background-color: #ff976a;">我</div>
                        <div class="message-content">
                            <div class="username">我</div>
                            <div class="bubble">这个要看具体项目需求,两个都很好用</div>
                        </div>
                    </div>

                    <div class="message message-left">
                        <div class="avatar" style="background-color: #f56c6c;">王</div>
                        <div class="message-content">
                            <div class="username">王五</div>
                            <div class="bubble">我们公司用的是Vue,感觉上手比较快</div>
                        </div>
                    </div>

                    <div class="message message-left">
                        <div class="avatar" style="background-color: #e6a23c;">赵</div>
                        <div class="message-content">
                            <div class="username">赵六</div>
                            <div class="bubble">最近React Hooks用的很爽😄</div>
                        </div>
                    </div>

                    <div class="message message-right">
                        <div class="avatar" style="background-color: #ff976a;">我</div>
                        <div class="message-content">
                            <div class="username">我</div>
                            <div class="bubble">Vue 3的Composition API也很强大</div>
                        </div>
                    </div>

                    <div class="system-message">以下为新消息</div>

                    <div class="message message-left">
                        <div class="avatar" style="background-color: #07c160;">张</div>
                        <div class="message-content">
                            <div class="username">张三</div>
                            <div class="bubble">看来我要好好学习一下了👍</div>
                        </div>
                    </div>
                </div>

                <div class="chat-input">
                    <input type="text" class="input-box" placeholder="请输入消息...">
                    <button class="send-btn">发送</button>
                </div>
            </div>
        `,
        'summary': `
            <div class="summary-container">
                <h3 style="margin-top: 0; color: #667eea; text-align: center;">内容总结</h3>
                <p style="text-align: center; color: #666; margin-bottom: 30px;">拖拽桌宠图标到总结区域，即可获取内容总结</p>
                
                <!-- 可拖拽的桌宠图标 -->
                <div class="draggable-pet" id="draggablePet" draggable="true">
                    <img src="桌宠图标1.png" alt="桌宠" style="width: 80px; height: 80px; object-fit: contain;">
                    <div class="pet-label">拖拽我</div>
                </div>
                
                <!-- 总结目标区域 -->
                <div class="summary-target" id="summaryTarget">
                    <div class="target-placeholder">
                        <div class="target-icon">📋</div>
                        <div class="target-text">拖拽桌宠到这里</div>
                    </div>
                    <div class="summary-result" id="summaryResult" style="display: none;">
                        <h4>内容总结</h4>
                        <div class="summary-content" id="summaryContent"></div>
                    </div>
                </div>
            </div>
        `,
        'guide': `
            <div class="voice-guide-container">
                <h3 style="margin-top: 0; color: #667eea; text-align: center;">语音互动</h3>
                <p style="text-align: center; color: #666; margin-bottom: 30px;">点击麦克风按钮，说出您的问题</p>
                
                <!-- 语音输入区域 -->
                <div class="voice-input-area">
                    <div class="voice-wave-container" id="voiceWaveContainer">
                        <div class="wave-bar"></div>
                        <div class="wave-bar"></div>
                        <div class="wave-bar"></div>
                        <div class="wave-bar"></div>
                        <div class="wave-bar"></div>
                        <div class="wave-bar"></div>
                        <div class="wave-bar"></div>
                        <div class="wave-bar"></div>
                        <div class="wave-bar"></div>
                        <div class="wave-bar"></div>
                    </div>
                    
                    <button class="voice-btn" id="voiceBtn">
                        <div class="mic-icon">🎤</div>
                        <span class="voice-btn-text">点击开始语音输入</span>
                    </button>
                    
                    <div class="voice-status" id="voiceStatus">准备就绪</div>
                </div>
                
                <!-- 语音识别结果 -->
                <div class="voice-result" id="voiceResult" style="display: none;">
                    <div class="result-header">
                        <span class="result-label">识别结果：</span>
                    </div>
                    <div class="result-text" id="resultText"></div>
                </div>
                
                <!-- 说明文档区域 -->
                <div class="guide-docs" id="guideDocs" style="display: none;">
                    <h4>操作说明</h4>
                    <div class="docs-content" id="docsContent"></div>
                </div>
            </div>
        `,
        'work': `
            <div class="cursor-demo-container">
                <div class="demo-area" id="demoArea">
                    <p>在此区域移动鼠标查看效果</p>
                    <div class="demo-icon">👆</div>
                </div>
                
                <div class="current-cursor">
                    当前指针: <span id="cursorName">默认</span>
                </div>
                
                <div class="cursor-control">
                    <button class="cursor-select-btn" id="cursorSelectBtn">
                        <span>选择鼠标类型</span>
                        <span class="dropdown-arrow">▼</span>
                    </button>
                    <div class="cursor-dropdown" id="cursorDropdown">
                        <div class="dropdown-item" data-cursor="default">默认</div>
                        <div class="dropdown-item" data-cursor="pointer">手指</div>
                        <div class="dropdown-item" data-cursor="text">文本</div>
                        <div class="dropdown-item" data-cursor="move">移动</div>
                        <div class="dropdown-item" data-cursor="crosshair">十字</div>
                        <div class="dropdown-item" data-cursor="wait">等待</div>
                        <div class="dropdown-item" data-cursor="help">帮助</div>
                        <div class="dropdown-item" data-cursor="not-allowed">禁止</div>
                        <div class="dropdown-item" data-cursor="grab">抓取</div>
                        <div class="dropdown-item" data-cursor="grabbing">抓住</div>
                        <div class="dropdown-item" data-cursor="zoom-in">放大</div>
                        <div class="dropdown-item" data-cursor="zoom-out">缩小</div>
                        <div class="dropdown-item" data-cursor="n-resize">上调整</div>
                        <div class="dropdown-item" data-cursor="s-resize">下调整</div>
                        <div class="dropdown-item" data-cursor="e-resize">右调整</div>
                        <div class="dropdown-item" data-cursor="w-resize">左调整</div>
                        <div class="dropdown-item" data-cursor="ne-resize">右上调整</div>
                        <div class="dropdown-item" data-cursor="nw-resize">左上调整</div>
                        <div class="dropdown-item" data-cursor="se-resize">右下调整</div>
                        <div class="dropdown-item" data-cursor="sw-resize">左下调整</div>
                        <div class="dropdown-item" data-cursor="ew-resize">横向调整</div>
                        <div class="dropdown-item" data-cursor="ns-resize">纵向调整</div>
                        <div class="dropdown-item" data-cursor="nesw-resize">对角调整1</div>
                        <div class="dropdown-item" data-cursor="nwse-resize">对角调整2</div>
                        <div class="dropdown-item" data-cursor="progress">进度</div>
                        <div class="dropdown-item" data-cursor="cell">单元格</div>
                        <div class="dropdown-item" data-cursor="context-menu">菜单</div>
                        <div class="dropdown-item" data-cursor="copy">复制</div>
                        <div class="dropdown-item" data-cursor="alias">别名</div>
                        <div class="dropdown-item" data-cursor="none">隐藏</div>
                    </div>
                </div>
            </div>
        `
    };
    
    return contents[feature] || '<p>功能内容加载中...</p>';
}

// 使窗口可拖动
function makeWindowDraggable(window) {
    const header = window.querySelector('.window-header');
    let isDragging = false;
    let startX, startY, initialX, initialY;
    
    header.addEventListener('mousedown', dragStart);
    document.addEventListener('mousemove', drag);
    document.addEventListener('mouseup', dragEnd);
    
    function dragStart(e) {
        if (e.target.classList.contains('window-close')) {
            return;
        }
        
        // 获取窗口当前位置（相对于画布的left和top）
        initialX = parseInt(window.style.left) || 0;
        initialY = parseInt(window.style.top) || 0;
        
        // 获取鼠标位置
        startX = e.clientX;
        startY = e.clientY;
        
        if (e.target === header || header.contains(e.target)) {
            isDragging = true;
            window.classList.add('dragging');
            e.preventDefault();
        }
    }
    
    function drag(e) {
        if (isDragging) {
            e.preventDefault();
            
            // 计算鼠标移动的距离
            const deltaX = e.clientX - startX;
            const deltaY = e.clientY - startY;
            
            // 计算新位置（相对于画布）
            let newX = initialX + deltaX;
            let newY = initialY + deltaY;
            
            // 限制窗口不超出画布区域
            const canvasRect = canvasContainer.getBoundingClientRect();
            const windowRect = window.getBoundingClientRect();
            const padding = 0;
            
            const maxX = canvasRect.width - windowRect.width - padding;
            const maxY = canvasRect.height - windowRect.height - padding;
            
            newX = Math.max(padding, Math.min(newX, maxX));
            newY = Math.max(padding, Math.min(newY, maxY));
            
            window.style.left = newX + 'px';
            window.style.top = newY + 'px';
        }
    }
    
    function dragEnd(e) {
        if (isDragging) {
            isDragging = false;
            window.classList.remove('dragging');
        }
    }
}

// 初始化聊天窗口功能
function initChatWindow(window) {
    const chatMessages = window.querySelector('.chat-messages');
    const messageInput = window.querySelector('.input-box');
    const sendBtn = window.querySelector('.send-btn');
    
    if (!chatMessages || !messageInput || !sendBtn) return;
    
    // 自动滚动到底部
    function scrollToBottom() {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    // 发送消息
    function sendMessage() {
        const text = messageInput.value.trim();
        if (!text) return;

        const messageDiv = document.createElement('div');
        messageDiv.className = 'message message-right';
        messageDiv.innerHTML = `
            <div class="avatar" style="background-color: #ff976a;">我</div>
            <div class="message-content">
                <div class="username">我</div>
                <div class="bubble">${text}</div>
            </div>
        `;

        chatMessages.appendChild(messageDiv);
        messageInput.value = '';
        scrollToBottom();

        // 模拟其他人回复
        setTimeout(() => {
            simulateReply(window);
        }, 1000 + Math.random() * 2000);
    }
    
    // 模拟回复
    function simulateReply(window) {
        const chatMessages = window.querySelector('.chat-messages');
        if (!chatMessages) return;
        
        const users = [
            { name: '张三', initial: '张', color: '#07c160' },
            { name: '李四', initial: '李', color: '#1989fa' },
            { name: '王五', initial: '王', color: '#f56c6c' },
            { name: '赵六', initial: '赵', color: '#e6a23c' }
        ];

        const replies = [
            '说得对👍',
            '我也这么认为',
            '学到了',
            '有道理',
            '感谢分享!',
            '👌',
            '确实如此',
            '赞同',
            '收藏了',
            '很有帮助'
        ];

        const randomUser = users[Math.floor(Math.random() * users.length)];
        const randomReply = replies[Math.floor(Math.random() * replies.length)];

        const messageDiv = document.createElement('div');
        messageDiv.className = 'message message-left';
        messageDiv.innerHTML = `
            <div class="avatar" style="background-color: ${randomUser.color};">${randomUser.initial}</div>
            <div class="message-content">
                <div class="username">${randomUser.name}</div>
                <div class="bubble">${randomReply}</div>
            </div>
        `;

        chatMessages.appendChild(messageDiv);
        scrollToBottom();
    }
    
    // 事件监听
    sendBtn.addEventListener('click', sendMessage);
    messageInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
    
    // 初始化时滚动到底部
    setTimeout(() => {
        scrollToBottom();
    }, 100);
}

// 初始化鼠标指针窗口功能
function initCursorWindow(window) {
    const demoArea = window.querySelector('#demoArea');
    const cursorName = window.querySelector('#cursorName');
    const selectBtn = window.querySelector('#cursorSelectBtn');
    const dropdown = window.querySelector('#cursorDropdown');
    const dropdownItems = window.querySelectorAll('.dropdown-item');
    
    if (!demoArea || !cursorName || !selectBtn || !dropdown) return;
    
    // 创建跟随鼠标的 SVG 指针
    const customCursor = document.createElement('div');
    customCursor.className = 'custom-cursor';
    customCursor.id = 'customCursor';
    customCursor.style.display = 'none';
    document.body.appendChild(customCursor);
    
    // 鼠标类型到 SVG 文件的映射
    const cursorSvgMap = {
        'default': 'tmp/准星.svg',
        'pointer': 'tmp/告警监测.svg',
        'text': 'tmp/智能抓包.svg',
        'move': 'tmp/机械.svg',
        'crosshair': 'tmp/准星.svg',
        'wait': 'tmp/雷达.svg',
        'help': 'tmp/大脑,研判,智慧,思考,联想.svg',
        'not-allowed': 'tmp/告警监测.svg',
        'grab': 'tmp/装备制造.svg',
        'grabbing': 'tmp/装备制造.svg',
        'zoom-in': 'tmp/卫星信号.svg',
        'zoom-out': 'tmp/卫星信号.svg',
        'n-resize': 'tmp/插头.svg',
        's-resize': 'tmp/插头.svg',
        'e-resize': 'tmp/插头.svg',
        'w-resize': 'tmp/插头.svg',
        'ne-resize': 'tmp/插头.svg',
        'nw-resize': 'tmp/插头.svg',
        'se-resize': 'tmp/插头.svg',
        'sw-resize': 'tmp/插头.svg',
        'ew-resize': 'tmp/插头.svg',
        'ns-resize': 'tmp/插头.svg',
        'nesw-resize': 'tmp/插头.svg',
        'nwse-resize': 'tmp/插头.svg',
        'progress': 'tmp/雷达.svg',
        'cell': 'tmp/智能抓包.svg',
        'context-menu': 'tmp/脑,思考,大脑,思维.svg',
        'copy': 'tmp/智能抓包.svg',
        'alias': 'tmp/卫星信号.svg',
        'none': ''
    };
    
    // 中文名称映射
    const cursorNames = {
        'default': '默认',
        'pointer': '手指',
        'text': '文本',
        'move': '移动',
        'crosshair': '十字',
        'wait': '等待',
        'help': '帮助',
        'not-allowed': '禁止',
        'grab': '抓取',
        'grabbing': '抓住',
        'zoom-in': '放大',
        'zoom-out': '缩小',
        'n-resize': '上调整',
        's-resize': '下调整',
        'e-resize': '右调整',
        'w-resize': '左调整',
        'ne-resize': '右上调整',
        'nw-resize': '左上调整',
        'se-resize': '右下调整',
        'sw-resize': '左下调整',
        'ew-resize': '横向调整',
        'ns-resize': '纵向调整',
        'nesw-resize': '对角调整1',
        'nwse-resize': '对角调整2',
        'progress': '进度',
        'cell': '单元格',
        'context-menu': '菜单',
        'copy': '复制',
        'alias': '别名',
        'none': '隐藏'
    };
    
    let currentCursor = 'default';
    
    // 更新自定义指针 SVG
    function updateCustomCursor(cursorType) {
        const svgPath = cursorSvgMap[cursorType];
        if (svgPath && svgPath !== '' && cursorType !== 'none') {
            customCursor.innerHTML = `<img src="${svgPath}" alt="cursor" style="width: 40px; height: 40px; pointer-events: none;">`;
            customCursor.style.display = 'block';
        } else {
            customCursor.style.display = 'none';
            // 如果选择隐藏，恢复默认指针
            if (cursorType === 'none') {
                document.body.style.cursor = 'default';
            }
        }
    }
    
    // 切换指针样式
    function changeCursor(cursorType) {
        // 隐藏默认指针，使用自定义指针
        document.body.style.cursor = 'none';
        cursorName.textContent = cursorNames[cursorType] || cursorType;
        currentCursor = cursorType;
        
        // 更新自定义指针
        updateCustomCursor(cursorType);
        
        // 更新下拉框选中状态
        dropdownItems.forEach(item => {
            item.classList.remove('selected');
            if (item.getAttribute('data-cursor') === cursorType) {
                item.classList.add('selected');
            }
        });
        
        // 更新按钮文本
        const btnText = selectBtn.querySelector('span:first-child');
        if (btnText) {
            btnText.textContent = cursorNames[cursorType] || cursorType;
        }
        
        // 添加切换动画
        demoArea.style.transform = 'scale(0.98)';
        setTimeout(() => {
            demoArea.style.transform = 'scale(1)';
        }, 100);
    }
    
    // 鼠标移动事件 - 更新自定义指针位置（全局跟随）
    function updateCursorPosition(e) {
        customCursor.style.left = e.clientX + 'px';
        customCursor.style.top = e.clientY + 'px';
    }
    
    // 全局鼠标移动事件
    const mouseMoveHandler = (e) => {
        updateCursorPosition(e);
    };
    
    document.addEventListener('mousemove', mouseMoveHandler);
    
    // 保存清理函数到窗口元素，以便关闭时调用
    window._cleanupCursor = () => {
        document.removeEventListener('mousemove', mouseMoveHandler);
        document.body.style.cursor = '';
        if (customCursor && customCursor.parentNode) {
            customCursor.remove();
        }
    };
    
    // 切换下拉框显示/隐藏
    selectBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        dropdown.classList.toggle('show');
    });
    
    // 点击下拉项
    dropdownItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.stopPropagation();
            const cursorType = item.getAttribute('data-cursor');
            changeCursor(cursorType);
            dropdown.classList.remove('show');
        });
    });
    
    // 点击外部关闭下拉框
    document.addEventListener('click', (e) => {
        if (!selectBtn.contains(e.target) && !dropdown.contains(e.target)) {
            dropdown.classList.remove('show');
        }
    });
    
    // 初始化默认指针
    changeCursor('default');
    
    // 返回窗口元素引用，用于清理
    return window;
}

// 初始化总结窗口功能
function initSummaryWindow(window) {
    const draggablePet = window.querySelector('#draggablePet');
    const summaryTarget = window.querySelector('#summaryTarget');
    const summaryResult = window.querySelector('#summaryResult');
    const summaryContent = window.querySelector('#summaryContent');
    const targetPlaceholder = window.querySelector('.target-placeholder');
    
    if (!draggablePet || !summaryTarget) return;
    
    let isDragging = false;
    let dragOffsetX = 0;
    let dragOffsetY = 0;
    
    // 鼠标按下 - 开始拖拽
    draggablePet.addEventListener('mousedown', (e) => {
        isDragging = true;
        const rect = draggablePet.getBoundingClientRect();
        dragOffsetX = e.clientX - rect.left;
        dragOffsetY = e.clientY - rect.top;
        draggablePet.style.opacity = '0.7';
        draggablePet.style.cursor = 'grabbing';
        e.preventDefault();
    });
    
    // 鼠标移动 - 更新位置
    const mouseMoveHandler = (e) => {
        if (!isDragging) return;
        
        const windowRect = window.getBoundingClientRect();
        const petWidth = draggablePet.offsetWidth;
        const petHeight = draggablePet.offsetHeight;
        
        // 计算新位置（相对于窗口）
        let newX = e.clientX - windowRect.left - dragOffsetX;
        let newY = e.clientY - windowRect.top - dragOffsetY;
        
        // 限制在窗口内
        const maxX = windowRect.width - petWidth;
        const maxY = windowRect.height - petHeight - 60; // 减去标题栏高度
        
        newX = Math.max(0, Math.min(newX, maxX));
        newY = Math.max(0, Math.min(newY, maxY));
        
        draggablePet.style.left = newX + 'px';
        draggablePet.style.top = newY + 'px';
        draggablePet.style.position = 'absolute';
        
        // 检查是否在目标区域上方
        const petRect = draggablePet.getBoundingClientRect();
        const targetRect = summaryTarget.getBoundingClientRect();
        
        const isOverTarget = petRect.left < targetRect.right &&
                            petRect.right > targetRect.left &&
                            petRect.top < targetRect.bottom &&
                            petRect.bottom > targetRect.top;
        
        if (isOverTarget) {
            summaryTarget.classList.add('drag-over');
        } else {
            summaryTarget.classList.remove('drag-over');
        }
    };
    
    document.addEventListener('mousemove', mouseMoveHandler);
    
    // 鼠标释放 - 结束拖拽
    const mouseUpHandler = (e) => {
        if (!isDragging) return;
        
        isDragging = false;
        draggablePet.style.opacity = '1';
        draggablePet.style.cursor = 'grab';
        summaryTarget.classList.remove('drag-over');
        
        // 检查是否拖到目标区域
        const petRect = draggablePet.getBoundingClientRect();
        const targetRect = summaryTarget.getBoundingClientRect();
        
        // 计算重叠区域
        const overlapX = Math.max(0, Math.min(petRect.right, targetRect.right) - Math.max(petRect.left, targetRect.left));
        const overlapY = Math.max(0, Math.min(petRect.bottom, targetRect.bottom) - Math.max(petRect.top, targetRect.top));
        const overlapArea = overlapX * overlapY;
        const petArea = petRect.width * petRect.height;
        
        // 如果重叠面积超过50%，触发总结
        if (overlapArea / petArea > 0.5) {
            showSummary(window);
        }
    };
    
    document.addEventListener('mouseup', mouseUpHandler);
    
    // 保存清理函数
    window._cleanupSummary = () => {
        document.removeEventListener('mousemove', mouseMoveHandler);
        document.removeEventListener('mouseup', mouseUpHandler);
    };
    
    // 显示总结内容
    function showSummary(window) {
        // 隐藏占位符
        targetPlaceholder.style.display = 'none';
        
        // 显示总结结果
        summaryResult.style.display = 'block';
        
        // 生成总结内容（示例）
        const summaryText = `
            <div class="summary-item">
                <strong>📊 数据概览</strong>
                <p>本次分析共处理了 1,234 条数据记录，涵盖了多个维度的信息。</p>
            </div>
            <div class="summary-item">
                <strong>🎯 关键发现</strong>
                <p>发现了 3 个主要趋势和 5 个需要关注的问题点。</p>
            </div>
            <div class="summary-item">
                <strong>💡 建议</strong>
                <p>建议优先处理高优先级问题，并持续监控数据变化。</p>
            </div>
        `;
        
        summaryContent.innerHTML = summaryText;
        
        // 添加动画效果
        summaryResult.style.opacity = '0';
        summaryResult.style.transform = 'translateY(20px)';
        setTimeout(() => {
            summaryResult.style.transition = 'all 0.3s ease';
            summaryResult.style.opacity = '1';
            summaryResult.style.transform = 'translateY(0)';
        }, 10);
        
        // 重置桌宠位置（可选）
        setTimeout(() => {
            draggablePet.style.position = 'relative';
            draggablePet.style.left = '';
            draggablePet.style.top = '';
        }, 500);
    }
}

// 初始化语音指导窗口功能
function initVoiceGuideWindow(window) {
    const voiceBtn = window.querySelector('#voiceBtn');
    const voiceWaveContainer = window.querySelector('#voiceWaveContainer');
    const voiceStatus = window.querySelector('#voiceStatus');
    const voiceResult = window.querySelector('#voiceResult');
    const resultText = window.querySelector('#resultText');
    const guideDocs = window.querySelector('#guideDocs');
    const docsContent = window.querySelector('#docsContent');
    
    if (!voiceBtn || !voiceWaveContainer) return;
    
    let isRecording = false;
    let recognition = null;
    
    // 检查浏览器是否支持语音识别
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    
    if (SpeechRecognition) {
        recognition = new SpeechRecognition();
        recognition.lang = 'zh-CN';
        recognition.continuous = false;
        recognition.interimResults = true;
        
        recognition.onstart = () => {
            isRecording = true;
            voiceBtn.classList.add('recording');
            voiceWaveContainer.classList.add('active');
            voiceStatus.textContent = '正在聆听...';
            voiceStatus.style.color = '#667eea';
        };
        
        recognition.onresult = (event) => {
            let interimTranscript = '';
            let finalTranscript = '';
            
            for (let i = event.resultIndex; i < event.results.length; i++) {
                const transcript = event.results[i][0].transcript;
                if (event.results[i].isFinal) {
                    finalTranscript += transcript;
                } else {
                    interimTranscript += transcript;
                }
            }
            
            if (finalTranscript) {
                resultText.textContent = finalTranscript;
                voiceResult.style.display = 'block';
                showGuideDocs(finalTranscript, window);
            } else if (interimTranscript) {
                resultText.textContent = interimTranscript;
                voiceResult.style.display = 'block';
            }
        };
        
        recognition.onerror = (event) => {
            console.error('语音识别错误:', event.error);
            stopRecording();
            voiceStatus.textContent = '识别出错，请重试';
            voiceStatus.style.color = '#f56c6c';
        };
        
        recognition.onend = () => {
            stopRecording();
        };
    } else {
        voiceStatus.textContent = '您的浏览器不支持语音识别';
        voiceStatus.style.color = '#f56c6c';
        voiceBtn.disabled = true;
    }
    
    // 开始/停止录音
    voiceBtn.addEventListener('click', () => {
        if (!recognition) return;
        
        if (!isRecording) {
            try {
                recognition.start();
            } catch (e) {
                console.error('启动语音识别失败:', e);
            }
        } else {
            recognition.stop();
        }
    });
    
    // 停止录音
    function stopRecording() {
        isRecording = false;
        voiceBtn.classList.remove('recording');
        voiceWaveContainer.classList.remove('active');
        voiceStatus.textContent = '识别完成';
        voiceStatus.style.color = '#07c160';
    }
    
    // 显示操作说明文档
    function showGuideDocs(query, window) {
        // 模拟根据查询内容返回说明文档
        const docs = getGuideDocs(query);
        
        docsContent.innerHTML = docs;
        guideDocs.style.display = 'block';
        
        // 添加显示动画
        guideDocs.style.opacity = '0';
        guideDocs.style.transform = 'translateY(20px)';
        setTimeout(() => {
            guideDocs.style.transition = 'all 0.3s ease';
            guideDocs.style.opacity = '1';
            guideDocs.style.transform = 'translateY(0)';
        }, 10);
    }
    
    // 根据查询获取说明文档
    function getGuideDocs(query) {
        const lowerQuery = query.toLowerCase();
        
        // 关键词匹配
        if (lowerQuery.includes('创建') || lowerQuery.includes('新建') || lowerQuery.includes('添加')) {
            return `
                <div class="doc-item">
                    <h5>📝 创建操作</h5>
                    <ol>
                        <li>点击"新建"按钮或使用快捷键 Ctrl+N</li>
                        <li>填写必要的信息字段</li>
                        <li>点击"保存"完成创建</li>
                    </ol>
                </div>
            `;
        } else if (lowerQuery.includes('删除') || lowerQuery.includes('移除')) {
            return `
                <div class="doc-item">
                    <h5>🗑️ 删除操作</h5>
                    <ol>
                        <li>选择要删除的项目</li>
                        <li>点击"删除"按钮或按 Delete 键</li>
                        <li>确认删除操作</li>
                    </ol>
                </div>
            `;
        } else if (lowerQuery.includes('编辑') || lowerQuery.includes('修改') || lowerQuery.includes('更新')) {
            return `
                <div class="doc-item">
                    <h5>✏️ 编辑操作</h5>
                    <ol>
                        <li>双击要编辑的项目</li>
                        <li>修改需要更改的内容</li>
                        <li>点击"保存"应用更改</li>
                    </ol>
                </div>
            `;
        } else if (lowerQuery.includes('搜索') || lowerQuery.includes('查找')) {
            return `
                <div class="doc-item">
                    <h5>🔍 搜索操作</h5>
                    <ol>
                        <li>在搜索框中输入关键词</li>
                        <li>按 Enter 键或点击搜索按钮</li>
                        <li>查看搜索结果列表</li>
                    </ol>
                </div>
            `;
        } else {
            return `
                <div class="doc-item">
                    <h5>📚 通用操作指南</h5>
                    <p>根据您的提问"${query}"，以下是相关操作说明：</p>
                    <ul>
                        <li>使用菜单栏访问各项功能</li>
                        <li>右键点击可查看上下文菜单</li>
                        <li>使用快捷键提高操作效率</li>
                        <li>查看帮助文档获取更多信息</li>
                    </ul>
                    <p style="margin-top: 15px; color: #999; font-size: 12px;">💡 提示：可以尝试说"如何创建"、"怎么删除"等具体问题</p>
                </div>
            `;
        }
    }
}

// 关闭窗口
function closeWindow(windowElement) {
    // 如果是鼠标指针窗口，清理自定义指针
    if (windowElement._cleanupCursor) {
        windowElement._cleanupCursor();
    }
    
    // 如果是总结窗口，清理事件监听
    if (windowElement._cleanupSummary) {
        windowElement._cleanupSummary();
    }
    
    windowElement.style.opacity = '0';
    windowElement.style.transform = 'scale(0.8) translateY(20px)';
    
    setTimeout(() => {
        if (windowElement.parentNode) {
            windowElement.parentNode.removeChild(windowElement);
        }
    }, 300);
}

// 导航到功能页面（保留备用）
function navigateToFeature(feature, button) {
    const page = featurePages[feature];
    const featureName = featureNames[feature];
    
    if (!page) {
        console.error(`未找到功能页面: ${feature}`);
        return;
    }
    
    // 添加加载状态
    if (button) {
        button.classList.add('loading');
    }
    
    // 检查页面是否存在
    checkPageExists(page).then(exists => {
        if (exists) {
            // 延迟跳转，显示加载动画
            setTimeout(() => {
                window.location.href = page;
            }, 300);
        } else {
            // 页面不存在，显示提示
            alert(`功能"${featureName}"的页面正在开发中，敬请期待！`);
            if (button) {
                button.classList.remove('loading');
            }
        }
    }).catch(() => {
        // 如果检查失败，直接尝试跳转
        window.location.href = page;
    });
}

// 检查页面是否存在
function checkPageExists(url) {
    return fetch(url, { method: 'HEAD' })
        .then(response => response.ok)
        .catch(() => false);
}

// 按钮悬停时移动到桌宠位置的效果已在CSS中实现
// 这里可以添加额外的交互效果

// 重置按钮变换
document.querySelectorAll('.feature-btn').forEach((btn, index) => {
    btn.addEventListener('mouseleave', () => {
        if (isExpanded) {
            // 恢复原始位置 - 桌宠左侧自底向上排列
            const isMobile = window.innerWidth <= 480;
            const isTablet = window.innerWidth <= 768;
            
            let positions;
            if (isMobile) {
                positions = [
                    `translate(0, 0) scale(1)`,
                    `translate(0, -100px) scale(1)`,
                    `translate(0, -200px) scale(1)`,
                    `translate(0, -300px) scale(1)`
                ];
            } else if (isTablet) {
                positions = [
                    `translate(0, 0) scale(1)`,
                    `translate(0, -120px) scale(1)`,
                    `translate(0, -240px) scale(1)`,
                    `translate(0, -360px) scale(1)`
                ];
            } else {
                positions = [
                    `translate(0, 0) scale(1)`,
                    `translate(0, -140px) scale(1)`,
                    `translate(0, -280px) scale(1)`,
                    `translate(0, -420px) scale(1)`
                ];
            }
            btn.style.transform = positions[index];
        }
    });
});

