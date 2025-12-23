/**
 * 智能Word表单填充服务 - 前端JavaScript
 * 处理文件上传、进度显示和结果处理
 */

// 上传状态管理
const uploadState = {
    file: null,
    uploading: false,
    progress: 0,
    status: 'idle', // idle, uploading, processing, completed, error
    error: null,
    result: null
};

// 数据更新状态管理
const updateState = {
    emptyCellsFile: null,
    fullCellsFile: null,
    updating: false,
    status: 'idle',
    error: null,
    result: null
};

// DOM元素
let uploadForm, fileInput, resultDiv, uploadArea;
let updateForm, emptyCellsInput, fullCellsInput, updateResultDiv;

// 初始化
document.addEventListener('DOMContentLoaded', function() {
    initializeElements();
    setupEventListeners();
});

function initializeElements() {
    // 文档处理相关元素
    uploadForm = document.getElementById('uploadForm');
    fileInput = document.getElementById('fileInput');
    resultDiv = document.getElementById('result');
    uploadArea = document.querySelector('.upload-area');
    
    // 数据更新相关元素
    updateForm = document.getElementById('updateForm');
    emptyCellsInput = document.getElementById('emptyCellsInput');
    fullCellsInput = document.getElementById('fullCellsInput');
    updateResultDiv = document.getElementById('updateResult');
}

function setupEventListeners() {
    // 文档处理事件
    uploadForm.addEventListener('submit', handleFormSubmit);
    fileInput.addEventListener('change', handleFileSelect);
    setupDragAndDrop();
    
    // 数据更新事件
    updateForm.addEventListener('submit', handleUpdateSubmit);
    emptyCellsInput.addEventListener('change', handleUpdateFileSelect);
    fullCellsInput.addEventListener('change', handleUpdateFileSelect);
}

function setupDragAndDrop() {
    // 防止默认拖拽行为
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        uploadArea.addEventListener(eventName, preventDefaults, false);
        document.body.addEventListener(eventName, preventDefaults, false);
    });
    
    // 高亮拖拽区域
    ['dragenter', 'dragover'].forEach(eventName => {
        uploadArea.addEventListener(eventName, highlight, false);
    });
    
    ['dragleave', 'drop'].forEach(eventName => {
        uploadArea.addEventListener(eventName, unhighlight, false);
    });
    
    // 处理文件拖拽
    uploadArea.addEventListener('drop', handleDrop, false);
}

function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}

function highlight() {
    uploadArea.classList.add('dragover');
}

function unhighlight() {
    uploadArea.classList.remove('dragover');
}

function handleDrop(e) {
    const dt = e.dataTransfer;
    const files = dt.files;
    
    if (files.length > 0) {
        fileInput.files = files;
        handleFileSelect();
    }
}

function handleFileSelect() {
    const file = fileInput.files[0];
    if (file) {
        uploadState.file = file;
        validateFile(file);
    }
}

function validateFile(file) {
    const allowedTypes = [
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/msword'
    ];
    
    const maxSize = 16 * 1024 * 1024; // 16MB
    
    if (!allowedTypes.includes(file.type) && !file.name.match(/\.(docx|doc)$/i)) {
        showError('请选择Word文档文件（.docx或.doc格式）');
        return false;
    }
    
    if (file.size > maxSize) {
        showError('文件大小不能超过16MB');
        return false;
    }
    
    return true;
}

async function handleFormSubmit(e) {
    e.preventDefault();
    
    if (!uploadState.file) {
        showError('请选择文件');
        return;
    }
    
    if (!validateFile(uploadState.file)) {
        return;
    }
    
    await uploadAndProcess();
}

async function uploadAndProcess() {
    try {
        updateUploadState('uploading');
        showProcessingStatus('⏳ 正在上传文档...');
        
        const formData = new FormData();
        formData.append('file', uploadState.file);
        
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error(`HTTP错误: ${response.status}`);
        }
        
        const result = await response.json();
        
        if (result.success) {
            updateUploadState('completed', result);
            handleUploadSuccess(result);
        } else {
            throw new Error(result.error || '处理失败');
        }
        
    } catch (error) {
        console.error('上传失败:', error);
        updateUploadState('error', null, error.message);
        showError(`上传失败: ${error.message}`);
    }
}

