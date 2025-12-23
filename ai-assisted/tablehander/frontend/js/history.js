// 历史数据页面应用类
class HistoryApp {
    constructor() {
        this.currentTab = null;
        this.historyData = [];
        this.init();
    }

    // 初始化应用
    async init() {
        await this.loadHistoryData();
        this.renderTabs();
        this.bindEvents();
    }

    // 加载历史数据
    async loadHistoryData() {
        try {
            // 调用我们的后端API获取历史文件列表
            const response = await fetch('http://localhost:5006/api/history');
            if (response.ok) {
                const result = await response.json();
                if (result.success) {
                    // 转换API返回的数据格式
                    this.historyData = result.data.map(file => ({
                        filename: file.文件名,
                        title: this.getDisplayTitle(file.文件名),
                        type: this.getFileType(file.文件名),
                        size: 0,
                        lastModified: Date.now(),
                        paragraphCount: file.记录数量 || 0,
                        filePath: file.文件路径
                    }));
                    console.log('从API加载历史数据成功:', this.historyData);
                    return;
                }
            }
        } catch (error) {
            console.warn('从API加载历史数据失败，使用默认数据:', error);
        }
        
        // 如果API不可用，使用默认数据
        this.historyData = [
            {
                filename: '2025市文创资金在建扶持类项目申请表样表.json',
                title: '市文创资金项目申请表',
                type: 'cultural',
                size: 0,
                lastModified: Date.now(),
                paragraphCount: 0
            },
            {
                filename: '小巨人申报书_财务数据脱敏版.json',
                title: '专精特新小巨人申报书',
                type: 'specialized',
                size: 0,
                lastModified: Date.now(),
                paragraphCount: 0
            },
            {
                filename: '黄浦区设计创新企业申报书.json',
                title: '黄浦区设计创新企业申报书',
                type: 'cultural',
                size: 0,
                lastModified: Date.now(),
                paragraphCount: 0
            }
        ];
        console.log('使用默认历史数据');
    }

    // 根据文件名获取显示标题
    getDisplayTitle(filename) {
        return filename.replace('.json', '').substring(0, 20);
    }

    // 根据文件名判断文件类型
    getFileType(filename) {
        if (filename.includes('小巨人')) {
            return 'specialized';
        } else {
            return 'cultural';
        }
    }

    // 渲染选项卡
    renderTabs() {
        const tabsContainer = document.querySelector('.history-tabs');
        
        // 清除现有的选项卡（保留上传按钮）
        const existingTabs = tabsContainer.querySelectorAll('.tab-item');
        existingTabs.forEach(tab => tab.remove());

        // 为每个历史文件创建选项卡，插入到上传按钮之后
        this.historyData.forEach((item, index) => {
            const tabElement = this.createTabElement(item, index);
            tabsContainer.appendChild(tabElement);
        });
    }

    // 创建选项卡元素
    createTabElement(item, index) {
        const tabDiv = document.createElement('div');
        tabDiv.className = `tab-item ${index === 0 ? 'active' : ''}`;
        tabDiv.dataset.tab = item.filename;
        
        if (index === 0) {
            this.currentTab = item.filename;
        }

        // 根据类型选择图标颜色
        const iconColor = item.type === 'specialized' ? '#4285f4' : '#52c41a';
        
        tabDiv.innerHTML = `
            <div class="tab-header">
                <div class="document-type-badge">
                    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M3 2h10a1 1 0 011 1v10a1 1 0 01-1 1H3a1 1 0 01-1-1V3a1 1 0 011-1z"
                            fill="${iconColor}" />
                        <path d="M5 5h6M5 7h6M5 9h4" stroke="white" stroke-width="1" stroke-linecap="round" />
                    </svg>
                    <span>${item.title}</span>
                </div>
                <button class="delete-btn" onclick="event.stopPropagation(); app.deleteFile('${item.filename}')" title="删除文件">
                    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M6 2h4M2 4h12M10.5 4v8a1 1 0 01-1 1h-3a1 1 0 01-1-1V4M6.5 6.5v3M9.5 6.5v3" 
                              stroke="#ff4d4f" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                </button>
            </div>
            <div class="document-preview">
                <div class="preview-image">
                    <div class="preview-placeholder ${item.type === 'cultural' ? 'meeting' : ''}">
                        ${item.type === 'cultural' ? `
                            <div class="meeting-header">
                                <div class="meeting-title"></div>
                                <div class="meeting-info"></div>
                            </div>
                            <div class="meeting-content">
                                <div class="bullet-point"></div>
                                <div class="bullet-point"></div>
                                <div class="bullet-point"></div>
                            </div>
                        ` : `
                            <div class="preview-lines">
                                <div class="line"></div>
                                <div class="line"></div>
                                <div class="line short"></div>
                            </div>
                        `}
                    </div>
                </div>
            </div>
            <div class="document-stats">
                <span class="usage-count">${item.paragraphCount > 0 ? item.paragraphCount + ' 个段落' : '点击查看详情'}</span>
            </div>
        `;

        return tabDiv;
    }

