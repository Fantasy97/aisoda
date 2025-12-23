const demoArea = document.getElementById('demoArea');
const cursorName = document.getElementById('cursorName');
const cursorButtons = document.querySelectorAll('.cursor-btn');

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

// 切换指针样式
function changeCursor(cursorType) {
    demoArea.style.cursor = cursorType;
    cursorName.textContent = cursorNames[cursorType] || cursorType;
    
    // 更新按钮激活状态
    cursorButtons.forEach(btn => {
        btn.classList.remove('active');
    });
    
    const activeBtn = document.querySelector(`[data-cursor="${cursorType}"]`);
    if (activeBtn) {
        activeBtn.classList.add('active');
    }
    
    // 添加切换动画
    demoArea.style.transform = 'scale(0.98)';
    setTimeout(() => {
        demoArea.style.transform = 'scale(1)';
    }, 100);
}

// 为所有按钮添加点击事件
cursorButtons.forEach(btn => {
    btn.addEventListener('click', () => {
        const cursorType = btn.getAttribute('data-cursor');
        changeCursor(cursorType);
        
        // 添加点击反馈
        btn.style.transform = 'scale(0.95)';
        setTimeout(() => {
            btn.style.transform = '';
        }, 100);
    });
});

// 初始化默认选中
changeCursor('default');

// 添加键盘快捷键支持
let currentIndex = 0;
const cursorTypes = Array.from(cursorButtons).map(btn => btn.getAttribute('data-cursor'));

document.addEventListener('keydown', (e) => {
    if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
        currentIndex = (currentIndex + 1) % cursorTypes.length;
        changeCursor(cursorTypes[currentIndex]);
    } else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
        currentIndex = (currentIndex - 1 + cursorTypes.length) % cursorTypes.length;
        changeCursor(cursorTypes[currentIndex]);
    }
});

// 添加随机切换功能（可选）
function randomCursor() {
    const randomIndex = Math.floor(Math.random() * cursorTypes.length);
    currentIndex = randomIndex;
    changeCursor(cursorTypes[randomIndex]);
}

// 可以通过按R键随机切换
document.addEventListener('keydown', (e) => {
    if (e.key === 'r' || e.key === 'R') {
        randomCursor();
    }
});