function updateUploadState(status, result = null, error = null) {
    uploadState.status = status;
    uploadState.result = result;
    uploadState.error = error;
    uploadState.uploading = (status === 'uploading' || status === 'processing');
    
    // 更新UI状态
    const submitButton = uploadForm.querySelector('button[type="submit"]');
    submitButton.disabled = uploadState.uploading;
    submitButton.textContent = uploadState.uploading ? '处理中...' : '上传并处理';
}

function showProcessingStatus(message) {
    resultDiv.style.display = 'block';
    resultDiv.className = 'result processing';
    resultDiv.innerHTML = `
        <div class="loading"></div>
        ${message}
    `;
}

function handleUploadSuccess(result) {
    const statistics = result.statistics || {};
    const successRate = (statistics.success_rate * 100).toFixed(1);
    
    let buttonsHtml = '';
    // let buttonsHtml = `<a href="/api/download/${result.output_filename}" class="btn">下载填充后的文档</a>`;
    
    // 如果有HTML报告，直接显示报告按钮
    if (result.report_filename && result.report_url) {
        buttonsHtml += `
            <a href="${result.report_url}" class="btn" target="_blank" style="margin-left: 10px; background: #28a745;">
                查看详细报告
            </a>
        `;
    }
    
    resultDiv.className = 'result success';
    resultDiv.innerHTML = `
        <h3>✅ 处理成功</h3>
        <p>处理了 ${statistics.total_processed || 0} 个单元格</p>
        <p>成功填充 ${statistics.successful_fills || 0} 个</p>
        <p>成功率: ${successRate}%</p>
        <div style="margin-top: 15px;">
            ${buttonsHtml}
        </div>
    `;
    
    // 如果有报告，显示提示信息
    if (result.report_filename) {
        resultDiv.innerHTML += `
            <div style="margin-top: 15px; padding: 15px; background: #e7f3ff; border-radius: 4px;">
                <p><strong>📊 HTML报告已生成！</strong></p>
                <p>报告包含详细的填充结果和统计信息。</p>
            </div>
        `;
    }
}



function jumpToReport(reportUrl) {
    // 跳转到报告页面
    window.location.href = reportUrl;
}

function handleDownload() {
    // 下载完成后可以选择清理状态或显示其他信息
    console.log('开始下载文件...');
}

function showError(message) {
    resultDiv.style.display = 'block';
    resultDiv.className = 'result error';
    resultDiv.innerHTML = `
        <h3>❌ 错误</h3>
        <p>${message}</p>
        <button class="btn" onclick="resetForm()" style="margin-top: 10px;">重新开始</button>
    `;
}

function resetForm() {
    // 重置表单状态
    uploadState.file = null;
    uploadState.status = 'idle';
    uploadState.error = null;
    uploadState.result = null;
    uploadState.uploading = false;
    
    // 重置UI
    fileInput.value = '';
    resultDiv.style.display = 'none';
    
    const submitButton = uploadForm.querySelector('button[type="submit"]');
    submitButton.disabled = false;
    submitButton.textContent = '上传并处理';
    
    unhighlight();
}

// 全局错误处理
window.addEventListener('error', function(e) {
    console.error('JavaScript错误:', e.error);
    if (uploadState.uploading) {
        showError('处理过程中发生错误，请重试');
        updateUploadState('error');
    }
    if (updateState.updating) {
        showUpdateError('更新过程中发生错误，请重试');
        updateUpdateState('error');
    }
});

// 网络错误处理
window.addEventListener('online', function() {
    console.log('网络连接已恢复');
});

window.addEventListener('offline', function() {
    console.log('网络连接已断开');
    if (uploadState.uploading) {
        showError('网络连接已断开，请检查网络后重试');
        updateUploadState('error');
    }
    if (updateState.updating) {
        showUpdateError('网络连接已断开，请检查网络后重试');
        updateUpdateState('error');
    }
});

// 标签页切换功能
function switchTab(tabName) {
    // 隐藏所有标签内容
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    
    // 移除所有标签按钮的激活状态
    document.querySelectorAll('.tab-button').forEach(button => {
        button.classList.remove('active');
    });
    
    // 显示选中的标签内容
    document.getElementById(tabName + '-tab').classList.add('active');
    
    // 激活对应的标签按钮
    event.target.classList.add('active');
    
    // 重置状态
    if (tabName === 'upload') {
        resetForm();
    } else if (tabName === 'update') {
        resetUpdateForm();
    }
}

