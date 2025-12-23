const chatMessages = document.getElementById('chatMessages');
const messageInput = document.getElementById('messageInput');
const sendBtn = document.getElementById('sendBtn');

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
        simulateReply();
    }, 1000 + Math.random() * 2000);
}

// 模拟回复
function simulateReply() {
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
scrollToBottom();