    // 绑定事件
    bindEvents() {
        // 使用事件委托处理动态创建的选项卡
        document.querySelector('.history-tabs').addEventListener('click', (e) => {
            // 如果点击的是删除按钮，不处理标签卡切换
            if (e.target.closest('.delete-btn')) {
                return;
            }
            
            const tabItem = e.target.closest('.tab-item');
            if (tabItem && tabItem.dataset.tab) {
                const tabName = tabItem.dataset.tab;
                this.switchTab(tabName);
            }
        });
    }

    // 切换选项卡
    switchTab(tabName) {
        // 更新选项卡状态
        document.querySelectorAll('.tab-item').forEach(tab => {
            tab.classList.remove('active');
        });
        const targetTab = document.querySelector(`[data-tab="${tabName}"]`);
        if (targetTab) {
            targetTab.classList.add('active');
        }

        this.currentTab = tabName;
        
        // 显示弹窗
        this.showModal(tabName);
    }

    // 显示弹窗
    async showModal(filename) {
        const modal = document.getElementById('modalOverlay');
        const modalTitle = document.getElementById('modalTitle');
        const modalContent = document.getElementById('modalContent');

        // 找到对应的数据项
        const dataItem = this.historyData.find(item => item.filename === filename);
        if (!dataItem) {
            console.error('未找到对应的数据项:', filename);
            return;
        }

        // 设置标题
        modalTitle.textContent = dataItem.title;
        
        // 显示加载状态
        modalContent.innerHTML = '<div class="loading-content">正在加载数据...</div>';
        
        // 显示弹窗
        modal.classList.add('show');
        document.body.style.overflow = 'hidden';

        try {
            // 加载JSON数据
            const jsonData = await this.loadJsonData(filename);
            // 渲染内容
            modalContent.innerHTML = this.renderJsonContent(jsonData, dataItem);
        } catch (error) {
            console.error('加载JSON数据失败:', error);
            modalContent.innerHTML = '<div class="error-content">加载数据失败，请稍后重试</div>';
        }
    }

    // 加载JSON数据
    async loadJsonData(filename) {
        try {
            // 调用我们的后端API获取文件内容
            const response = await fetch(`http://localhost:5006/api/file/${encodeURIComponent(filename)}`);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const result = await response.json();
            
            if (result.success) {
                console.log('从API加载文件内容成功:', result.file_info);
                return result.data;
            } else {
                throw new Error(result.message || '获取文件内容失败');
            }
        } catch (error) {
            console.error('加载JSON文件失败:', error);
            throw error;
        }
    }

    // 渲染JSON内容
    renderJsonContent(jsonData, dataItem) {
        if (!jsonData || !jsonData.document_structure) {
            return '<div class="error-content">数据格式错误</div>';
        }

        let content = '<div class="document-content">';
        
        // 添加文档基本信息和操作按钮
        content += `
            <div class="document-section">
                <div class="section-header">
                    <h3 class="section-title">文档信息</h3>
                    <div class="action-buttons">
                        <button class="copy-all-btn" onclick="app.copyAllContent()">复制全部内容</button>
                        <button class="export-btn" onclick="app.exportContent()">导出文本</button>
                    </div>
                </div>
                <div class="info-grid">
                    <div class="info-item">
                        <span class="info-label">文档类型</span>
                        <span class="info-value">${dataItem.title}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">文件名</span>
                        <span class="info-value">${dataItem.filename}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">段落数量</span>
                        <span class="info-value">${jsonData.document_structure.length}</span>
                    </div>
                </div>
            </div>
        `;

        // 添加文档内容区域
        content += '<div class="document-section">';
        content += '<h3 class="section-title">文档内容</h3>';
        
        // 显示所有段落内容，以便复制
        content += '<div class="content-container">';
        
        // 添加纯文本区域，方便整体复制
        const allText = this.extractAllText(jsonData.document_structure);
        
        // 添加分段显示，每段都可以单独复制
        content += '<div class="paragraphs-container">';
        content += '<h4 class="subsection-title">分段内容（点击复制单段）</h4>';
        
        jsonData.document_structure.forEach((item, index) => {
            if (item.type === 'paragraph' && item.content && item.content.trim()) {
                content += `
                    <div class="paragraph-item copyable" onclick="app.copyParagraph(this)" data-content="${this.escapeHtml(item.content)}">
                        <div class="paragraph-content">${this.escapeHtml(item.content)}</div>
                    </div>
                `;
            } else if (item.type === 'table' && item.structure && item.structure.cell_map) {
                // 处理表格数据
                content += this.renderTableAsParagraphs(item, index);
            }
        });
        
        content += '</div>'; // paragraphs-container
        content += '</div>'; // content-container
        content += '</div>'; // document-section
        content += '</div>'; // document-content

        // 存储当前数据供复制使用
        this.currentJsonData = jsonData;
        this.currentDataItem = dataItem;

        return content;
    }