// 数据更新相关函数
function handleUpdateFileSelect() {
    updateState.emptyCellsFile = emptyCellsInput.files[0];
    updateState.fullCellsFile = fullCellsInput.files[0];
}

async function handleUpdateSubmit(e) {
    e.preventDefault();
    
    if (!updateState.emptyCellsFile || !updateState.fullCellsFile) {
        showUpdateError('请选择两个Word文档文件');
        return;
    }
    
    if (!validateFile(updateState.emptyCellsFile) || !validateFile(updateState.fullCellsFile)) {
        return;
    }
    
    await updateData();
}

async function updateData() {
    try {
        updateUpdateState('updating');
        showUpdateProcessingStatus('⏳ 正在处理文档并更新数据...');
        
        const formData = new FormData();
        formData.append('empty_cells_doc', updateState.emptyCellsFile);
        formData.append('full_cells_doc', updateState.fullCellsFile);
        
        const response = await fetch('/api/update-data', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error(`HTTP错误: ${response.status}`);
        }
        
        const result = await response.json();
        
        if (result.success) {
            updateUpdateState('completed', result);
            handleUpdateSuccess(result);
        } else {
            throw new Error(result.error || '数据更新失败');
        }
        
    } catch (error) {
        console.error('数据更新失败:', error);
        updateUpdateState('error', null, error.message);
        showUpdateError(`数据更新失败: ${error.message}`);
    }
}

function updateUpdateState(status, result = null, error = null) {
    updateState.status = status;
    updateState.result = result;
    updateState.error = error;
    updateState.updating = (status === 'updating');
    
    // 更新UI状态
    const submitButton = updateForm.querySelector('button[type="submit"]');
    submitButton.disabled = updateState.updating;
    submitButton.textContent = updateState.updating ? '更新中...' : '更新数据';
}

function showUpdateProcessingStatus(message) {
    updateResultDiv.style.display = 'block';
    updateResultDiv.className = 'result processing';
    updateResultDiv.innerHTML = `
        <div class="loading"></div>
        ${message}
    `;
}

function handleUpdateSuccess(result) {
    const updateResult = result.result.update_result;
    
    updateResultDiv.className = 'result success';
    updateResultDiv.innerHTML = `
        <h3>✅ 数据更新成功</h3>
        <div class="update-stats">
            <h4>📊 更新统计：</h4>
            <ul>
                <li>解析空单元格数量: ${result.result.empty_cells_count}</li>
                <li>成功更新字段: ${updateResult.successfully_updated}</li>
                <li>跳过字段: ${updateResult.skipped}</li>
                <li>错误字段: ${updateResult.errors}</li>
            </ul>
        </div>
        <div class="update-stats">
            <h4>📁 生成的文件：</h4>
            <ul>
                <li>空单元格数据: ${result.result.files_generated.empty_cells_json}</li>
                <li>完整数据: ${result.result.files_generated.full_cells_json}</li>
                <li>更新后的训练数据: ${result.result.files_generated.updated_example_data}</li>
            </ul>
        </div>
        <p style="margin-top: 15px; padding: 10px; background: #e7f3ff; border-radius: 4px;">
            <strong>💡 提示：</strong>数据更新完成后，系统将使用新的训练数据来提高填充准确性。
        </p>
    `;
}

function showUpdateError(message) {
    updateResultDiv.style.display = 'block';
    updateResultDiv.className = 'result error';
    updateResultDiv.innerHTML = `
        <h3>❌ 更新失败</h3>
        <p>${message}</p>
        <button class="btn" onclick="resetUpdateForm()" style="margin-top: 10px;">重新开始</button>
    `;
}

function resetUpdateForm() {
    // 重置更新表单状态
    updateState.emptyCellsFile = null;
    updateState.fullCellsFile = null;
    updateState.status = 'idle';
    updateState.error = null;
    updateState.result = null;
    updateState.updating = false;
    
    // 重置UI
    emptyCellsInput.value = '';
    fullCellsInput.value = '';
    updateResultDiv.style.display = 'none';
    
    const submitButton = updateForm.querySelector('button[type="submit"]');
    submitButton.disabled = false;
    submitButton.textContent = '更新数据';
}