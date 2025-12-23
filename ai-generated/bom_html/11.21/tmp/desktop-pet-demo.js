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

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    const featureCards = document.querySelectorAll('.feature-card');
    
    // 为每个卡片添加点击事件
    featureCards.forEach(card => {
        const feature = card.getAttribute('data-feature');
        
        // 点击事件
        card.addEventListener('click', () => {
            navigateToFeature(feature);
        });
        
        // 键盘支持
        card.setAttribute('tabindex', '0');
        card.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                navigateToFeature(feature);
            }
        });
        
        // 添加鼠标进入时的音效提示（可选）
        card.addEventListener('mouseenter', () => {
            card.style.transition = 'all 0.3s ease';
        });
    });
    
    // 添加页面加载动画
    animateOnLoad();
});

// 导航到功能页面
function navigateToFeature(feature) {
    const page = featurePages[feature];
    const featureName = featureNames[feature];
    
    if (!page) {
        console.error(`未找到功能页面: ${feature}`);
        return;
    }
    
    // 添加加载状态
    const card = document.querySelector(`[data-feature="${feature}"]`);
    if (card) {
        card.classList.add('loading');
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
            if (card) {
                card.classList.remove('loading');
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

// 页面加载动画
function animateOnLoad() {
    const cards = document.querySelectorAll('.feature-card');
    
    // 使用 Intersection Observer 实现滚动动画
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.animationPlayState = 'running';
            }
        });
    }, {
        threshold: 0.1
    });
    
    cards.forEach(card => {
        observer.observe(card);
    });
}

// 添加鼠标跟随效果（可选）
document.addEventListener('mousemove', (e) => {
    const cards = document.querySelectorAll('.feature-card');
    cards.forEach(card => {
        const rect = card.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        
        // 计算鼠标相对于卡片中心的位置
        const centerX = rect.width / 2;
        const centerY = rect.height / 2;
        const deltaX = (x - centerX) / centerX;
        const deltaY = (y - centerY) / centerY;
        
        // 添加轻微的3D倾斜效果
        if (card.matches(':hover')) {
            card.style.transform = `translateY(-10px) scale(1.02) perspective(1000px) rotateX(${deltaY * -5}deg) rotateY(${deltaX * 5}deg)`;
        }
    });
});

// 重置卡片变换
document.querySelectorAll('.feature-card').forEach(card => {
    card.addEventListener('mouseleave', () => {
        card.style.transform = '';
    });
});