    // 提取所有文本内容
    extractAllText(documentStructure) {
        let allText = '';
        
        documentStructure.forEach(item => {
            if (item.type === 'paragraph' && item.content && item.content.trim()) {
                allText += item.content.trim() + '\n';
            } else if (item.type === 'table' && item.structure && item.structure.cell_map) {
                allText += `\n[表格 ${item.table_index + 1}]\n`;
                let currentRow = -1;
                
                item.structure.cell_map.forEach(row => {
                    row.forEach(cell => {
                        if (cell.content && cell.content.trim()) {
                            // 如果行号变化，添加分割线
                            if (cell.row !== currentRow && currentRow !== -1) {
                                allText += '---\n';
                            }
                            currentRow = cell.row;
                            allText += cell.content.trim() + '\n';
                        }
                    });
                });
                allText += '\n';
            }
        });
        
        return allText;
    }

    // 将表格渲染为段落形式
    renderTableAsParagraphs(tableItem, tableIndex) {
        const structure = tableItem.structure;
        if (!structure || !structure.cell_map) {
            return '';
        }

        let tableContent = '';
        let currentRow = -1;

        // 添加表格标题
        tableContent += `
            <div class="table-divider">
                <span class="table-title">表格 ${tableItem.table_index + 1} (${structure.rows}行 × ${structure.columns}列)</span>
            </div>
        `;

        // 遍历所有单元格
        structure.cell_map.forEach((row, rowIndex) => {
            row.forEach((cell, colIndex) => {
                if (cell.content && cell.content.trim()) {
                    // 如果行号发生变化，添加行分割线
                    if (cell.row !== currentRow && currentRow !== -1) {
                        tableContent += `<div class="row-divider"></div>`;
                    }
                    currentRow = cell.row;

                    // 添加单元格内容作为段落
                    tableContent += `
                        <div class="paragraph-item copyable table-cell-item" onclick="app.copyParagraph(this)" data-content="${this.escapeHtml(cell.content)}">
                            <div class="paragraph-content">${this.escapeHtml(cell.content)}</div>
                        </div>
                    `;
                }
            });
        });

        return tableContent;
    }

    // HTML转义
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // 关闭弹窗
    closeModal() {
        const modal = document.getElementById('modalOverlay');
        modal.classList.remove('show');
        document.body.style.overflow = ''; // 恢复滚动
    }



    // 复制全部内容
    copyAllContent() {
        if (!this.currentJsonData) return;
        
        const allText = this.extractAllText(this.currentJsonData.document_structure);
        this.copyToClipboard(allText, '全部内容已复制到剪贴板');
    }

    // 复制文本区域内容
    copyTextArea() {
        const textarea = document.querySelector('.content-textarea');
        if (textarea) {
            textarea.select();
            document.execCommand('copy');
            this.showCopySuccess('文本内容已复制到剪贴板');
        }
    }

    // 复制单个段落
    copyParagraph(element) {
        const content = element.dataset.content;
        if (content) {
            // 解码HTML实体
            const textarea = document.createElement('textarea');
            textarea.innerHTML = content;
            const decodedContent = textarea.value;
            
            this.copyToClipboard(decodedContent, '段落内容已复制');
            
            // 添加视觉反馈
            element.classList.add('copied');
            setTimeout(() => {
                element.classList.remove('copied');
            }, 1000);
        }
    }

