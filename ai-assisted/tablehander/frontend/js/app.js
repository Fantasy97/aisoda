// 应用主类 - 为后续Vue迁移做准备
class InfoQueryApp {
    constructor() {
        console.log('InfoQueryApp 构造函数被调用');
        this.currentTab = 'contact';
        this.searchResults = [];
        this.init();
        console.log('InfoQueryApp 初始化完成');
    }

    // 初始化应用
    init() {
        this.bindEvents();
        this.loadMockData();
        // 移除初始搜索结果显示，保持界面干净
    }

    // 绑定事件
    bindEvents() {
        // 搜索按钮事件
        const searchBtn = document.getElementById('searchBtn');
        const searchInput = document.getElementById('searchInput');

        searchBtn.addEventListener('click', () => this.handleSearch());
        searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.handleSearch();
            }
        });

        // 更新数据按钮事件
        const updateBtn = document.getElementById('updateBtn');
        if (updateBtn) {
            updateBtn.addEventListener('click', () => {
                console.log('更新按钮被点击');
                this.handleUpdateData();
            });
        } else {
            console.error('找不到更新按钮元素');
        }

        // 快捷查询按钮事件
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('quick-search-btn')) {
                e.preventDefault();
                this.handleQuickSearch(e.target);
            }
        });

        // 复制按钮事件
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('copy-btn')) {
                e.preventDefault();
                this.copyCompanyName(e.target);
            }
        });

        // 删除按钮事件
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('delete-btn')) {
                e.preventDefault();
                this.deleteCompanyData(e.target);
            }
        });
    }

    // 处理快捷查询
    handleQuickSearch(button) {
        const query = button.dataset.query;
        const searchInput = document.getElementById('searchInput');

        // 将查询词填入搜索框
        searchInput.value = query;

        // 自动执行搜索
        this.handleSearch();
    }

    // 处理搜索
    handleSearch() {
        const searchInput = document.getElementById('searchInput');
        const query = searchInput.value.trim();

        if (!query) {
            this.showMessage('请输入搜索关键字');
            this.hideSearchResults();
            return;
        }

        this.showLoading();

        // 调用后端API
        this.performSearch(query);
    }

    // 执行搜索
    async performSearch(query) {
        try {
            const response = await fetch('http://192.168.61.29:5006/api/query', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    keyword: query,
                    include_context: true,
                    case_sensitive: false
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            // 添加调试日志
            console.log('API响应数据:', data);

            if (data.success) {
                console.log('搜索结果:', data.data);
                this.displaySearchResults(data.data);
                this.updateSearchInfo(data.data.length, 0.23);
                this.updateRecommendations(data.data);
            } else {
                console.error('搜索失败:', data.message);
                this.showMessage('搜索失败: ' + (data.message || '未知错误'));
            }
        } catch (error) {
            console.error('搜索请求失败:', error);
            this.showMessage('网络错误，请检查服务是否正常运行');
            // 降级到模拟数据
            const mockResults = this.getMockSearchResults(query);
            this.displaySearchResults(mockResults);
            this.updateSearchInfo(mockResults.length, 0.23);
            this.updateRecommendations(mockResults);
        } finally {
            this.hideLoading();
        }
    }

    // 获取模拟搜索结果
    getMockSearchResults(query) {
        return [
            {
                key: `${query}示例字段1`,
                value: '示例值1',
                数据源: 'example_data.json',
                查询方式: '模糊匹配'
            },
            {
                key: `${query}示例字段2`,
                value: '示例值2',
                数据源: 'example_data.json',
                查询方式: '模糊匹配'
            },
            {
                key: '推荐字段1',
                value: '推荐值1',
                数据源: 'example_data.json',
                查询方式: '上下文推荐'
            }
        ];
    }

    // 显示搜索结果
    displaySearchResults(results) {
        const resultsSection = document.querySelector('.results-section');
        const searchInfo = document.querySelector('.search-info');
        const specializedResults = document.getElementById('specializedResults');

        // 显示结果区域和搜索信息
        resultsSection.style.display = 'block';
        searchInfo.style.display = 'block';

        // 清空现有结果
        this.clearResultItems(specializedResults);

        // 过滤出模糊匹配的结果
        const matchedResults = results.filter(r => r.查询方式 !== '上下文推荐');

        // 更新结果组标题
        const specializedTitle = specializedResults.querySelector('.result-title');
        if (matchedResults.length > 0) {
            const firstResult = matchedResults[0];
            if (specializedTitle) {
                specializedTitle.textContent = `来源：${firstResult.数据源}`;
            }

            // 显示每个匹配结果
            matchedResults.forEach(result => {
                const resultItem = this.createResultItem(result);
                specializedResults.appendChild(resultItem);
            });
        } else {
            if (specializedTitle) {
                specializedTitle.textContent = '来源：无匹配结果';
            }
        }

        // 添加淡入动画
        document.querySelectorAll('.result-item').forEach(item => {
            item.classList.add('fade-in');
        });
    }

    // 清空结果项
    clearResultItems(container) {
        const existingItems = container.querySelectorAll('.result-item');
        existingItems.forEach(item => item.remove());
    }

    // 创建结果项
    createResultItem(result) {
        const div = document.createElement('div');
        div.className = 'result-item';
        div.innerHTML = `
            <div class="company-icon">
                <img src="data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAiIGhlaWdodD0iNDAiIHZpZXdCb3g9IjAgMCA0MCA0MCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHJlY3Qgd2lkdGg9IjQwIiBoZWlnaHQ9IjQwIiByeD0iOCIgZmlsbD0iIzY2NzNkYyIvPgo8cGF0aCBkPSJNMTIgMTZoMTZ2OEgxMnYtOHoiIGZpbGw9IndoaXRlIi8+Cjwvc3ZnPgo=" alt="Field">
            </div>
            <div class="company-info">
                <div class="field-name">${result.key}</div>
                <div class="field-value">${result.value}</div>
            </div>
            <div class="result-actions">
                <button class="copy-btn" data-copy="${result.value}">复制</button>
                <button class="delete-btn" data-key="${result.key}">删除</button>
            </div>
        `;
        return div;
    }

    // 复制公司名称
    copyCompanyName(button) {
        const companyName = button.dataset.copy;

        // 使用现代浏览器的 Clipboard API
        if (navigator.clipboard && window.isSecureContext) {
            navigator.clipboard.writeText(companyName).then(() => {
                this.showCopySuccess(button);
            }).catch(err => {
                console.error('复制失败:', err);
                this.fallbackCopy(companyName, button);
            });
        } else {
            // 降级方案
            this.fallbackCopy(companyName, button);
        }
    }

    // 降级复制方案
    fallbackCopy(text, button) {
        const textArea = document.createElement('textarea');
        textArea.value = text;
        textArea.style.position = 'fixed';
        textArea.style.left = '-999999px';
        textArea.style.top = '-999999px';
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();

        try {
            document.execCommand('copy');
            this.showCopySuccess(button);
        } catch (err) {
            console.error('复制失败:', err);
            this.showMessage('复制失败，请手动复制');
        } finally {
            document.body.removeChild(textArea);
        }
    }

    // 显示复制成功状态
    showCopySuccess(button) {
        const originalText = button.textContent;
        button.textContent = '已复制!';
        button.classList.add('copied');

        setTimeout(() => {
            button.textContent = originalText;
            button.classList.remove('copied');
        }, 2000);
    }

    // 删除公司数据
    async deleteCompanyData(button) {
        const companyKey = button.dataset.key;

        // 确认删除
        // if (!confirm(`确定要删除 "${companyKey}" 吗？`)) {
        //     return;
        // }

        // 显示删除中状态
        const originalText = button.textContent;
        button.textContent = '删除中...';
        button.disabled = true;

        try {
            // 调用更新数据接口，使用 "企业名称 @" 格式表示删除
            const deleteData = {};
            deleteData[companyKey] = '@';

            const response = await fetch('http://192.168.61.29:5006/api/update-data', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    data: deleteData
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();

            if (result.success) {
                // 显示成功状态
                button.textContent = '已删除!';
                button.classList.add('deleted');

                // 2秒后刷新搜索结果
                setTimeout(() => {
                    const searchInput = document.getElementById('searchInput');
                    if (searchInput && searchInput.value.trim()) {
                        this.handleSearch();
                    }
                }, 1000);
            } else {
                throw new Error(result.message || '删除失败');
            }
        } catch (error) {
            console.error('删除数据失败:', error);
            alert('删除失败: ' + error.message);

            // 恢复按钮状态
            button.textContent = originalText;
            button.disabled = false;
        }
    }

    // 显示加载状态
    showLoading() {
        const searchBtn = document.getElementById('searchBtn');
        searchBtn.innerHTML = '<span class="loading"></span> 查询中...';
        searchBtn.disabled = true;
    }

    // 隐藏加载状态
    hideLoading() {
        const searchBtn = document.getElementById('searchBtn');
        searchBtn.innerHTML = '查询';
        searchBtn.disabled = false;
    }

    // 显示消息
    showMessage(message) {
        // 简单的消息提示，可以后续替换为更好的UI组件
        alert(message);
    }

    // 加载模拟数据
    loadMockData() {
        // 可以在这里加载一些初始数据
        console.log('应用初始化完成');
    }



    // 更新搜索信息
    updateSearchInfo(count, time) {
        const resultCount = document.querySelector('.search-result-count');
        const searchTime = document.querySelector('.search-time');

        if (resultCount) {
            resultCount.textContent = `找到 ${count} 条相关结果`;
        }
        if (searchTime) {
            searchTime.textContent = `搜索用时: ${time}秒`;
        }
    }

    // 隐藏搜索结果区域
    hideSearchResults() {
        const resultsSection = document.querySelector('.results-section');
        const searchInfo = document.querySelector('.search-info');

        if (resultsSection) {
            resultsSection.style.display = 'none';
        }
        if (searchInfo) {
            searchInfo.style.display = 'none';
        }

        // 清理动态添加的推荐按钮
        this.updateRecommendations([]);
    }

    // 更新推荐查询
    updateRecommendations(results) {
        const quickSearchButtons = document.querySelector('.quick-search-buttons');

        // 过滤出上下文推荐的结果
        const recommendations = results.filter(r => r.查询方式 === '上下文推荐');

        // 先清除所有动态添加的推荐按钮
        const dynamicButtons = quickSearchButtons.querySelectorAll('.quick-search-btn');
        dynamicButtons.forEach(btn => btn.remove());

        // 如果有推荐结果，添加新的推荐按钮
        if (recommendations.length > 0) {
            recommendations.forEach(rec => {
                const button = document.createElement('button');
                button.className = 'quick-search-btn';
                button.setAttribute('data-query', rec.key);
                button.textContent = rec.key;
                quickSearchButtons.appendChild(button);
            });
        }
    }

    // 处理更新数据
    handleUpdateData() {
        // 显示数据输入对话框
        this.showUpdateDataDialog();
    }

    // 显示更新数据对话框
    showUpdateDataDialog() {
        const dialog = document.createElement('div');
        dialog.className = 'update-dialog-overlay';
        dialog.innerHTML = `
            <div class="update-dialog">
                <div class="dialog-header">
                    <h3>更新数据</h3>
                </div>
                <div class="dialog-content">
                    <textarea 
                        id="updateDataInput" 
                        placeholder="可以直接粘贴excel复制的文本，如需删除数据请写:企业名称 @}"
                        rows="12"
                    ></textarea>
                    <div class="dialog-actions">
                        <button class="btn-cancel" onclick="this.closest('.update-dialog-overlay').remove()">取消</button>
                        <button class="btn-confirm" onclick="window.handleUpdateConfirm()">更新数据</button>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(dialog);

        // 聚焦到文本框
        setTimeout(() => {
            document.getElementById('updateDataInput').focus();
        }, 100);
    }

    // 解析原始文本为JSON格式
    parseRawText() {
        const input = document.getElementById('updateDataInput');
        if (!input) {
            alert('找不到输入框');
            return;
        }

        const rawText = input.value.trim();
        if (!rawText) {
            alert('请先输入要解析的文本');
            return;
        }

        try {
            // 尝试直接解析JSON
            JSON.parse(rawText);
            alert('输入的已经是有效的JSON格式，无需解析');
            return;
        } catch (e) {
            // 不是JSON格式，需要解析
        }

        const parsedData = this.parseTextToJson(rawText);

        if (Object.keys(parsedData).length === 0) {
            alert('无法解析文本，请检查格式或手动输入JSON');
            return;
        }

        // 将解析后的JSON格式化并填入输入框
        const formattedJson = JSON.stringify(parsedData, null, 2);
        input.value = formattedJson;

        alert(`成功解析出 ${Object.keys(parsedData).length} 个字段`);
    }

    // 将文本解析为JSON对象
    parseTextToJson(text) {
        const result = {};

        // 按行分割文本
        const lines = text.split('\n').map(line => line.trim()).filter(line => line);

        for (const line of lines) {
            // 尝试多种分隔符模式
            const patterns = [
                /^(.+?)[:：]\s*(.+)$/,  // 冒号分隔
                /^(.+?)[=＝]\s*(.+)$/,   // 等号分隔
                /^(.+?)\s+(.+)$/,       // 空格分隔（最后尝试）
            ];

            let matched = false;
            for (const pattern of patterns) {
                const match = line.match(pattern);
                if (match) {
                    let key = match[1].trim();
                    let value = match[2].trim();

                    // 清理键名
                    key = this.cleanKey(key);
                    // 清理值
                    value = this.cleanValue(value);

                    if (key && value) {
                        result[key] = value;
                        matched = true;
                        break;
                    }
                }
            }

            // 如果没有匹配到分隔符，尝试识别特殊格式
            if (!matched) {
                // 检查是否是URL格式
                if (line.includes('http')) {
                    const urlMatch = line.match(/(.+?)\s*(https?:\/\/[^\s]+)/);
                    if (urlMatch) {
                        const key = this.cleanKey(urlMatch[1]);
                        const url = urlMatch[2];
                        if (key) {
                            result[key] = url;
                        }
                    }
                }
                // 检查是否是纯文本描述
                else if (line.length > 5 && !line.includes(':') && !line.includes('=')) {
                    // 如果是较长的文本且没有分隔符，可能是描述性文本
                    if (!result['描述'] && !result['内容'] && !result['说明']) {
                        result['内容描述'] = line;
                    }
                }
            }
        }

        // 如果解析结果为空，尝试整体作为一个字段
        if (Object.keys(result).length === 0 && text.length > 0) {
            result['复制内容'] = text;
        }

        return result;
    }

    // 清理键名
    cleanKey(key) {
        return key
            .replace(/[【】\[\]()（）]/g, '') // 移除括号
            .replace(/[^\w\u4e00-\u9fa5]/g, '') // 只保留中文、字母、数字
            .trim();
    }

    // 清理值
    cleanValue(value) {
        return value
            .replace(/^[,，。.;；]+/, '') // 移除开头的标点
            .replace(/[,，。.;；]+$/, '') // 移除结尾的标点
            .trim();
    }

    // 执行数据更新
    async performUpdateData() {
        console.log('performUpdateData 被调用');

        const input = document.getElementById('updateDataInput');
        if (!input) {
            alert('找不到输入框元素');
            return;
        }

        const rawData = input.value.trim();
        console.log('输入的数据:', rawData);

        if (!rawData) {
            alert('请输入要更新的数据');
            return;
        }

        let updateData;
        try {
            // 尝试解析JSON数据
            updateData = JSON.parse(rawData);
            console.log('直接解析JSON成功:', updateData);
        } catch (error) {
            console.log('JSON解析失败，尝试文本解析:', error.message);

            // 尝试自动解析文本
            updateData = this.parseTextToJson(rawData);

            if (Object.keys(updateData).length === 0) {
                alert('数据格式错误，无法解析。请点击"智能解析文本"按钮或手动输入JSON格式数据。\n错误信息: ' + error.message);
                return;
            }

            console.log('文本解析成功:', updateData);

            // 询问用户是否使用解析结果
            const useParseResult = confirm(
                `检测到非JSON格式文本，已自动解析出 ${Object.keys(updateData).length} 个字段：\n` +
                Object.keys(updateData).map(key => `• ${key}: ${updateData[key]}`).join('\n').substring(0, 200) +
                (Object.keys(updateData).length > 3 ? '\n...' : '') +
                '\n\n是否使用此解析结果？'
            );

            if (!useParseResult) {
                return;
            }
        }

        // 显示更新按钮加载状态
        const confirmBtn = document.querySelector('.btn-confirm');
        if (!confirmBtn) {
            alert('找不到确认按钮');
            return;
        }

        const originalText = confirmBtn.textContent;
        confirmBtn.innerHTML = '<span class="loading"></span> 更新中...';
        confirmBtn.disabled = true;

        try {
            console.log('开始发送请求到后端...');
            const response = await fetch('http://192.168.61.29:5006/api/update-data', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    data: updateData
                })
            });

            console.log('收到响应:', response);

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            console.log('响应数据:', result);

            if (result.success) {
                alert('数据更新成功！');
                // 关闭对话框
                const overlay = document.querySelector('.update-dialog-overlay');
                if (overlay) {
                    overlay.remove();
                }

                // 如果当前有搜索结果，重新搜索以显示更新后的数据
                const searchInput = document.getElementById('searchInput');
                if (searchInput && searchInput.value.trim()) {
                    this.handleSearch();
                }
            } else {
                alert('数据更新失败: ' + (result.message || '未知错误'));
            }
        } catch (error) {
            console.error('更新数据请求失败:', error);
            alert('网络错误，请检查服务是否正常运行: ' + error.message);
        } finally {
            // 恢复按钮状态
            if (confirmBtn) {
                confirmBtn.innerHTML = originalText;
                confirmBtn.disabled = false;
            }
        }
    }
}

// 工具函数
const Utils = {
    // 防抖函数
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    // 格式化日期
    formatDate(date) {
        return new Intl.DateTimeFormat('zh-CN').format(date);
    },

    // 验证输入
    validateInput(value, type = 'text') {
        if (!value || value.trim() === '') {
            return false;
        }

        switch (type) {
            case 'email':
                return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);
            case 'phone':
                return /^1[3-9]\d{9}$/.test(value);
            default:
                return true;
        }
    }
};

// 全局测试函数
window.testUpdateFunction = function () {
    console.log('测试函数被调用');
    if (window.app) {
        console.log('window.app 存在');
        if (window.app.performUpdateData) {
            console.log('performUpdateData 方法存在');
            window.app.performUpdateData();
        } else {
            console.log('performUpdateData 方法不存在');
        }
    } else {
        console.log('window.app 不存在');
    }
};

// 全局更新确认处理函数
window.handleUpdateConfirm = function () {
    console.log('handleUpdateConfirm 被调用');
    if (window.app && window.app.performUpdateData) {
        window.app.performUpdateData();
    } else {
        alert('无法找到更新方法');
        console.error('window.app:', window.app);
    }
};

// 应用启动
document.addEventListener('DOMContentLoaded', () => {
    console.log('正在初始化应用...');
    try {
        window.app = new InfoQueryApp();
        console.log('应用初始化完成，window.app:', window.app);
        console.log('可用方法:', Object.getOwnPropertyNames(Object.getPrototypeOf(window.app)));
    } catch (error) {
        console.error('应用初始化失败:', error);
    }
});

// 为Vue迁移准备的数据结构
const AppData = {
    searchQuery: '',
    searchResults: [],
    currentTab: 'contact',
    loading: false,
    tabs: [
        { key: 'contact', label: '联系人' },
        { key: 'legal', label: '法人代表' },
        { key: 'location', label: '地址' }
    ]
};

// 为Vue迁移准备的方法结构
const AppMethods = {
    handleSearch() {
        // 搜索逻辑
    },
    switchTab(tabName) {
        // 切换标签页逻辑
    },
    showCompanyDetail(company) {
        // 显示详情逻辑
    }
};