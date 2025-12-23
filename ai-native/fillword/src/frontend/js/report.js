/**
 * 智能Word表单填充服务 - 报告页面JavaScript
 * 处理报告页面的交互功能
 */

// 报告页面初始化
document.addEventListener('DOMContentLoaded', function() {
    initializeReportPage();
});

function initializeReportPage() {
    // 添加返回主页按钮（如果不存在）
    addNavigationButtons();
    
    // 设置页面样式
    setupReportStyles();
    
    // 处理下载链接
    setupDownloadLinks();
}

function addNavigationButtons() {
    // 检查是否已经有导航按钮
    if (document.querySelector('.navigation-buttons')) {
        return;
    }
    
    // 创建导航按钮容器
    const navContainer = document.createElement('div');
    navContainer.className = 'navigation-buttons';
    navContainer.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 1000;
        display: flex;
        gap: 10px;
    `;
    
    // 返回主页按钮
    const homeButton = document.createElement('a');
    homeButton.href = '/';
    homeButton.className = 'btn btn-secondary';
    homeButton.textContent = '🏠 返回主页';
    homeButton.style.cssText = `
        background: #6c757d;
        color: white;
        padding: 10px 15px;
        text-decoration: none;
        border-radius: 4px;
        font-size: 14px;
        transition: background-color 0.3s ease;
    `;
    
    homeButton.addEventListener('mouseenter', function() {
        this.style.background = '#545b62';
    });
    
    homeButton.addEventListener('mouseleave', function() {
        this.style.background = '#6c757d';
    });
    
    navContainer.appendChild(homeButton);
    
    // 查找下载链接并添加下载按钮
    const downloadLinks = document.querySelectorAll('a[href*="/api/download/"]');
    if (downloadLinks.length > 0) {
        const downloadButton = document.createElement('a');
        downloadButton.href = downloadLinks[0].href;
        downloadButton.className = 'btn btn-primary';
        downloadButton.textContent = '📥 下载文档';
        downloadButton.style.cssText = `
            background: #007bff;
            color: white;
            padding: 10px 15px;
            text-decoration: none;
            border-radius: 4px;
            font-size: 14px;
            transition: background-color 0.3s ease;
        `;
        
        downloadButton.addEventListener('mouseenter', function() {
            this.style.background = '#0056b3';
        });
        
        downloadButton.addEventListener('mouseleave', function() {
            this.style.background = '#007bff';
        });
        
        navContainer.appendChild(downloadButton);
    }
    
    // 添加到页面
    document.body.appendChild(navContainer);
}

function setupReportStyles() {
    // 添加报告页面的基础样式
    const style = document.createElement('style');
    style.textContent = `
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: #f8f9fa;
        }
        
        .report-container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        }
        
        h1, h2, h3 {
            color: #333;
            border-bottom: 2px solid #007bff;
            padding-bottom: 10px;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }
        
        th, td {
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }
        
        th {
            background-color: #f8f9fa;
            font-weight: bold;
            color: #333;
        }
        
        tr:nth-child(even) {
            background-color: #f9f9f9;
        }
        
        tr:hover {
            background-color: #f5f5f5;
        }
        
        .statistics-summary {
            background: #e7f3ff;
            border: 1px solid #b3d9ff;
            border-radius: 4px;
            padding: 20px;
            margin: 20px 0;
        }
        
        .success-rate {
            font-size: 1.2em;
            font-weight: bold;
            color: #28a745;
        }
        
        .error-rate {
            color: #dc3545;
        }
        
        .btn {
            display: inline-block;
            padding: 10px 20px;
            margin: 5px;
            text-decoration: none;
            border-radius: 4px;
            font-size: 14px;
            cursor: pointer;
            border: none;
            transition: all 0.3s ease;
        }
        
        .btn-primary {
            background-color: #007bff;
            color: white;
        }
        
        .btn-secondary {
            background-color: #6c757d;
            color: white;
        }
        
        @media (max-width: 768px) {
            .navigation-buttons {
                position: static !important;
                margin-bottom: 20px;
                justify-content: center;
            }
            
            .report-container {
                padding: 15px;
                margin: 10px;
            }
            
            table {
                font-size: 14px;
            }
            
            th, td {
                padding: 8px;
            }
        }
    `;
    
    document.head.appendChild(style);
    
    // 为报告内容添加容器类
    const body = document.body;
    if (!body.querySelector('.report-container')) {
        const container = document.createElement('div');
        container.className = 'report-container';
        
        // 将现有内容移到容器中
        while (body.firstChild && !body.firstChild.classList?.contains('navigation-buttons')) {
            container.appendChild(body.firstChild);
        }
        
        body.appendChild(container);
    }
}

function setupDownloadLinks() {
    // 为所有下载链接添加点击事件
    const downloadLinks = document.querySelectorAll('a[href*="/api/download/"]');
    
    downloadLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            // 添加下载提示
            const originalText = this.textContent;
            this.textContent = '下载中...';
            this.style.pointerEvents = 'none';
            
            // 恢复链接状态
            setTimeout(() => {
                this.textContent = originalText;
                this.style.pointerEvents = 'auto';
            }, 2000);
        });
    });
}

// 工具函数：格式化数字
function formatNumber(num) {
    return num.toLocaleString();
}

// 工具函数：格式化百分比
function formatPercentage(decimal) {
    return (decimal * 100).toFixed(1) + '%';
}

// 导出函数供其他脚本使用
window.ReportUtils = {
    formatNumber,
    formatPercentage,
    addNavigationButtons,
    setupReportStyles
};