    // 导出内容为文本文件
    exportContent() {
        if (!this.currentJsonData || !this.currentDataItem) return;
        
        const allText = this.currentJsonData.document_structure
            .filter(p => p.content && p.content.trim())
            .map((p, index) => `${index + 1}. ${p.content.trim()}`)
            .join('\n\n');
        
        const content = `文档：${this.currentDataItem.title}\n文件名：${this.currentDataItem.filename}\n段落数量：${this.currentJsonData.document_structure.length}\n\n内容：\n${allText}`;
        
        const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${this.currentDataItem.title}.txt`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        this.showCopySuccess('文件已导出下载');
    }

    // 复制到剪贴板的通用方法
    copyToClipboard(text, successMessage) {
        if (navigator.clipboard && window.isSecureContext) {
            navigator.clipboard.writeText(text).then(() => {
                this.showCopySuccess(successMessage);
            }).catch(err => {
                console.error('复制失败:', err);
                this.fallbackCopy(text, successMessage);
            });
        } else {
            this.fallbackCopy(text, successMessage);
        }
    }

    // 降级复制方案
    fallbackCopy(text, successMessage) {
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
            this.showCopySuccess(successMessage);
        } catch (err) {
            console.error('复制失败:', err);
            alert('复制失败，请手动复制');
        } finally {
            document.body.removeChild(textArea);
        }
    }

    // 显示复制成功提示
    showCopySuccess(message) {
        // 创建提示元素
        const toast = document.createElement('div');
        toast.className = 'copy-toast';
        toast.textContent = message;
        document.body.appendChild(toast);
        
        // 显示动画
        setTimeout(() => toast.classList.add('show'), 10);
        
        // 自动隐藏
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => document.body.removeChild(toast), 300);
        }, 2000);
    }

    // 触发文件上传
    triggerFileUpload() {
        const fileInput = document.getElementById('wordFileInput');
        if (fileInput) {
            fileInput.click();
        }
    }

    // 处理文件上传
    async handleFileUpload(event) {
        const file = event.target.files[0];
        if (!file) return;

        // 检查文件类型
        const allowedTypes = ['.doc', '.docx'];
        const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
        
        if (!allowedTypes.includes(fileExtension)) {
            alert('请选择Word文档文件（.doc 或 .docx）');
            return;
        }

        // 显示上传进度
        this.showUploadProgress('正在上传文件...');

        try {
            // 上传并解析文档
            const result = await this.uploadAndParseDocument(file);
            
            if (result.success) {
                this.showUploadProgress('解析完成，正在刷新列表...');
                
                // 刷新历史文件列表
                await this.loadHistoryData();
                this.renderTabs();
                
                // 隐藏进度提示
                this.hideUploadProgress();
                
                // 显示成功消息
                const stats = result.data.statistics;
                this.showCopySuccess(
                    `文档 "${file.name}" 解析成功！\n` +
                    `共解析 ${stats.total_items} 项内容（${stats.paragraphs} 个段落，${stats.tables} 个表格）`
                );
                
                // 清空文件输入
                event.target.value = '';
            } else {
                throw new Error(result.message || '解析失败');
            }
            
        } catch (error) {
            console.error('文件处理失败:', error);
            this.hideUploadProgress();
            alert(`文件处理失败: ${error.message}`);
            
            // 清空文件输入
            event.target.value = '';
        }
    }

    // 上传并解析Word文档
    async uploadAndParseDocument(file) {
        try {
            const formData = new FormData();
            formData.append('file', file);
            
            const response = await fetch('http://localhost:5006/api/upload-and-parse', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            return result;
            
        } catch (error) {
            console.error('上传并解析Word文档失败:', error);
            throw error;
        }
    }

    // 显示上传进度
    showUploadProgress(message) {
        // 创建或更新进度提示
        let progressDiv = document.getElementById('uploadProgress');
        if (!progressDiv) {
            progressDiv = document.createElement('div');
            progressDiv.id = 'uploadProgress';
            progressDiv.className = 'upload-progress';
            document.body.appendChild(progressDiv);
        }
        
        progressDiv.innerHTML = `
            <div class="progress-content">
                <div class="progress-spinner"></div>
                <div class="progress-message">${message}</div>
            </div>
        `;
        progressDiv.style.display = 'flex';
    }

    // 隐藏上传进度
    hideUploadProgress() {
        const progressDiv = document.getElementById('uploadProgress');
        if (progressDiv) {
            progressDiv.style.display = 'none';
        }
    }

    // 删除文件
    async deleteFile(filename) {
        // 显示确认对话框
        const confirmed = confirm(`确定要删除文件 "${filename}" 吗？\n此操作不可撤销。`);
        if (!confirmed) {
            return;
        }

        try {
            // 显示删除进度
            this.showUploadProgress('正在删除文件...');

            // 调用删除API
            const response = await fetch(`http://localhost:5006/api/history/${encodeURIComponent(filename)}`, {
                method: 'DELETE'
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();

            if (result.success) {
                // 删除成功，刷新文件列表
                this.showUploadProgress('删除成功，正在刷新列表...');
                
                await this.loadHistoryData();
                this.renderTabs();
                
                // 隐藏进度提示
                this.hideUploadProgress();
                
                // 显示成功消息
                this.showCopySuccess(`文件 "${filename}" 已成功删除`);
                
                // 如果删除的是当前打开的文件，关闭弹窗
                if (this.currentTab === filename) {
                    this.closeModal();
                    this.currentTab = null;
                }
            } else {
                throw new Error(result.message || '删除失败');
            }

        } catch (error) {
            console.error('删除文件失败:', error);
            this.hideUploadProgress();
            alert(`删除文件失败: ${error.message}`);
        }
    }
}

// 应用启动
document.addEventListener('DOMContentLoaded', () => {
    window.app = new HistoryApp();
});