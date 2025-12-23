// ==================== 飞书登录功能 ====================
// API 基础地址
const API_BASE_URL = 'https://ai-uat.aiswei-tech.com/sbom';

// 用户信息存储
let currentUserId = null;
let currentUserName = null;

// 初始化用户界面和页面显示
function initUserInterface() {
  const loginButton = document.getElementById('loginButton');
  const userInfo = document.getElementById('userInfo');
  const loginOverlay = document.getElementById('loginOverlay');
  const mainPageContent = document.getElementById('mainPageContent');
  
  // 检查本地存储是否有用户信息
  const savedUserId = localStorage.getItem('currentUserId');
  const savedUserName = localStorage.getItem('currentUserName');
  
  if (savedUserId && savedUserName) {
    // 已登录，显示主页面
    currentUserId = savedUserId;
    currentUserName = savedUserName;
    showMainPage();
    updateUserDisplay();
    // 显示设计列表视图并加载数据（确保数据同步）
    showDesignListView();
  } else {
    // 未登录，显示登录遮罩层
    showLoginOverlay();
  }
}

// 显示登录遮罩层，隐藏主页面
function showLoginOverlay() {
  const loginOverlay = document.getElementById('loginOverlay');
  const mainPageContent = document.getElementById('mainPageContent');
  
  if (loginOverlay) loginOverlay.style.display = 'flex';
  if (mainPageContent) mainPageContent.style.display = 'none';
}

// 显示主页面，隐藏登录遮罩层
function showMainPage() {
  const loginOverlay = document.getElementById('loginOverlay');
  const mainPageContent = document.getElementById('mainPageContent');
  
  if (loginOverlay) loginOverlay.style.display = 'none';
  if (mainPageContent) mainPageContent.style.display = 'block';
}

// 更新用户信息显示
function updateUserDisplay() {
  const loginButton = document.getElementById('loginButton');
  const userInfo = document.getElementById('userInfo');
  const userAvatar = document.getElementById('userAvatar');
  const userName = document.getElementById('userName');
  
  if (currentUserId && currentUserName) {
    // 显示用户信息
    if (loginButton) loginButton.style.display = 'none';
    if (userInfo) userInfo.style.display = 'flex';
    if (userAvatar) {
      // 显示用户名的第一个字符作为头像
      userAvatar.textContent = currentUserName.charAt(0);
    }
    if (userName) {
      userName.textContent = currentUserName;
    }
  } else {
    // 显示登录按钮
    if (loginButton) loginButton.style.display = 'flex';
    if (userInfo) userInfo.style.display = 'none';
  }

  updateInitiatorDisplay();
}

// 更新发起人显示
function updateInitiatorDisplay() {
  const initiatorElement = document.getElementById('initiatorName');
  if (initiatorElement) {
    initiatorElement.innerHTML = `创建人: <strong>${currentUserName || '未知'}</strong>`;
  }
}

// 飞书登录
function feishuLogin() {
  console.log('开始飞书登录...');
  
  // 打开新窗口跳转到登录接口
  const loginUrl = `${API_BASE_URL}/login`;
  const loginWindow = window.open(
    loginUrl,
    '飞书登录',
    'width=600,height=700,left=' + (window.screen.width / 2 - 300) + ',top=' + (window.screen.height / 2 - 350)
  );
  
  // 监听登录窗口关闭
  const checkClosed = setInterval(() => {
    if (loginWindow.closed) {
      clearInterval(checkClosed);
    }
  }, 1000);
}

// 监听来自登录回调窗口的消息
window.addEventListener('message', function(event) {
  // 安全检查：只接受来自同源的消息（如果需要，可以改为检查 origin）
  // if (event.origin !== window.location.origin) return;
  
  if (event.data && event.data.type === 'feishu_login_success') {
    console.log('收到登录成功消息:', event.data);
    
    // 存储用户信息
    currentUserId = event.data.userId;
    currentUserName = event.data.name || '用户';
    
    // 保存到本地存储
    localStorage.setItem('currentUserId', currentUserId);
    localStorage.setItem('currentUserName', currentUserName);
    
    // 更新界面显示
    updateUserDisplay();
    // 显示主页面，隐藏登录遮罩
    showMainPage();
    
    // 显示设计列表视图并加载数据（确保数据同步）
    // showDesignListView 内部会调用 loadUserDesigns，所以这里不需要单独调用
    showDesignListView();
    
    console.log('登录成功！用户ID:', currentUserId, '用户名:', currentUserName);
  }
});

// ==================== 加载用户设计数据 ====================
// 存储设计数据
let designDataList = [];

// 加载用户设计数据
async function loadUserDesigns(usrId, limit = 50) {
  const cardGrid = document.getElementById('designCardGrid');
  const loadingIndicator = document.getElementById('loadingIndicator');
  const emptyState = document.getElementById('emptyState');
  
  if (!cardGrid) {
    console.error('找不到卡片容器');
    return;
  }
  
  // 显示加载提示
  if (loadingIndicator) {
    loadingIndicator.style.display = 'block';
  }
  if (emptyState) {
    emptyState.style.display = 'none';
  }
  
  try {
    const url = `${API_BASE_URL}/api/user_designs?usr_id=${usrId}&limit=${limit}`;
    console.log('加载用户设计数据:', url);
    
    const response = await fetch(url);
    const result = await response.json();
    
    if (result.success && result.data) {
      designDataList = result.data;
      console.log(`成功加载 ${designDataList.length} 条设计记录`);
      
      // 调试：查看前几条数据的状态信息
      // 注意：前端接收的是后端转换后的数据，字段名已转换
      if (designDataList.length > 0) {
        console.log('前3条数据的状态信息:', designDataList.slice(0, 3).map(d => ({
          design_id: d.design_id,      // ✅ 设计ID
          status: d.status,            // ✅ 中文状态（如"审核中"）
          status_code: d.status_code,  // ✅ 英文状态码（如"PENDING"）- 用于筛选
          status_class: d.status_class, // ✅ CSS类名（如"status-review"）
          title: d.title,              // ✅ 标题（approval_name）
          desc: d.desc,                // ✅ 详情（form_value2 + create_time）
          date: d.date                 // ✅ 最后更新时间
        })));
      }
      
      // 渲染卡片
      renderDesignCards(designDataList);
      
      // 隐藏加载提示
      if (loadingIndicator) {
        loadingIndicator.style.display = 'none';
      }
      
      // 如果没有数据，显示空状态
      if (designDataList.length === 0 && emptyState) {
        emptyState.style.display = 'block';
      } else {
        // 数据加载完成后，重新初始化筛选功能（确保事件绑定正确）
        initFilterAndSearch();
        // 应用当前的筛选条件
        setTimeout(() => {
          applyFilters();
        }, 100);
      }
    } else {
      console.error('加载设计数据失败:', result.error || result.message);
      if (loadingIndicator) {
        loadingIndicator.style.display = 'none';
      }
      if (emptyState) {
        emptyState.style.display = 'block';
        emptyState.querySelector('div:last-child').textContent = result.error || '加载失败';
      }
    }
  } catch (error) {
    console.error('加载设计数据时出错:', error);
    if (loadingIndicator) {
      loadingIndicator.style.display = 'none';
    }
    if (emptyState) {
      emptyState.style.display = 'block';
      emptyState.querySelector('div:last-child').textContent = '加载失败，请稍后重试';
    }
  }
}

// 渲染设计卡片
function renderDesignCards(designs) {
  const cardGrid = document.getElementById('designCardGrid');
  if (!cardGrid) {
    console.error('找不到卡片容器');
    return;
  }
  
  // 清除现有的卡片（保留加载提示和空状态）
  const existingCards = cardGrid.querySelectorAll('.design-card');
  existingCards.forEach(card => card.remove());
  
  if (!designs || designs.length === 0) {
    return;
  }
  
  // 为每个设计创建卡片
  designs.forEach(design => {
    const card = createDesignCard(design);
    cardGrid.appendChild(card);
  });
}

// 创建单个设计卡片
function createDesignCard(design) {
  const card = document.createElement('div');
  card.className = 'design-card';
  card.setAttribute('data-design-id', design.design_id || '');
  
  // 确保使用状态码（如DRAFT, PENDING等）用于筛选，必须是英文状态码
  // 如果status_code不存在，尝试从status映射或使用默认值
  let statusCode = design.status_code || '';
  if (!statusCode) {
    // 如果后端没有返回status_code，尝试从中文status映射
    const statusText = design.status || '';
    if (statusText.includes('草稿')) {
      statusCode = 'DRAFT';
    } else if (statusText.includes('审核中') || statusText.includes('待处理')) {
      statusCode = 'PENDING';
    } else if (statusText.includes('已推送')) {
      statusCode = 'PUSHED';
    } else if (statusText.includes('失败')) {
      statusCode = 'FAILED';
    } else if (statusText.includes('已废弃')) {
      statusCode = 'DISCARDED';
    } else {
      statusCode = 'DRAFT'; // 默认值
    }
  }
  
  card.setAttribute('data-status', statusCode.toUpperCase());
  
  // 保存日期到data属性，用于时间段筛选
  if (design.date) {
    // 提取日期部分（YYYY-MM-DD）
    const dateMatch = design.date.match(/(\d{4}-\d{2}-\d{2})/);
    if (dateMatch) {
      card.setAttribute('data-date', dateMatch[1]);
    }
  }
  
  // 保存instance_code到data属性，用于筛选
  if (design.approval_instance_code) {
    card.setAttribute('data-instance-code', design.approval_instance_code);
  }
  
  // 调试日志
  console.log('创建卡片:', {
    design_id: design.design_id,
    status: design.status,
    status_code: design.status_code,
    final_status_code: statusCode
  });
  
  card.innerHTML = `
    <div class="card-header">
      <div class="card-header-top">
        <div class="card-status ${design.status_class || 'status-draft'}">${escapeHtml(design.status || '草稿')}</div>
        <span class="card-date">${escapeHtml('更新时间:' + design.date || '')}</span>
      </div>
    </div>
    <div class="card-title">${escapeHtml(design.title || '未知设计')}</div>
    <div class="card-desc">${escapeHtml(design.desc || '暂无描述')}</div>
  `;
  
  // 添加点击事件
  card.addEventListener('click', function() {
    console.log('点击设计卡片:', design.design_id, '状态:', design.status_code);
    
    // 如果状态为草稿(DRAFT)，跳转到设计详情页面
    if (design.status_code === 'DRAFT' || design.status_code === 'draft') {
      loadDesignDetailFromCard(design);
    } else {
      // 其他状态显示飞书审批实例信息弹窗
      showLarkInstanceModal(design);
    }
  });
  
  return card;
}

// HTML转义函数，防止XSS攻击
function escapeHtml(text) {
  if (!text) return '';
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

// 防抖函数，避免频繁触发请求
function debounce(fn, delay = 300) {
  let timeoutId;
  return function(...args) {
    const context = this;
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => fn.apply(context, args), delay);
  };
}

// 用户信息缓存，避免重复请求
const userInfoCache = {};

async function resolveUserNames(userIds = []) {
  const resultMap = {};
  const normalizedIds = Array.from(
    new Set(
      (userIds || [])
        .map(id => (id === null || id === undefined ? '' : String(id).trim()))
        .filter(Boolean)
    )
  );

  if (normalizedIds.length === 0) {
    return resultMap;
  }

  const idsToFetch = normalizedIds.filter(id => !userInfoCache[id]);

  if (idsToFetch.length > 0) {
    await Promise.all(
      idsToFetch.map(async (id) => {
        try {
          const response = await fetch(
            `${API_BASE_URL}/api/user_login_search?keyword=${encodeURIComponent(id)}&limit=1`
          );
          const data = await response.json();
          if (data.success && Array.isArray(data.data) && data.data.length > 0) {
            const record = data.data[0];
            userInfoCache[id] = record.login_name || record.login_id || id;
          } else {
            userInfoCache[id] = id;
          }
        } catch (error) {
          console.error('查询用户姓名失败:', id, error);
          userInfoCache[id] = id;
        }
      })
    );
  }

  normalizedIds.forEach(id => {
    resultMap[id] = userInfoCache[id] || id;
  });

  return resultMap;
}

// 初始化审批人自动联想输入
function initApproverAutocomplete({
  inputId,
  hiddenId,
  selectedListId,
  suggestionsId,
  maxSelection = 5
}) {
  const inputEl = document.getElementById(inputId);
  const hiddenEl = document.getElementById(hiddenId);
  const selectedListEl = document.getElementById(selectedListId);
  const suggestionsEl = document.getElementById(suggestionsId);

  if (!inputEl || !hiddenEl || !selectedListEl || !suggestionsEl) {
    return;
  }

  let selectedEntries = [];
  let currentKeyword = '';
  let lastRequestToken = 0;

  const updateHiddenValue = () => {
    hiddenEl.value = selectedEntries.map(item => item.login_id).join(',');
  };

  const hideSuggestions = () => {
    suggestionsEl.style.display = 'none';
    suggestionsEl.innerHTML = '';
  };

  const renderSelected = () => {
    selectedListEl.innerHTML = '';

    if (selectedEntries.length === 0) {
      selectedListEl.style.display = 'none';
      updateHiddenValue();
      return;
    }

    selectedListEl.style.display = 'flex';

    selectedEntries.forEach(entry => {
      const chip = document.createElement('span');
      chip.className = 'approver-chip';
      chip.style.display = 'inline-flex';
      chip.style.alignItems = 'center';
      chip.style.gap = '6px';
      chip.style.padding = '6px 10px';
      chip.style.borderRadius = '999px';
      chip.style.background = '#e0f2fe';
      chip.style.color = '#0369a1';
      chip.style.fontSize = '12px';
      chip.style.lineHeight = '1.2';
      chip.style.border = '1px solid #bae6fd';
      chip.style.userSelect = 'none';

      const textSpan = document.createElement('span');
      const displayName = entry.login_name ? `${entry.login_name} (${entry.login_id})` : entry.login_id;
      textSpan.textContent = displayName;
      chip.appendChild(textSpan);

      const removeBtn = document.createElement('button');
      removeBtn.type = 'button';
      removeBtn.textContent = '×';
      removeBtn.style.background = 'transparent';
      removeBtn.style.border = 'none';
      removeBtn.style.color = '#0f172a';
      removeBtn.style.cursor = 'pointer';
      removeBtn.style.fontSize = '14px';
      removeBtn.style.lineHeight = '1';
      removeBtn.style.padding = '0';
      removeBtn.style.marginLeft = '4px';
      removeBtn.setAttribute('aria-label', '移除审批人');

      removeBtn.addEventListener('click', () => {
        selectedEntries = selectedEntries.filter(item => item.login_id !== entry.login_id);
        renderSelected();
      });

      chip.appendChild(removeBtn);
      selectedListEl.appendChild(chip);
    });

    updateHiddenValue();
  };

  const appendSelection = (entry) => {
    if (!entry || !entry.login_id) {
      return;
    }

    if (selectedEntries.some(item => item.login_id === entry.login_id)) {
      hideSuggestions();
      inputEl.value = '';
      return;
    }

    if (selectedEntries.length >= maxSelection) {
      alert(`最多只能选择 ${maxSelection} 位审批人`);
      return;
    }

    selectedEntries.push({
      login_id: String(entry.login_id),
      login_name: entry.login_name || entry.login_id
    });
    renderSelected();
    hideSuggestions();
    inputEl.value = '';
    inputEl.focus();
  };

  const renderSuggestions = (items) => {
    suggestionsEl.innerHTML = '';
    if (!items || items.length === 0) {
      hideSuggestions();
      return;
    }

    items.forEach(item => {
      const option = document.createElement('div');
      option.style.padding = '10px 14px';
      option.style.cursor = 'pointer';
      option.style.display = 'flex';
      option.style.flexDirection = 'column';
      option.style.gap = '4px';
      option.style.fontSize = '13px';
      option.style.color = '#0f172a';
      option.style.borderBottom = '1px solid #e2e8f0';
      option.addEventListener('mouseenter', () => {
        option.style.background = '#f1f5f9';
      });
      option.addEventListener('mouseleave', () => {
        option.style.background = '#ffffff';
      });

      const nameLine = document.createElement('span');
      nameLine.style.fontWeight = '600';
      nameLine.textContent = item.login_name || '(未设置姓名)';

      const idLine = document.createElement('span');
      idLine.style.fontSize = '12px';
      idLine.style.color = '#475569';
      idLine.textContent = `工号: ${item.login_id || '-'}`;

      option.appendChild(nameLine);
      option.appendChild(idLine);

      option.addEventListener('click', () => appendSelection(item));
      suggestionsEl.appendChild(option);
    });

    suggestionsEl.lastElementChild?.style?.setProperty('border-bottom', 'none');
    suggestionsEl.style.display = 'block';
  };

  const fetchSuggestions = debounce(async (keyword, token) => {
    try {
      const response = await fetch(
        `${API_BASE_URL}/api/user_login_search?keyword=${encodeURIComponent(keyword)}&limit=10`
      );
      const result = await response.json();

      if (token !== lastRequestToken) {
        return; // 忽略过期的请求结果
      }

      if (result.success && Array.isArray(result.data)) {
        // 过滤已选中的人员
        const filtered = result.data.filter(item => !selectedEntries.some(sel => sel.login_id === item.login_id));
        renderSuggestions(filtered);
      } else {
        hideSuggestions();
      }
    } catch (error) {
      console.error('获取审批人联想数据失败:', error);
      hideSuggestions();
    }
  }, 250);

  inputEl.addEventListener('input', (event) => {
    const value = event.target.value.trim();
    currentKeyword = value;

    if (!value) {
      hideSuggestions();
      return;
    }

    lastRequestToken += 1;
    fetchSuggestions(value, lastRequestToken);
  });

  inputEl.addEventListener('keydown', (event) => {
    if (event.key === 'Enter') {
      event.preventDefault();
      const firstSuggestion = suggestionsEl.querySelector('div');
      if (firstSuggestion) {
        firstSuggestion.click();
        return;
      }

      const manualValue = inputEl.value.trim();
      if (!manualValue) {
        return;
      }

      // 允许手动输入工号
      const manualIdMatch = manualValue.match(/(\d{3,})$/);
      if (manualIdMatch) {
        appendSelection({
          login_id: manualIdMatch[1],
          login_name: manualValue.replace(/\(\d+\)$/, '').trim() || manualIdMatch[1]
        });
        return;
      }
    } else if (event.key === 'Escape') {
      hideSuggestions();
    }
  });

  inputEl.addEventListener('blur', () => {
    setTimeout(() => {
      hideSuggestions();
      inputEl.value = '';
    }, 200);
  });

  // 支持通过Backspace删除最后一位审批人
  inputEl.addEventListener('keydown', (event) => {
    if (event.key === 'Backspace' && inputEl.value === '' && selectedEntries.length > 0) {
      selectedEntries.pop();
      renderSelected();
      hideSuggestions();
    }
  });

  // 点击外部区域时隐藏下拉
  document.addEventListener('click', (event) => {
    if (!suggestionsEl.contains(event.target) && event.target !== inputEl) {
      hideSuggestions();
    }
  });

  renderSelected();
}

function initApproverInputs() {
  const configs = [
    {
      inputId: 'approver1ContactInput',
      hiddenId: 'approver1ContactIds',
      selectedListId: 'approver1SelectedList',
      suggestionsId: 'approver1Suggestions'
    },
    {
      inputId: 'approver2ContactInput',
      hiddenId: 'approver2ContactIds',
      selectedListId: 'approver2SelectedList',
      suggestionsId: 'approver2Suggestions'
    }
  ];

  configs.forEach(config => initApproverAutocomplete(config));
}

// ==================== 初始化筛选和搜索功能 ====================
function initFilterAndSearch() {
  // 搜索功能
  const searchInput = document.querySelector('.search-input');
  if (searchInput) {
    // 重新绑定搜索事件
    searchInput.addEventListener('input', function(e) {
      // 使用统一的筛选函数
      applyFilters();
    });
  }
  
  // 状态筛选功能
  const statusFilters = document.querySelectorAll('.filter-bar .filter-tags .filter-tag');
  statusFilters.forEach((filter) => {
    // 移除旧的事件监听器，重新绑定
    const newFilter = filter.cloneNode(true);
    filter.parentNode.replaceChild(newFilter, filter);
    
    newFilter.addEventListener('click', function() {
      // 移除所有active状态
      const allFilters = document.querySelectorAll('.filter-bar .filter-tags .filter-tag');
      allFilters.forEach(f => f.classList.remove('active'));
      // 添加当前active状态
      this.classList.add('active');
      
      console.log('点击筛选标签:', this.textContent.trim(), '状态码:', this.getAttribute('data-status'));
      
      // 应用筛选（会同时考虑搜索关键词）
      applyFilters();
    });
  });
  
  console.log('筛选和搜索功能已初始化，找到', statusFilters.length, '个筛选标签');
}

// 页面加载时初始化用户界面
document.addEventListener('DOMContentLoaded', function() {
  initUserInterface();
  // 初始化筛选和搜索功能
  initFilterAndSearch();
  // 初始化侧边栏加号按钮
  initSidebarAddButton();
  // 初始化审批人联想输入
  initApproverInputs();
  // 注意：
  // 1. 如果用户已登录（从localStorage恢复），initUserInterface 会调用 showDesignListView()，内部会加载数据
  // 2. 如果用户未登录，等待登录成功消息，登录成功后会调用 showDesignListView()，内部会加载数据
  // 所以这里不需要额外加载数据，避免重复查询
});

// 应用筛选和搜索的通用函数
function applyFilters() {
  const activeFilter = document.querySelector('.filter-bar .filter-tags .filter-tag.active');
  const filterStatus = activeFilter ? activeFilter.getAttribute('data-status') : 'all';
  const searchTerm = document.querySelector('.search-input')?.value.toLowerCase() || '';
  const cards = document.querySelectorAll('.design-card');
  
  if (cards.length === 0) {
    console.log('没有找到卡片，跳过筛选');
    return;
  }
  
  // 获取时间段筛选条件
  const dateRange = window.currentFilterDateRange || null;
  // 获取instance_code筛选条件
  const instanceCodeFilter = window.currentFilterInstanceCode || '';
  
  console.log('应用筛选:', {
    filterStatus: filterStatus,
    searchTerm: searchTerm,
    dateRange: dateRange ? {
      startDate: dateRange.startDate ? dateRange.startDate.toISOString() : '无限制',
      endDate: dateRange.endDate ? dateRange.endDate.toISOString() : '无限制'
    } : '无限制',
    instanceCodeFilter: instanceCodeFilter || '无限制',
    cardCount: cards.length,
    activeFilterText: activeFilter ? activeFilter.textContent.trim() : 'none'
  });
  
  let visibleCount = 0;
  let draftCount = 0;
  let pendingCount = 0;
  let pushedCount = 0;
  let failedCount = 0;
  let discardedCount = 0;
  
  cards.forEach(card => {
    const cardStatus = card.getAttribute('data-status') || '';
    const title = card.querySelector('.card-title')?.textContent.toLowerCase() || '';
    const desc = card.querySelector('.card-desc')?.textContent.toLowerCase() || '';
    
    // 统计各状态数量
    if (cardStatus === 'DRAFT') draftCount++;
    else if (cardStatus === 'PENDING') pendingCount++;
    else if (cardStatus === 'PUSHED') pushedCount++;
    else if (cardStatus === 'FAILED') failedCount++;
    else if (cardStatus === 'DISCARDED') discardedCount++;
    
    // 检查状态筛选（状态码必须完全匹配，不区分大小写）
    const matchesFilter = (filterStatus === 'all') || (cardStatus.toUpperCase() === filterStatus.toUpperCase());
    
    // 检查搜索关键词
    const matchesSearch = !searchTerm || title.includes(searchTerm) || desc.includes(searchTerm);
    
    // 检查时间段筛选
    let matchesDateRange = true;
    if (dateRange && (dateRange.startDate || dateRange.endDate)) {
      // 从卡片的日期信息中获取日期
      const cardDateText = card.querySelector('.card-date')?.textContent || '';
      // 尝试从日期文本中提取日期（格式：更新时间: 2024-11-04 14:30:00）
      const dateMatch = cardDateText.match(/(\d{4}-\d{2}-\d{2})/);
      if (dateMatch) {
        const cardDate = new Date(dateMatch[1]);
        cardDate.setHours(0, 0, 0, 0);
        
        if (dateRange.startDate && cardDate < dateRange.startDate) {
          matchesDateRange = false;
        }
        if (dateRange.endDate && cardDate > dateRange.endDate) {
          matchesDateRange = false;
        }
      } else {
        // 如果无法解析日期，尝试从data属性获取
        const cardDateAttr = card.getAttribute('data-date');
        if (cardDateAttr) {
          const cardDate = new Date(cardDateAttr);
          if (!isNaN(cardDate.getTime())) {
            cardDate.setHours(0, 0, 0, 0);
            if (dateRange.startDate && cardDate < dateRange.startDate) {
              matchesDateRange = false;
            }
            if (dateRange.endDate && cardDate > dateRange.endDate) {
              matchesDateRange = false;
            }
          }
        }
      }
    }
    
    // 检查instance_code筛选
    let matchesInstanceCode = true;
    if (instanceCodeFilter) {
      const cardInstanceCode = card.getAttribute('data-instance-code') || '';
      if (!cardInstanceCode.toLowerCase().includes(instanceCodeFilter.toLowerCase())) {
        matchesInstanceCode = false;
      }
    }
    
    // 同时满足筛选、搜索、时间段和instance_code条件才显示
    if (matchesFilter && matchesSearch && matchesDateRange && matchesInstanceCode) {
      card.style.display = 'block';
      visibleCount++;
    } else {
      card.style.display = 'none';
    }
  });
  
  console.log(`筛选完成，显示 ${visibleCount} / ${cards.length} 个卡片`);
  console.log(`状态统计: DRAFT=${draftCount}, PENDING=${pendingCount}, PUSHED=${pushedCount}, FAILED=${failedCount}, DISCARDED=${discardedCount}`);
}

// 类型筛选功能
const typeFilters = document.querySelectorAll('.filter-bar .filter-tags:last-of-type .filter-tag');
typeFilters.forEach(filter => {
  filter.addEventListener('click', function() {
    // 移除所有active状态
    typeFilters.forEach(f => f.classList.remove('active'));
    // 添加当前active状态
    this.classList.add('active');
    
    const filterText = this.textContent.trim();
    const cards = document.querySelectorAll('.design-card');
    
    cards.forEach(card => {
      const title = card.querySelector('.card-title').textContent;
      
      if (filterText === '全部') {
        card.style.display = 'block';
      } else if (filterText === '新建' && title.includes('产品设计')) {
        card.style.display = 'block';
      } else if (filterText === '差异' && title.includes('差异分析')) {
        card.style.display = 'block';
      } else if (filterText === '更新' && (title.includes('更新') || title.includes('模块'))) {
        card.style.display = 'block';
      } else {
        card.style.display = 'none';
      }
    });
  });
});

// 视图切换
const designListView = document.getElementById('designListView');
const newDesignView = document.getElementById('newDesignView');
const designDetailView = document.getElementById('designDetailView');

// 初始化侧边栏加号按钮
function initSidebarAddButton() {
  const sidebarAddBtn = document.getElementById('sidebarAddBtn');
  if (sidebarAddBtn) {
    sidebarAddBtn.addEventListener('click', function(e) {
      e.stopPropagation(); // 防止事件冒泡
      console.log('点击添加导航项按钮');
      // TODO: 后续实现添加导航项的功能
      // 可以打开一个弹窗让用户输入新的导航项信息
      handleAddSidebarItem();
    });
  }
}

// 处理添加导航项（预留函数，后续实现）
function handleAddSidebarItem() {
  console.log('添加导航项功能待实现');
  // 这里可以打开一个弹窗，让用户输入：
  // - 导航项名称
  // - 图标（可选）
  // - 关联的视图或功能
  alert('添加导航项功能开发中...');
}

// 侧边栏导航切换
const sidebarItems = document.querySelectorAll('.sidebar-item');
sidebarItems.forEach(item => {
  item.addEventListener('click', function() {
    // 移除所有active状态
    sidebarItems.forEach(i => i.classList.remove('active'));
    // 添加当前active状态
    this.classList.add('active');
    
    const itemText = this.textContent.trim();
    console.log('切换到:', itemText);
    
    // 根据点击的项目切换视图
    if (itemText.includes('新建设计')) {
      showNewDesignView();
    } else if (itemText.includes('设计详情')) {
      // 显示设计详情视图
      showDesignDetailView();
    } else if (itemText.includes('小惟推荐')) {
      showRecommendationView();
    } else {
      showDesignListView();
    }
  });
});

// 重置新建设计的所有状态
function resetNewDesignState() {
  // 重置所有状态变量
  uploadedFiles = [];
  currentUploadDir = null;
  currentProcessResult = null;
  
  // 重置文件输入框
  if (fileInput) fileInput.value = '';
  
  // 重置文件列表显示
  renderFileList();
  
  // 更新处理按钮状态
  updateProcessButton();
  
  // 更新上传目录显示
  updateUploadDirDisplay();
  
  // 重置审批按钮状态（如果存在）
  const detailApprovalBtn = document.getElementById('detailApprovalBtn');
  if (detailApprovalBtn) {
    detailApprovalBtn.disabled = false;
    detailApprovalBtn.classList.remove('btn-success');
    detailApprovalBtn.classList.add('btn-primary');
    detailApprovalBtn.innerHTML = `
      <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
        <path d="M3 8h7M10 5l3 3-3 3" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
      发起审批
    `;
  }
  
  console.log('已重置新建设计状态');
}

function showNewDesignView() {
  // 重置状态
  resetNewDesignState();
  
  designListView.style.display = 'none';
  newDesignView.style.display = 'block';
  if (designDetailView) designDetailView.style.display = 'none';
  const recommendationView = document.getElementById('recommendationView');
  if (recommendationView) recommendationView.style.display = 'none';

  const searchActionBar = document.getElementById('searchActionBar');
  if (searchActionBar) {
    searchActionBar.style.display = 'none';
  }

  // 隐藏输入框，显示原标题
  const mainTitle = document.getElementById('mainTitle');
  const detailTitleContainer = document.getElementById('detailTitleContainer');
  const detailTitleInput = document.getElementById('detailTitleInput');
  if (mainTitle) {
    mainTitle.style.display = 'block';
    mainTitle.textContent = '新建设计 - 文件上传';
  }
  if (detailTitleContainer) {
    detailTitleContainer.style.display = 'none';
  }
  if (detailTitleInput) {
    detailTitleInput.value = '';
  }
  
  // 启用全局粘贴功能
  enableGlobalPaste();
}

// 更新设计详情视图，使用实际处理结果数据
function updateDesignDetailView(processResult) {
  if (!processResult || !processResult.json_files || processResult.json_files.length === 0) {
    console.warn('没有JSON文件数据');
    return;
  }

  // 获取所有JSON文件（显示所有生成的JSON文件作为页签）
  const jsonFiles = processResult.json_files || [];
  
  // 显示所有JSON文件，不进行筛选
  const targetJsonFiles = jsonFiles;
  
  console.log('JSON文件列表:', targetJsonFiles);
  console.log('JSON文件数量:', targetJsonFiles.length);

  const tabsList = document.querySelector('.tabs-list');
  const detailContentSection = document.querySelector('.detail-content-section');
  
  if (!tabsList || !detailContentSection) {
    console.error('找不到页签或内容区域');
    return;
  }

  // 清空现有内容
  tabsList.innerHTML = '';
  detailContentSection.innerHTML = '';

  // 存储第一个页签的型号名称
  let firstTabModelName = '';

  // 为每个JSON文件生成页签和内容
  targetJsonFiles.forEach((jsonFile, index) => {
    // 从文件路径提取文件名（支持正斜杠和反斜杠）
    // 统一将反斜杠替换为正斜杠，然后提取最后一个路径部分
    const normalizedPath = jsonFile.replace(/\\/g, '/');
    const fileName = normalizedPath.split('/').pop().replace('.json', '');
    let modelName = fileName;
    
    // 尝试从文件名提取型号（去掉类型后缀）
    // 匹配格式：型号_DIFF.json, 型号_PLM.json, 型号_GBOM.json, 型号_to_型号_DIFF.json
    const typeMatch = fileName.match(/^(.+?)_(DIFF|PLM|GBOM)$/);
    const diffToMatch = fileName.match(/^(.+?)_to_(.+?)_DIFF$/);
    
    if (diffToMatch) {
      // 格式：SP0030-00-23-5QP_to_SP0030-3Q-23-5QP_DIFF
      // 显示目标型号
      modelName = diffToMatch[2];
    } else if (typeMatch) {
      // 格式：SP0030-3Q-23-5QP_DIFF
      modelName = typeMatch[1];
    }
    
    // 保存第一个页签的型号名称
    if (index === 0) {
      firstTabModelName = modelName;
    }
    
    // 确定文件类型和状态
    let fileType = 'UNKNOWN';
    let statusClass = 'status-draft';
    if (fileName.includes('_DIFF')) {
      fileType = 'DIFF';
      statusClass = 'status-review';
    } else if (fileName.includes('_PLM')) {
      fileType = 'PLM';
      statusClass = 'status-approved';
    } else if (fileName.includes('_GBOM')) {
      fileType = 'GBOM';
      statusClass = 'status-approved';
    }

    const tabId = `tab_${index}`;

    // 创建页签
    const tabItem = document.createElement('button');
    tabItem.className = `tab-item ${index === 0 ? 'active' : ''}`;
    tabItem.setAttribute('data-tab', tabId);
    tabItem.innerHTML = `
      <div class="tab-status ${statusClass}"></div>
      <span>${modelName}</span>
    `;
    tabsList.appendChild(tabItem);

    // 创建内容区域
    const tabContent = document.createElement('div');
    tabContent.className = `tab-content ${index === 0 ? 'active' : ''}`;
    tabContent.setAttribute('data-content', tabId);
    
    // 生成BOM表格内容
    tabContent.innerHTML = generateBOMContentFromJson(jsonFile, modelName, fileType, tabId);
    
    detailContentSection.appendChild(tabContent);
  });

  // 更新页签点击事件
  setupTabEvents();

  // 更新标题和元数据
  if (targetJsonFiles.length > 0) {
    // 统一处理路径分隔符（支持正斜杠和反斜杠）
    const normalizedFirstPath = targetJsonFiles[0].replace(/\\/g, '/');
    const firstFileName = normalizedFirstPath.split('/').pop().replace('.json', '');
    const firstModelName = firstFileName.split('_')[0];
    updateDetailHeaderFromJson(firstModelName, processResult);
  }

  // 自动生成标题并设置到输入框（放在最后，确保不被其他函数覆盖）
  if (targetJsonFiles.length > 0 && firstTabModelName) {
    const tabCount = targetJsonFiles.length;
    const generatedTitle = `${firstTabModelName}共${tabCount}个BOM设计申请`;
    
    // 设置到标题输入框
    const detailTitleInput = document.getElementById('detailTitleInput');
    if (detailTitleInput) {
      detailTitleInput.value = generatedTitle;
      console.log('已自动生成标题:', generatedTitle);
    }
  }
}

// 从JSON文件生成BOM内容
function generateBOMContentFromJson(jsonFilePath, modelName, fileType, tabId) {
  // 显示加载提示并异步加载数据
  const bomTableHTML = `
    <div class="bom-loading" id="bom-loading-${tabId}">
      <p>正在加载BOM数据...</p>
    </div>
    <div class="bom-detail-table" id="bom-table-${tabId}" style="display: none;">
      <!-- BOM表格将通过JavaScript动态生成 -->
    </div>
  `;

  // 异步加载BOM数据
  loadBOMData(jsonFilePath, tabId);

  return `
    <div class="category-filters" id="category-filters-${tabId}">
      <button class="category-btn active" data-category="all">全部</button>
    </div>
    ${bomTableHTML}
  `;
}

// 显示加载错误信息
function showBOMLoadError(tabId, errorMessage) {
  const loadingEl = document.getElementById(`bom-loading-${tabId}`);
  if (loadingEl) {
    loadingEl.innerHTML = `<p style="color: #ff4d4f;">加载失败: ${errorMessage}</p>`;
  }
}

// 获取JSON文件数据
async function fetchBOMJsonData(jsonFilePath) {
  const response = await fetch(`${API_BASE_URL}/api/get_json_file?file_path=${encodeURIComponent(jsonFilePath)}`);
  if (!response.ok) {
    throw new Error(`HTTP错误: ${response.status}`);
  }
  return await response.json();
}

// 加载BOM数据
async function loadBOMData(jsonFilePath, tabId) {
  try {
    const result = await fetchBOMJsonData(jsonFilePath);
    
    if (result.success && result.data) {
      renderBOMTable(result.data, tabId);
    } else {
      showBOMLoadError(tabId, result.error || '未知错误');
    }
  } catch (error) {
    console.error(`加载BOM数据失败 (${tabId}):`, error);
    showBOMLoadError(tabId, error.message);
  }
}

// 渲染BOM表格（支持MPART格式）
function renderBOMTable(bomData, tabId) {
  const tableContainer = document.getElementById(`bom-table-${tabId}`);
  const loadingEl = document.getElementById(`bom-loading-${tabId}`);
  const categoryFilters = document.getElementById(`category-filters-${tabId}`);
  
  if (!tableContainer) {
    console.error(`找不到表格容器: bom-table-${tabId}`);
    return;
  }
  
  console.log(`开始渲染BOM表格 (${tabId}):`, bomData);

  // 解析BOM数据结构
  let allParts = [];
  let categories = {};
  
  // 检查数据结构 - 支持MPART格式
  if (bomData.MPART) {
    // MPART格式：按类别分组的物料
    Object.keys(bomData.MPART).forEach(categoryId => {
      const categoryParts = bomData.MPART[categoryId];
      if (Array.isArray(categoryParts)) {
        // 扁平化处理，提取所有层级的物料
        const flattenParts = flattenMPARTParts(categoryParts, categoryId);
        categories[categoryId] = {
          id: categoryId,
          name: getCategoryName(categoryId),
          parts: flattenParts,
          count: flattenParts.length
        };
        allParts = allParts.concat(flattenParts);
      }
    });
  } else if (bomData.bom_data) {
    // 标准格式：有bom_data字段
    Object.keys(bomData.bom_data).forEach(categoryId => {
      const category = bomData.bom_data[categoryId];
      if (category.parts && Array.isArray(category.parts)) {
        categories[categoryId] = {
          id: categoryId,
          name: category.category_name || getCategoryName(categoryId),
          parts: category.parts,
          count: category.parts.length
        };
        allParts = allParts.concat(category.parts);
      }
    });
  } else if (Array.isArray(bomData)) {
    // 数组格式
    allParts = bomData;
    categories['all'] = {
      id: 'all',
      name: '全部',
      parts: allParts,
      count: allParts.length
    };
  } else if (bomData.parts && Array.isArray(bomData.parts)) {
    // 有parts字段
    allParts = bomData.parts;
    categories['all'] = {
      id: 'all',
      name: '全部',
      parts: allParts,
      count: allParts.length
    };
  }

  if (allParts.length === 0) {
    tableContainer.innerHTML = '<p>暂无BOM数据</p>';
    if (loadingEl) loadingEl.style.display = 'none';
    tableContainer.style.display = 'flex'; // 保持flex布局
    return;
  }

  // 更新分类筛选按钮
  if (categoryFilters && Object.keys(categories).length > 0) {
    let filterHTML = '<button class="category-btn active" data-category="all">全部 (' + allParts.length + ')</button>';
    Object.values(categories).forEach(category => {
      if (category.id !== 'all') {
        filterHTML += `<button class="category-btn" data-category="${category.id}">${category.name} (${category.count})</button>`;
      }
    });
    categoryFilters.innerHTML = filterHTML;
    
    // 绑定分类筛选事件
    setupCategoryFilters(tabId, categories, allParts);
  }

  // 生成表格HTML
  console.log(`渲染表格内容，物料数量: ${allParts.length}`);
  renderBOMTableContent(tableContainer, allParts, tabId);

  if (loadingEl) loadingEl.style.display = 'none';
  tableContainer.style.display = 'flex'; // 保持flex布局，与CSS一致
  
  // 设置固定高度
  setFixedTableHeight(tabId);
}

// 扁平化MPART物料（仅处理当前层级，不递归处理children）
function flattenMPARTParts(parts, categoryId, level = 0) {
  return parts.map(part => ({
    part_code: part['MPART.NO'] || part['MPART_NO'] || '-',
    part_name: part['MPART.NAME'] || part['MPART_NAME'] || '-',
    quantity: part['MPART.BNUM'] || part['MPART_BNUM'] || 1,
    unit: 'PCS',
    part_type: part['MPART.MFG'] || part['MPART_MFG'] || '未知',
    category_id: categoryId,
    level: level,
    part_id: part['MPART.ID'] || part['MPART_ID'] || 0
  }));
}

// 获取类别名称
function getCategoryName(categoryId) {
  const categoryNames = {
    '223': '电子元件',
    '275': '线材',
    '311': 'PCBA组件',
    '334': '组装件',
    '500': '钣金件',
    '532': '标签类',
    '536': '包装材料'
  };
  return categoryNames[categoryId] || `类别${categoryId}`;
}

// 渲染BOM表格内容
function renderBOMTableContent(container, parts, tabId) {
  if (!container) {
    console.error(`容器不存在，无法渲染表格 (${tabId})`);
    return;
  }
  
  if (!parts || parts.length === 0) {
    console.warn(`物料列表为空 (${tabId})`);
    container.innerHTML = '<p>暂无BOM数据</p>';
    return;
  }
  
  console.log(`生成表格HTML，物料数量: ${parts.length}`);
  
  let tableHTML = `
    <table class="bom-table" id="bom-table-content-${tabId}">
      <thead>
        <tr>
          <th>序号</th>
          <th>物料编码</th>
          <th>物料名称</th>
          <th>数量</th>
          <th>单位</th>
          <th>物料属性</th>
          <th>类别</th>
        </tr>
      </thead>
      <tbody>
  `;

  parts.forEach((part, index) => {
    const partCode = part.part_code || part['MPART.NO'] || part.material_code || part.code || '-';
    const partName = part.part_name || part['MPART.NAME'] || part.material_name || part.name || '-';
    const quantity = part.quantity || part['MPART.BNUM'] || part.qty || part.count || '-';
    const unit = part.unit || 'PCS';
    const partType = part.part_type || part['MPART.MFG'] || part.material_type || '未知';
    const categoryId = part.category_id || '-';
    const categoryName = getCategoryName(categoryId);
    const level = part.level || 0;
    
    // 根据物料属性设置badge颜色
    let badgeClass = 'badge badge-blue';
    if (partType.includes('自制') || partType.includes('自产') || partType === '') {
      badgeClass = 'badge badge-green';
    }
    
    // 根据层级添加缩进
    const indentStyle = level > 0 ? `padding-left: ${level * 20}px;` : '';
    const indentIcon = level > 0 ? '└ ' : '';

    tableHTML += `
      <tr data-category="${categoryId}" data-level="${level}">
        <td>${index + 1}</td>
        <td style="${indentStyle}">${indentIcon}${partCode}</td>
        <td>${partName}</td>
        <td>${quantity}</td>
        <td>${unit}</td>
        <td><span class="${badgeClass}">${partType || '未知'}</span></td>
        <td>${categoryName}</td>
      </tr>
    `;
  });

  tableHTML += `
      </tbody>
    </table>
  `;

  container.innerHTML = tableHTML;
  console.log(`表格HTML已设置到容器 (${tabId})，HTML长度: ${tableHTML.length}`);
  
  // 验证表格是否真的被添加到了DOM中
  const table = container.querySelector('.bom-table');
  if (table) {
    console.log(`表格已成功添加到DOM (${tabId})`);
  } else {
    console.error(`表格未能添加到DOM (${tabId})`);
  }
}

// 设置表格容器固定高度（使用视口高度百分比）
function setFixedTableHeight(tabId) {
  const tableContainer = document.getElementById(`bom-table-${tabId}`);
  if (!tableContainer) {
    console.warn(`设置高度：找不到表格容器 (${tabId})`);
    return;
  }
  
  // 使用视口高度的60%作为表格高度
  const FIXED_HEIGHT = '30vh';
  
  // 强制设置高度，防止被 flex 布局压缩
  tableContainer.style.height = FIXED_HEIGHT;
  tableContainer.style.maxHeight = FIXED_HEIGHT;
  tableContainer.style.minHeight = FIXED_HEIGHT;
  tableContainer.style.flexShrink = '0'; // 防止被压缩
  tableContainer.style.flexGrow = '0'; // 防止被拉伸
  tableContainer.style.overflowY = 'auto'; // 确保可以滚动
}

// 设置分类筛选功能
function setupCategoryFilters(tabId, categories, allParts) {
  const filterButtons = document.querySelectorAll(`#category-filters-${tabId} .category-btn`);
  const table = document.getElementById(`bom-table-content-${tabId}`);
  
  if (!table) return;
  
  filterButtons.forEach(button => {
    button.addEventListener('click', function() {
      const category = this.getAttribute('data-category');
      
      // 更新按钮状态
      filterButtons.forEach(btn => btn.classList.remove('active'));
      this.classList.add('active');
      
      // 筛选表格行
      const rows = table.querySelectorAll('tbody tr');
      rows.forEach(row => {
        const rowCategory = row.getAttribute('data-category');
        if (category === 'all' || rowCategory === category) {
          row.style.display = '';
        } else {
          row.style.display = 'none';
        }
      });
    });
  });
}

// 更新详情头部信息（从JSON文件名）
function updateDetailHeaderFromJson(modelName, processResult) {
  // 注意：标题现在由输入框管理，不再在这里设置
  // const detailTitle = document.querySelector('.detail-title');
  const detailMeta = document.querySelector('.detail-meta');
  
  // 标题已改为输入框，由 updateDesignDetailView 函数自动生成
  // if (detailTitle) {
  //   detailTitle.textContent = `${modelName} 及相关设计`;
  // }
  
  if (detailMeta) {
    const totalFiles = processResult.total_files || 0;
    const successCount = processResult.success_count || 0;
    const jsonFileCount = processResult.json_files ? processResult.json_files.length : 0;
    const now = new Date();
    const timeStr = now.toLocaleString('zh-CN');
    
    detailMeta.innerHTML = `
      <span>处理文件: <strong>${successCount}/${totalFiles}</strong></span>
      <span>JSON文件: <strong>${jsonFileCount}</strong></span>
      <span>创建人: <strong>${currentUserName || '未知'}</strong></span>
      <span>创建时间: <strong>${timeStr}</strong></span>
    `;
  }
}

// 设置页签事件
function setupTabEvents() {
  const tabItems = document.querySelectorAll('.tab-item');
  const tabContents = document.querySelectorAll('.tab-content');

  tabItems.forEach(tab => {
    tab.addEventListener('click', function() {
      const targetTab = this.getAttribute('data-tab');
      
      // 移除所有active状态
      tabItems.forEach(t => t.classList.remove('active'));
      tabContents.forEach(c => c.classList.remove('active'));
      
      // 添加当前active状态
      this.classList.add('active');
      const targetContent = document.querySelector(`[data-content="${targetTab}"]`);
      if (targetContent) {
        targetContent.classList.add('active');
        
        // 切换tab后设置固定高度
        setFixedTableHeight(targetTab);
      }
    });
  });
}

function showDesignDetailView(designData = null) {
  designListView.style.display = 'none';
  newDesignView.style.display = 'none';
  if (designDetailView) designDetailView.style.display = 'block';
  const recommendationView = document.getElementById('recommendationView');
  if (recommendationView) recommendationView.style.display = 'none';
  
  // 禁用全局粘贴功能
  disableGlobalPaste();
  
  // 显示输入框，隐藏原标题
  const mainTitle = document.getElementById('mainTitle');
  const detailTitleContainer = document.getElementById('detailTitleContainer');
  const detailTitleInput = document.getElementById('detailTitleInput');
  if (mainTitle) {
    mainTitle.style.display = 'none';
  }
  if (detailTitleContainer) {
    detailTitleContainer.style.display = 'flex';
  }
  if (detailTitleInput) {
    // 如果有设计数据，更新输入框的值
    if (designData && designData.title) {
      detailTitleInput.value = designData.title;
    } else if (designData && designData.design_name) {
      detailTitleInput.value = designData.design_name;
    }
  }

  // 隐藏搜索栏
  const searchActionBar = document.getElementById('searchActionBar');
  if (searchActionBar) {
    searchActionBar.style.display = 'none';
  }
  
  // 如果有设计数据，更新详情视图
  if (designData) {
    updateDesignDetailFromCard(designData);
  }
}

// 从卡片加载设计详情
function loadDesignDetailFromCard(design) {
  console.log('从卡片加载设计详情:', design);
  
  // 解析design_info获取json_files和output_dir
  let designInfo = {};
  let jsonFiles = [];
  let outputDir = null;
  
  if (design.design_info) {
    try {
      designInfo = typeof design.design_info === 'string' 
        ? JSON.parse(design.design_info) 
        : design.design_info;
      
      // 从design_info中提取json_files和output_dir
      jsonFiles = designInfo.json_files || [];
      outputDir = designInfo.output_dir || null;
      
      console.log('解析design_info:', {
        jsonFilesCount: jsonFiles.length,
        outputDir: outputDir,
        designInfo: designInfo
      });
    } catch (e) {
      console.error('解析design_info失败:', e);
    }
  }
  
  // 如果没有json_files，尝试从bom_path获取文件列表
  if (jsonFiles.length === 0 && design.bom_path) {
    console.log('尝试从bom_path获取文件列表:', design.bom_path);
    // 可以在这里调用API获取文件列表
    // 暂时使用bom_path作为output_dir
    outputDir = design.bom_path;
  }
  
  // 确保json_files路径是完整的（如果output_dir存在，且路径是相对的）
  let processedJsonFiles = jsonFiles;
  if (outputDir && jsonFiles.length > 0) {
    processedJsonFiles = jsonFiles.map(filePath => {
      // 如果路径已经是绝对路径，直接返回
      if (filePath.startsWith('/') || filePath.match(/^[A-Za-z]:/)) {
        return filePath;
      }
      // 如果路径是相对的，基于output_dir构建完整路径
      // 统一使用正斜杠
      const normalizedOutputDir = outputDir.replace(/\\/g, '/');
      const normalizedFilePath = filePath.replace(/\\/g, '/');
      
      // 如果文件路径已经包含output_dir，直接返回
      if (normalizedFilePath.includes(normalizedOutputDir)) {
        return normalizedFilePath;
      }
      
      // 否则拼接路径
      return `${normalizedOutputDir}/${normalizedFilePath}`.replace(/\/+/g, '/');
    });
  }
  
  // 构建processResult格式的数据
  const processResult = {
    design_id: design.design_id,
    json_files: processedJsonFiles,
    output_dir: outputDir || design.bom_path || null,
    worker_id: designInfo.worker_id || currentUserId,
    total_files: designInfo.total_files || 0,
    success_count: designInfo.success_count || 0,
    json_file_count: processedJsonFiles.length,
    process_time: designInfo.process_time || design.date
  };
  
  console.log('构建processResult:', {
    design_id: processResult.design_id,
    json_files_count: processResult.json_files.length,
    output_dir: processResult.output_dir,
    json_files: processResult.json_files
  });
  
  // 保存当前设计数据
  window.currentDesignData = design;
  window.currentProcessResult = processResult;
  
  // 跳转到详情页面
  showDesignDetailView(design);
}

// 更新设计详情视图（从卡片数据）
function updateDesignDetailFromCard(design) {
  const processResult = window.currentProcessResult;
  
  if (!processResult || !processResult.json_files || processResult.json_files.length === 0) {
    console.warn('没有JSON文件数据，显示空状态');
    
    // 显示空状态提示
    const tabsList = document.querySelector('.tabs-list');
    const detailContentSection = document.querySelector('.detail-content-section');
    
    if (tabsList && detailContentSection) {
      tabsList.innerHTML = '';
      detailContentSection.innerHTML = `
        <div style="text-align: center; padding: 60px 20px; color: #999;">
          <div style="font-size: 48px; margin-bottom: 16px;">📋</div>
          <div style="font-size: 16px; margin-bottom: 8px;">暂无BOM数据</div>
          <div style="font-size: 14px; color: #ccc;">该设计尚未生成BOM文件</div>
        </div>
      `;
    }
    
    // 更新详情页头部信息
    updateDetailHeaderFromDesign(design);
    return;
  }
  
  // 使用现有的updateDesignDetailView函数
  updateDesignDetailView(processResult);
  
  // 更新详情页头部信息
  updateDetailHeaderFromDesign(design);
}

// 从设计数据更新详情页头部
function updateDetailHeaderFromDesign(design) {
  // 更新标题输入框
  const detailTitleInput = document.getElementById('detailTitleInput');
  if (detailTitleInput && design.title) {
    detailTitleInput.value = design.title;
  }
  
  // 可以在这里更新其他元数据，比如设计ID、创建时间等
  console.log('更新详情页头部信息:', design);
}

function showDesignListView() {
  designListView.style.display = 'block';
  newDesignView.style.display = 'none';
  if (designDetailView) designDetailView.style.display = 'none';
  const recommendationView = document.getElementById('recommendationView');
  if (recommendationView) recommendationView.style.display = 'none';
  
  // 禁用全局粘贴功能
  disableGlobalPaste();
  
  // 隐藏输入框，显示原标题
  const mainTitle = document.getElementById('mainTitle');
  const detailTitleContainer = document.getElementById('detailTitleContainer');
  const detailTitleInput = document.getElementById('detailTitleInput');
  if (mainTitle) {
    mainTitle.style.display = 'block';
    mainTitle.textContent = '设计项目管理';
  }
  if (detailTitleContainer) {
    detailTitleContainer.style.display = 'none';
  }
  if (detailTitleInput) {
    detailTitleInput.value = '';
  }

  // 显示搜索栏
  const searchActionBar = document.getElementById('searchActionBar');
  if (searchActionBar) {
    searchActionBar.style.display = 'flex';
  }
  
  // 每次切换到全部设计视图时都重新查询，确保数据同步
  if (currentUserId) {
    console.log('切换到全部设计视图，重新加载数据以确保同步');
    loadUserDesigns(currentUserId);
  }
}

// 显示小惟推荐视图
function showRecommendationView() {
  designListView.style.display = 'none';
  newDesignView.style.display = 'none';
  if (designDetailView) designDetailView.style.display = 'none';
  const recommendationView = document.getElementById('recommendationView');
  if (recommendationView) recommendationView.style.display = 'block';
  
  // 禁用全局粘贴功能
  disableGlobalPaste();
  
  // 隐藏输入框，显示原标题
  const mainTitle = document.getElementById('mainTitle');
  const detailTitleContainer = document.getElementById('detailTitleContainer');
  const detailTitleInput = document.getElementById('detailTitleInput');
  if (mainTitle) {
    mainTitle.style.display = 'block';
    mainTitle.textContent = '小惟推荐';
  }
  if (detailTitleContainer) {
    detailTitleContainer.style.display = 'none';
  }
  if (detailTitleInput) {
    detailTitleInput.value = '';
  }

  // 隐藏搜索栏
  const searchActionBar = document.getElementById('searchActionBar');
  if (searchActionBar) {
    searchActionBar.style.display = 'none';
  }
  
  // 检查右侧边栏是否折叠，如果折叠则展开
  const rightSidebar = document.getElementById('rightSidebar');
  const floatingToggle = document.getElementById('floatingToggle');
  
  if (rightSidebar && floatingToggle) {
    // 检查是否处于折叠状态
    const isCollapsed = rightSidebar.classList.contains('collapsed');
    const isFloatingVisible = window.getComputedStyle(floatingToggle).display !== 'none';
    
    if (isCollapsed || isFloatingVisible) {
      console.log('右侧边栏处于折叠状态，正在展开...');
      // 确保右侧栏显示
      rightSidebar.style.display = 'block';
      // 移除折叠状态
      rightSidebar.classList.remove('collapsed');
      // 隐藏悬浮按钮
      floatingToggle.style.display = 'none';
      console.log('右侧边栏已展开');
    }
  }
  
  console.log('已切换到小惟推荐视图');
}

// 顶部导航切换
const topNavItems = document.querySelectorAll('.top-nav-item');
topNavItems.forEach(item => {
  item.addEventListener('click', function() {
    // 移除所有active状态
    topNavItems.forEach(i => i.classList.remove('active'));
    // 添加当前active状态
    this.classList.add('active');
    
    console.log('切换到:', this.textContent.trim());
  });
});

// 卡片点击事件
const designCards = document.querySelectorAll('.design-card');
designCards.forEach(card => {
  card.addEventListener('click', function(e) {
    // 如果点击的不是按钮，则显示详情
    if (!e.target.closest('.btn')) {
      const title = this.querySelector('.card-title').textContent;
      console.log('查看详情:', title);
      alert('查看详情: ' + title);
    }
  });
});

// 快捷操作点击事件
const quickActions = document.querySelectorAll('.quick-action');
quickActions.forEach(action => {
  action.addEventListener('click', function() {
    const actionText = this.querySelector('.quick-action-text').textContent;
    console.log('执行操作:', actionText);
    alert('执行操作: ' + actionText);
  });
});

// 新建设计按钮
const newDesignButtons = document.querySelectorAll('.btn-primary');
newDesignButtons.forEach(btn => {
  if (btn.textContent.includes('新建设计')) {
    btn.addEventListener('click', function(e) {
      e.stopPropagation();
      console.log('新建设计项目');
      
      // 跳转到新建设计视图
      showNewDesignView();
      
      // 更新左侧导航状态
      sidebarItems.forEach(i => i.classList.remove('active'));
      const newDesignItem = Array.from(sidebarItems).find(item => item.textContent.includes('新建设计'));
      if (newDesignItem) {
        newDesignItem.classList.add('active');
      }
    });
  }
});

// 设计详情视图中的发起审批按钮
const detailApprovalBtn = document.getElementById('detailApprovalBtn');
if (detailApprovalBtn) {
  detailApprovalBtn.addEventListener('click', async function(e) {
    e.stopPropagation();
    console.log('从设计详情视图发起审批');
    
    // 检查用户是否登录
    if (!currentUserId) {
      alert('请先登录');
      return;
    }
    
    // 检查是否有处理结果或上传目录
    if (!currentProcessResult && !currentUploadDir) {
      alert('请先上传并处理文件');
      return;
    }
    
    try {
      // 禁用按钮，显示加载状态
      detailApprovalBtn.disabled = true;
      const originalHTML = detailApprovalBtn.innerHTML;
      detailApprovalBtn.innerHTML = `
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none" style="margin-right: 6px; animation: spin 1s linear infinite;">
          <circle cx="8" cy="8" r="6" stroke="currentColor" stroke-width="2" stroke-dasharray="12" stroke-dashoffset="6"/>
        </svg>
        提交中...
      `;
      
      // 构建请求数据
      const requestData = {
        user_id: currentUserId
      };
      
      // 获取顶部标题输入框的值（位于waterfall-header区域）
      const detailTitleInput = document.getElementById('detailTitleInput');
      if (detailTitleInput) {
        const titleValue = detailTitleInput.value.trim();
        if (titleValue) {
          requestData.title = titleValue;
          console.log('使用顶部标题输入框的值:', titleValue);
        } else {
          console.warn('顶部标题输入框为空，将使用默认标题');
        }
      } else {
        console.warn('未找到顶部标题输入框');
      }

      // 获取审批联系人输入框的值
      const approver1Hidden = document.getElementById('approver1ContactIds');
      const approver1Input = document.getElementById('approver1ContactInput');
      if (approver1Hidden && approver1Hidden.value.trim()) {
        const approver1Ids = approver1Hidden.value
          .split(',')
          .map(item => item.trim())
          .filter(Boolean);
        if (approver1Ids.length > 0) {
          requestData.approver1_contact_ids = approver1Ids;
        }
      } else if (approver1Input) {
        const approver1Value = approver1Input.value.trim();
        if (approver1Value) {
          requestData.approver1_contact_ids = approver1Value
            .split(/[,，\s]+/)
            .map(item => item.trim())
            .filter(Boolean);
        }
      }

      const approver2Hidden = document.getElementById('approver2ContactIds');
      const approver2Input = document.getElementById('approver2ContactInput');
      if (approver2Hidden && approver2Hidden.value.trim()) {
        const approver2Ids = approver2Hidden.value
          .split(',')
          .map(item => item.trim())
          .filter(Boolean);
        if (approver2Ids.length > 0) {
          requestData.approver2_contact_ids = approver2Ids;
        }
      } else if (approver2Input) {
        const approver2Value = approver2Input.value.trim();
        if (approver2Value) {
          requestData.approver2_contact_ids = approver2Value
            .split(/[,，\s]+/)
            .map(item => item.trim())
            .filter(Boolean);
        }
      }
      
      // 校验审批人信息是否填写
      const approver1Ids = Array.isArray(requestData.approver1_contact_ids)
        ? requestData.approver1_contact_ids
        : [];
      const approver2Ids = Array.isArray(requestData.approver2_contact_ids)
        ? requestData.approver2_contact_ids
        : [];

      if (approver1Ids.length === 0) {
        alert('请先选择节点 2 · 研发代表的审批人');
        detailApprovalBtn.disabled = false;
        detailApprovalBtn.innerHTML = originalHTML;
        return;
      }

      if (approver2Ids.length === 0) {
        alert('请先选择节点 3 · 部门经理的审批人');
        detailApprovalBtn.disabled = false;
        detailApprovalBtn.innerHTML = originalHTML;
        return;
      }

      // 如果有处理结果，优先使用
      if (currentProcessResult) {
        requestData.process_result = currentProcessResult;
      }
      
      // 如果有上传目录，添加文件路径
      if (currentUploadDir) {
        requestData.file_path = currentUploadDir;
      }
      
      // 如果有处理结果中的文件路径列表，也添加
      if (currentProcessResult && currentProcessResult.success_files) {
        const filePaths = currentProcessResult.success_files.map(file => file.relative_path || file.file_path);
        if (filePaths.length > 0) {
          requestData.file_paths = filePaths;
        }
      }
      
      console.log('发起审批请求:', requestData);
      
      // 调用后端接口
      const response = await fetch(`${API_BASE_URL}/create_approval_instance_with_multiple_files`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestData)
      });
      
      const result = await response.json();
      
      if (result.success) {
        // 审批创建成功，更新按钮状态为已提交
        detailApprovalBtn.disabled = true;
        detailApprovalBtn.innerHTML = `
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <path d="M13 4L6 11L3 8" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          已提交
        `;
        detailApprovalBtn.classList.add('btn-success');
        detailApprovalBtn.classList.remove('btn-primary');
        
        // 显示成功消息
        const instanceCode = result.data?.instance_code || '';
        const message = instanceCode ? `审批创建成功！\n审批实例编号: ${instanceCode}\n${result.message || ''}` : `审批创建成功！\n${result.message || ''}`;
        alert(message);
        console.log('审批创建结果:', result);
        
        // 返回到全部设计视图
        showDesignListView();
        
        // 更新左侧导航状态
        const sidebarItems = document.querySelectorAll('.sidebar-item');
        sidebarItems.forEach(i => i.classList.remove('active'));
        const allDesignItem = Array.from(sidebarItems).find(item => item.textContent.includes('全部设计'));
        if (allDesignItem) {
          allDesignItem.classList.add('active');
        }
      } else {
        // 审批创建失败，恢复按钮状态
        detailApprovalBtn.disabled = false;
        detailApprovalBtn.innerHTML = originalHTML;
        alert(`审批创建失败：${result.error || result.message || '未知错误'}`);
        console.error('审批创建失败:', result);
      }
    } catch (error) {
      console.error('调用审批接口失败:', error);
      alert(`调用审批接口失败: ${error.message}`);
      // 恢复按钮状态
      detailApprovalBtn.disabled = false;
      detailApprovalBtn.innerHTML = originalHTML;
    }
  });
}

// 重新上传按钮
const reuploadBtn = document.getElementById('reuploadBtn');
if (reuploadBtn) {
  reuploadBtn.addEventListener('click', function(e) {
    e.stopPropagation();
    console.log('点击重新上传按钮');
    resetAndReturnToNewDesign();
  });
}

// 筛选按钮 - 打开筛选弹窗
function initFilterButton() {
  const filterButton = document.querySelector('.btn-secondary');
  if (filterButton && filterButton.textContent.includes('筛选')) {
    filterButton.addEventListener('click', function(e) {
      e.stopPropagation();
      console.log('打开筛选弹窗');
      showFilterModal();
    });
  }
}

// 显示筛选弹窗
function showFilterModal() {
  // 确保弹窗元素存在，如果不存在则创建
  let modal = document.getElementById('filterModal');
  if (!modal) {
    modal = createFilterModal();
    document.body.appendChild(modal);
  }
  
  // 恢复之前的筛选条件
  const instanceCodeInput = document.getElementById('filterInstanceCode');
  if (instanceCodeInput && window.currentFilterInstanceCode) {
    instanceCodeInput.value = window.currentFilterInstanceCode;
  }
  
  // 显示弹窗
  modal.style.display = 'flex';
  document.body.style.overflow = 'hidden';
}

// 创建筛选弹窗元素
function createFilterModal() {
  const modal = document.createElement('div');
  modal.id = 'filterModal';
  modal.className = 'modal-overlay';
  modal.style.display = 'none';
  
  // 获取当前日期作为默认值
  const today = new Date();
  const oneMonthAgo = new Date();
  oneMonthAgo.setMonth(today.getMonth() - 1);
  
  const formatDate = (date) => {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  };
  
  modal.innerHTML = `
    <div class="modal-container filter-modal">
      <div class="modal-header">
        <h3 class="modal-title">筛选条件</h3>
        <button class="modal-close-btn" onclick="closeFilterModal()" aria-label="关闭">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M18 6L6 18M6 6l12 12"/>
          </svg>
        </button>
      </div>
      <div class="modal-body filter-modal-body">
        <div class="filter-section">
          <div class="filter-section-title">时间段筛选</div>
          <div class="date-range-picker">
            <div class="date-input-group">
              <label class="date-label">开始日期</label>
              <input type="date" id="filterStartDate" class="date-input" value="${formatDate(oneMonthAgo)}">
            </div>
            <div class="date-input-group">
              <label class="date-label">结束日期</label>
              <input type="date" id="filterEndDate" class="date-input" value="${formatDate(today)}">
            </div>
          </div>
          <div class="quick-date-buttons">
            <button class="quick-date-btn" data-days="7">最近7天</button>
            <button class="quick-date-btn" data-days="30">最近30天</button>
            <button class="quick-date-btn" data-days="90">最近90天</button>
            <button class="quick-date-btn" data-days="0">全部</button>
          </div>
        </div>
        <div class="filter-section">
          <div class="filter-section-title">变更单编号筛选</div>
          <div class="filter-input-group">
            <label class="filter-label">变更单编号</label>
            <input type="text" id="filterInstanceCode" class="filter-input" placeholder="请输入审批实例编号">
          </div>
        </div>
      </div>
      <div class="modal-footer">
        <button class="btn btn-secondary" onclick="resetFilter()">重置</button>
        <button class="btn btn-primary" onclick="applyFilter()">应用筛选</button>
      </div>
    </div>
  `;
  
  // 点击遮罩层关闭弹窗
  modal.addEventListener('click', function(e) {
    if (e.target === modal) {
      closeFilterModal();
    }
  });
  
  // 绑定快速日期按钮事件
  setTimeout(() => {
    const quickDateButtons = modal.querySelectorAll('.quick-date-btn');
    quickDateButtons.forEach(btn => {
      btn.addEventListener('click', function() {
        const days = parseInt(this.getAttribute('data-days'));
        setQuickDateRange(days);
      });
    });
  }, 0);
  
  return modal;
}

// 设置快速日期范围
function setQuickDateRange(days) {
  const startDateInput = document.getElementById('filterStartDate');
  const endDateInput = document.getElementById('filterEndDate');
  
  if (!startDateInput || !endDateInput) return;
  
  const endDate = new Date();
  const startDate = new Date();
  
  if (days === 0) {
    // 全部：设置为一个很早的日期和今天
    startDate.setFullYear(2020, 0, 1);
    endDateInput.value = formatDateForInput(endDate);
    startDateInput.value = formatDateForInput(startDate);
  } else {
    startDate.setDate(endDate.getDate() - days);
    endDateInput.value = formatDateForInput(endDate);
    startDateInput.value = formatDateForInput(startDate);
  }
}

// 格式化日期为input date格式
function formatDateForInput(date) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

// 重置筛选条件
function resetFilter() {
  const startDateInput = document.getElementById('filterStartDate');
  const endDateInput = document.getElementById('filterEndDate');
  const instanceCodeInput = document.getElementById('filterInstanceCode');
  
  if (startDateInput && endDateInput) {
    const today = new Date();
    const oneMonthAgo = new Date();
    oneMonthAgo.setMonth(today.getMonth() - 1);
    
    startDateInput.value = formatDateForInput(oneMonthAgo);
    endDateInput.value = formatDateForInput(today);
  }
  
  if (instanceCodeInput) {
    instanceCodeInput.value = '';
  }
  
  // 清除筛选，应用默认筛选
  applyFilter();
}

// 应用筛选条件
function applyFilter() {
  const startDateInput = document.getElementById('filterStartDate');
  const endDateInput = document.getElementById('filterEndDate');
  const instanceCodeInput = document.getElementById('filterInstanceCode');
  
  let startDate = null;
  let endDate = null;
  
  if (startDateInput && startDateInput.value) {
    startDate = new Date(startDateInput.value);
    startDate.setHours(0, 0, 0, 0);
  }
  
  if (endDateInput && endDateInput.value) {
    endDate = new Date(endDateInput.value);
    endDate.setHours(23, 59, 59, 999);
  }
  
  // 验证日期范围
  if (startDate && endDate && startDate > endDate) {
    alert('开始日期不能晚于结束日期');
    return;
  }
  
  // 获取instance_code筛选值
  const instanceCodeFilter = instanceCodeInput ? instanceCodeInput.value.trim() : '';
  
  // 保存筛选条件到全局变量
  window.currentFilterDateRange = {
    startDate: startDate,
    endDate: endDate
  };
  window.currentFilterInstanceCode = instanceCodeFilter;
  
  console.log('应用筛选条件:', {
    startDate: startDate ? startDate.toISOString() : '无限制',
    endDate: endDate ? endDate.toISOString() : '无限制',
    instanceCode: instanceCodeFilter || '无限制'
  });
  
  // 关闭弹窗
  closeFilterModal();
  
  // 应用筛选
  applyFilters();
}

// 关闭筛选弹窗
function closeFilterModal() {
  const modal = document.getElementById('filterModal');
  if (modal) {
    modal.style.display = 'none';
    document.body.style.overflow = 'auto';
  }
}

// 初始化筛选按钮
initFilterButton();

// 用户信息点击 - 退出登录
const userInfoElement = document.getElementById('userInfo');
if (userInfoElement) {
  userInfoElement.addEventListener('click', function() {
    if (currentUserId) {
      // 显示退出登录确认
      if (confirm(`确定要退出登录吗？\n当前用户：${currentUserName} (${currentUserId})`)) {
        logout();
      }
    }
  });
}

// 退出登录
function logout() {
  console.log('退出登录');
  
  // 清除用户信息
  currentUserId = null;
  currentUserName = null;
  
  // 清除本地存储
  localStorage.removeItem('currentUserId');
  localStorage.removeItem('currentUserName');
  
  // 更新界面显示
  updateUserDisplay();
  // 显示登录遮罩，隐藏主页面
  showLoginOverlay();
  
  console.log('已退出登录');
}

// 右侧边栏折叠功能
const rightSidebar = document.getElementById('rightSidebar');
const sidebarToggle = document.getElementById('sidebarToggle');
const floatingToggle = document.getElementById('floatingToggle');

if (sidebarToggle && floatingToggle && rightSidebar) {
  // 初始化：如果右侧栏默认隐藏，设置为collapsed状态并显示悬浮按钮
  const computedDisplay = window.getComputedStyle(rightSidebar).display;
  if (rightSidebar.style.display === 'none' || computedDisplay === 'none') {
    rightSidebar.style.display = 'block';
    rightSidebar.classList.add('collapsed');
    floatingToggle.style.display = 'flex';
  } else {
    // 如果右侧栏默认显示，隐藏悬浮按钮
    floatingToggle.style.display = 'none';
  }
  
  // 侧边栏内的折叠按钮
  sidebarToggle.addEventListener('click', function(e) {
    e.stopPropagation();
    rightSidebar.classList.add('collapsed');
    floatingToggle.style.display = 'flex';
  });

  // 悬浮按钮
  floatingToggle.addEventListener('click', function(e) {
    e.stopPropagation();
    // 确保右侧栏显示，然后移除collapsed class
    rightSidebar.style.display = 'block';
    rightSidebar.classList.remove('collapsed');
    floatingToggle.style.display = 'none';
  });
}

// 文件管理功能
let uploadedFiles = [];
// 保存上传目录路径（用于后续调用接口）
let currentUploadDir = null;
// 保存处理结果数据（用于显示详情视图）
let currentProcessResult = null;

const fileInput = document.getElementById('fileInput');
const fileList = document.getElementById('fileList');
const fileCount = document.getElementById('fileCount');
const processBtn = document.getElementById('processBtn');

if (fileInput) {
  fileInput.addEventListener('change', function(e) {
    handleFiles(e.target.files);
  });
}

function handleFiles(files) {
  let addedCount = 0;
  let skippedCount = 0;
  
  Array.from(files).forEach(file => {
    if (file.name.endsWith('.xlsx') || file.name.endsWith('.xls')) {
      // 检查是否已存在同名文件
      const exists = uploadedFiles.some(existingFile => 
        existingFile.name === file.name && 
        existingFile.size === formatFileSize(file.size)
      );
      
      if (!exists) {
        uploadedFiles.push({
          id: Date.now() + Math.random(),
          name: file.name,
          size: formatFileSize(file.size),
          file: file
        });
        addedCount++;
      } else {
        skippedCount++;
      }
    }
  });
  
  if (addedCount > 0) {
    renderFileList();
    updateProcessButton();
    
    // 如果有跳过的文件，显示提示
    if (skippedCount > 0) {
      showToast(`已添加 ${addedCount} 个文件，${skippedCount} 个文件已存在，已跳过`, 'info');
    }
  } else if (skippedCount > 0) {
    showToast(`${skippedCount} 个文件已存在，已跳过`, 'info');
  }
}

function formatFileSize(bytes) {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

function renderFileList() {
  if (uploadedFiles.length === 0) {
    fileList.innerHTML = `
      <div class="empty-state-merged">
        <div class="empty-icon">📁</div>
        <p class="empty-text">暂无文件</p>
        <p class="empty-hint">拖拽Excel文件到此处，或点击上方区域选择，也可使用 Ctrl+V 粘贴</p>
        <p class="empty-format">支持 .xlsx 和 .xls 格式</p>
      </div>
    `;
    // 显示拖拽提示区域
    if (dragHint) {
      dragHint.classList.add('visible');
    }
  } else {
    fileList.innerHTML = uploadedFiles.map(file => `
      <div class="file-item" data-id="${file.id}">
        <div class="file-icon">
          <svg viewBox="0 0 24 24" fill="none">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" stroke="currentColor" stroke-width="2"/>
            <path d="M14 2v6h6M16 13H8M16 17H8M10 9H8" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          </svg>
        </div>
        <div class="file-info">
          <div class="file-name">${file.name}</div>
          <div class="file-size">${file.size}</div>
        </div>
        <div class="file-actions">
          <button class="file-action-btn delete" onclick="removeFile('${file.id}')" title="删除">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path d="M3 4h10M6 4V3h4v1M5 4v9h6V4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
            </svg>
          </button>
        </div>
      </div>
    `).join('');
    // 隐藏拖拽提示区域
    if (dragHint) {
      dragHint.classList.remove('visible');
    }
  }
  
  fileCount.textContent = uploadedFiles.length;
}

function removeFile(fileId) {
  uploadedFiles = uploadedFiles.filter(f => f.id != fileId);
  renderFileList();
  updateProcessButton();
}

function clearAllFiles() {
  if (uploadedFiles.length === 0) return;
  
  if (confirm('确定要清空所有文件吗？')) {
    uploadedFiles = [];
    currentUploadDir = null; // 清空上传目录路径
    renderFileList();
    updateProcessButton();
    updateUploadDirDisplay(); // 更新上传目录显示
    if (fileInput) fileInput.value = '';
    console.log('已清空文件列表和上传目录路径');
  }
}

// 重置所有状态并返回新建设计视图
function resetAndReturnToNewDesign() {
  // 返回到新建设计视图（showNewDesignView内部会调用resetNewDesignState重置状态）
  showNewDesignView();
  
  // 更新左侧导航状态
  const sidebarItems = document.querySelectorAll('.sidebar-item');
  sidebarItems.forEach(i => i.classList.remove('active'));
  const newDesignItem = Array.from(sidebarItems).find(item => item.textContent.includes('新建设计'));
  if (newDesignItem) {
    newDesignItem.classList.add('active');
  }
  
  console.log('已重置所有状态并返回新建设计视图');
}

// 更新上传目录显示
function updateUploadDirDisplay() {
  const uploadDirInfo = document.getElementById('uploadDirInfo');
  const uploadDirPath = document.getElementById('uploadDirPath');
  
  if (uploadDirInfo && uploadDirPath) {
    if (currentUploadDir) {
      uploadDirPath.textContent = currentUploadDir;
      uploadDirInfo.style.display = 'block';
    } else {
      uploadDirInfo.style.display = 'none';
    }
  }
}

function updateProcessButton() {
  if (processBtn) {
    if (uploadedFiles.length > 0) {
      processBtn.disabled = false;
      processBtn.style.opacity = '1';
      processBtn.style.cursor = 'pointer';
    } else {
      processBtn.disabled = true;
      processBtn.style.opacity = '0.5';
      processBtn.style.cursor = 'not-allowed';
    }
  }
}

// 上传文件到服务器
async function uploadFilesToServer() {
  if (uploadedFiles.length === 0) {
    alert('请先选择要上传的文件');
    return { success: false, uploadResult: null };
  }

  // 检查是否已登录
  if (!currentUserId) {
    alert('请先登录');
    return { success: false, uploadResult: null };
  }

  try {
    // 显示上传中状态（不在这里恢复按钮，因为还要继续处理）
    if (processBtn) {
      processBtn.disabled = true;
      processBtn.innerHTML = `
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none" style="margin-right: 6px; animation: spin 1s linear infinite;">
          <circle cx="8" cy="8" r="6" stroke="currentColor" stroke-width="2" stroke-dasharray="12" stroke-dashoffset="6"/>
        </svg>
        上传中...
      `;
    }

    // 创建 FormData
    const formData = new FormData();
    
    // 添加文件
    uploadedFiles.forEach(fileObj => {
      formData.append('files', fileObj.file);
    });
    
    // 添加用户ID
    if (currentUserId) {
      formData.append('user_id', currentUserId);
    }

    // 调用上传接口
    const response = await fetch(`${API_BASE_URL}/api/upload_files`, {
      method: 'POST',
      body: formData
    });

    const result = await response.json();

    if (result.success) {
      // 保存上传目录路径
      currentUploadDir = result.upload_dir;
      
      console.log('文件上传成功:', result);
      console.log('上传目录路径已保存:', currentUploadDir);
      
      // 更新上传目录显示
      updateUploadDirDisplay();
      
      // 返回成功结果和上传结果数据
      return { success: true, uploadResult: result };
    } else {
      throw new Error(result.error || result.message || '上传失败');
    }
  } catch (error) {
    console.error('文件上传失败:', error);
    alert(`上传失败: ${error.message}`);
    // 上传失败时恢复按钮状态
    if (processBtn) {
      processBtn.disabled = false;
      processBtn.innerHTML = `
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
          <path d="M8 2v12M2 8h12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>
        开始处理
      `;
    }
    return { success: false, uploadResult: null };
  }
}

// 处理上传的文件
async function processUploadedFiles(uploadResult) {
  try {
    // 更新按钮状态为处理中
    if (processBtn) {
      processBtn.disabled = true;
      processBtn.innerHTML = `
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none" style="margin-right: 6px; animation: spin 1s linear infinite;">
          <circle cx="8" cy="8" r="6" stroke="currentColor" stroke-width="2" stroke-dasharray="12" stroke-dashoffset="6"/>
        </svg>
        处理中...
      `;
    }

    // 构建文件路径列表（使用相对路径）
    const excelFilePaths = uploadResult.files.map(file => file.relative_path);
    
    console.log('开始处理文件，文件路径列表:', excelFilePaths);
    
    // 调用处理接口
    const response = await fetch(`${API_BASE_URL}/process_multiple_excel_files`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        excel_file_paths: excelFilePaths,
        worker_id: currentUserId || '250000',
        output_dir: 'data/tmp',
        create_subdir: true
      })
    });

    const result = await response.json();

    if (result.success) {
      console.log('文件处理成功:', result);
      
      // 保存处理结果
      currentProcessResult = result.data;
      
      // 显示成功消息
      const successCount = result.data?.success_count || 0;
      const totalFiles = result.data?.total_files || 0;
      alert(`处理完成！\n成功: ${successCount}/${totalFiles} 个文件\n${result.message || ''}`);
      
      return { success: true, processResult: result.data };
    } else {
      throw new Error(result.error || result.message || '处理失败');
    }
  } catch (error) {
    console.error('文件处理失败:', error);
    alert(`处理失败: ${error.message}`);
    return { success: false, processResult: null };
  } finally {
    // 恢复按钮状态
    if (processBtn) {
      processBtn.disabled = false;
      processBtn.innerHTML = `
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
          <path d="M8 2v12M2 8h12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>
        开始处理
      `;
    }
  }
}

function startProcessing() {
  if (uploadedFiles.length === 0) return;
  
  console.log(`开始处理 ${uploadedFiles.length} 个文件:`, uploadedFiles);
  
  // 先上传文件到服务器
  uploadFilesToServer().then(async (uploadResponse) => {
    if (uploadResponse && uploadResponse.success && uploadResponse.uploadResult) {
      console.log('文件已上传，上传目录:', currentUploadDir);
      
      // 处理上传的文件
      const processResponse = await processUploadedFiles(uploadResponse.uploadResult);
      
      if (processResponse && processResponse.success && processResponse.processResult) {
        // 更新设计详情视图，使用实际数据
        updateDesignDetailView(processResponse.processResult);
        
        // 跳转到设计详情视图
        showDesignDetailView();
        
        // 更新左侧导航状态
        sidebarItems.forEach(i => i.classList.remove('active'));
        const detailItem = Array.from(sidebarItems).find(item => item.textContent.includes('设计详情'));
        if (detailItem) {
          detailItem.classList.add('active');
        }
      }
    } else {
      // 上传失败，按钮状态已在 uploadFilesToServer 中恢复
      console.error('文件上传失败');
    }
  }).catch(error => {
    console.error('处理流程出错:', error);
    // 确保按钮状态恢复
    if (processBtn) {
      processBtn.disabled = false;
      processBtn.innerHTML = `
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
          <path d="M8 2v12M2 8h12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>
        开始处理
      `;
    }
  });
}

// 拖拽上传支持 - 整个文件管理区域
const fileManagerSection = document.getElementById('fileManagerSection');
const dragHint = document.getElementById('dragHint');

if (fileManagerSection) {
  // 防止默认拖拽行为
  ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
    fileManagerSection.addEventListener(eventName, preventDefaults, false);
  });

  function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
  }

  // 拖拽进入
  ['dragenter', 'dragover'].forEach(eventName => {
    fileManagerSection.addEventListener(eventName, function() {
      fileManagerSection.classList.add('drag-over');
    }, false);
  });

  // 拖拽离开
  ['dragleave', 'drop'].forEach(eventName => {
    fileManagerSection.addEventListener(eventName, function() {
      fileManagerSection.classList.remove('drag-over');
    }, false);
  });

  // 文件放下
  fileManagerSection.addEventListener('drop', function(e) {
    const dt = e.dataTransfer;
    const files = dt.files;
    handleFiles(files);
  }, false);
}

// 点击拖拽提示区域触发文件选择
if (dragHint && fileInput) {
  dragHint.addEventListener('click', function(e) {
    // 只有在可见状态时才触发点击
    if (dragHint.classList.contains('visible')) {
      e.preventDefault();
      e.stopPropagation();
      fileInput.click();
    }
  });
}

// 显示提示消息的通用函数
function showToast(message, type = 'info') {
  const colors = {
    success: '#52c41a',
    warning: '#ff9800',
    error: '#f5222d',
    info: '#1890ff'
  };
  
  const color = colors[type] || colors.info;
  
  const toast = document.createElement('div');
  toast.style.cssText = `
    position: fixed;
    top: 20px;
    right: 20px;
    background: ${color};
    color: white;
    padding: 12px 20px;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    z-index: 10000;
    font-size: 14px;
    animation: slideIn 0.3s ease;
    max-width: 400px;
    word-wrap: break-word;
  `;
  toast.textContent = message;
  document.body.appendChild(toast);
  
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transition = 'opacity 0.3s';
    setTimeout(() => {
      if (document.body.contains(toast)) {
        document.body.removeChild(toast);
      }
    }, 300);
  }, 3000);
}

// 粘贴上传功能 - 监听 Ctrl+V 粘贴事件
const uploadArea = document.getElementById('uploadArea');
if (uploadArea) {
  // 点击上传区域时自动获取焦点，以便接收粘贴事件
  uploadArea.addEventListener('click', function(e) {
    // 如果点击的不是文件列表中的元素，则获取焦点
    if (!e.target.closest('.file-item')) {
      uploadArea.focus();
    }
  });

  // 注意：粘贴事件处理已移至全局监听器，避免重复处理

  // 添加键盘快捷键提示
  uploadArea.addEventListener('keydown', function(e) {
    // 当用户按下 Ctrl+V 时，确保焦点在上传区域
    if (e.ctrlKey && e.key === 'v') {
      uploadArea.focus();
    }
  });
}

// 全局粘贴监听 - 当新建设计视图显示时，允许全局粘贴
let globalPasteHandler = null;
let isProcessingPaste = false; // 防止重复处理

function enableGlobalPaste() {
  if (globalPasteHandler) return; // 已经启用
  
  globalPasteHandler = function(e) {
    // 防止重复处理
    if (isProcessingPaste) {
      return;
    }
    
    // 检查是否在新建设计视图中
    const newDesignView = document.getElementById('newDesignView');
    if (!newDesignView || newDesignView.style.display === 'none') {
      return; // 不在新建设计视图，不处理
    }
    
    // 检查焦点是否在输入框或文本框中
    const activeElement = document.activeElement;
    if (activeElement && (
      activeElement.tagName === 'INPUT' && activeElement.type !== 'file' ||
      activeElement.tagName === 'TEXTAREA' ||
      activeElement.isContentEditable
    )) {
      return; // 焦点在输入框中，不拦截
    }
    
    // 检查焦点是否在上传区域或其子元素中
    const uploadArea = document.getElementById('uploadArea');
    if (!uploadArea) {
      return;
    }
    
    // 如果焦点不在上传区域，先获取焦点
    if (activeElement !== uploadArea && !uploadArea.contains(activeElement)) {
      uploadArea.focus();
    }
    
    // 设置处理标志
    isProcessingPaste = true;
    e.preventDefault();
    e.stopPropagation();
    
    // 处理粘贴的文件
    const clipboardData = e.clipboardData || window.clipboardData;
    if (!clipboardData) {
      isProcessingPaste = false;
      showToast('无法访问剪贴板，请使用拖拽或点击上传', 'warning');
      return;
    }

    const items = clipboardData.items;
    if (!items || items.length === 0) {
      isProcessingPaste = false;
      showToast('剪贴板中没有文件，请先复制文件（Ctrl+C）', 'info');
      return;
    }

    const files = [];
    for (let i = 0; i < items.length; i++) {
      const item = items[i];
      
      // 检查是否是文件类型
      if (item.kind === 'file') {
        const file = item.getAsFile();
        if (file) {
          // 检查文件扩展名
          const fileName = file.name || 'pasted-file';
          const fileExtension = fileName.toLowerCase().substring(fileName.lastIndexOf('.'));
          
          // 如果是 Excel 文件，直接添加
          if (fileExtension === '.xlsx' || fileExtension === '.xls') {
            files.push(file);
          } else if (!fileExtension || fileExtension === fileName.toLowerCase()) {
            // 如果没有扩展名，尝试根据 MIME 类型判断
            const mimeType = file.type || item.type;
            if (mimeType.includes('spreadsheet') || 
                mimeType.includes('excel') || 
                mimeType === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' ||
                mimeType === 'application/vnd.ms-excel') {
              // 创建一个带扩展名的文件对象
              const blob = file.slice(0, file.size, mimeType);
              const renamedFile = new File([blob], fileName.endsWith('.xlsx') || fileName.endsWith('.xls') 
                ? fileName 
                : fileName + (mimeType.includes('openxml') ? '.xlsx' : '.xls'), 
                { type: mimeType });
              files.push(renamedFile);
            } else {
              // 对于其他文件类型，也尝试添加（用户可能想上传）
              // 但优先处理 Excel 文件
              if (mimeType.startsWith('image/')) {
                // 图片文件，跳过（通常不是 Excel 文件）
                continue;
              }
              files.push(file);
            }
          }
        }
      }
    }

    // 如果有文件，处理它们
    if (files.length > 0) {
      // 过滤出 Excel 文件
      const excelFiles = files.filter(file => {
        const name = file.name.toLowerCase();
        return name.endsWith('.xlsx') || name.endsWith('.xls');
      });

      if (excelFiles.length > 0) {
        handleFiles(excelFiles);
        showToast(`成功粘贴 ${excelFiles.length} 个文件`, 'success');
      } else {
        showToast('粘贴的文件不是 Excel 格式（.xlsx 或 .xls），已忽略', 'warning');
      }
    } else {
      // 显示提示信息
      showToast('剪贴板中没有可用的文件，请先复制文件（Ctrl+C）', 'info');
    }
    
    // 重置处理标志（使用 setTimeout 确保异步操作完成）
    setTimeout(() => {
      isProcessingPaste = false;
    }, 100);
  };
  
  document.addEventListener('paste', globalPasteHandler, true);
}

function disableGlobalPaste() {
  if (globalPasteHandler) {
    document.removeEventListener('paste', globalPasteHandler, true);
    globalPasteHandler = null;
  }
}

// 全局粘贴功能已通过 showNewDesignView() 和 disableGlobalPaste() 函数管理
// 当显示新建设计视图时启用，切换到其他视图时禁用

// 页签切换功能
const tabItems = document.querySelectorAll('.tab-item');
const tabContents = document.querySelectorAll('.tab-content');

tabItems.forEach(tab => {
  tab.addEventListener('click', function() {
    const targetTab = this.getAttribute('data-tab');
    
    // 移除所有active状态
    tabItems.forEach(t => t.classList.remove('active'));
    tabContents.forEach(c => c.classList.remove('active'));
    
    // 添加当前active状态
    this.classList.add('active');
    const targetContent = document.querySelector(`[data-content="${targetTab}"]`);
    if (targetContent) {
      targetContent.classList.add('active');
    }
  });
});

// 状态标签切换功能
const statusBadge = document.getElementById('detailStatusBadge');
if (statusBadge) {
  const statuses = [
    {
      class: 'status-review',
      icon: '<path d="M8 3v5l3 3M14 8A6 6 0 1 1 2 8a6 6 0 0 1 12 0z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>',
      text: '审批中'
    },
    {
      class: 'status-approved',
      icon: '<path d="M13 7L6.5 13.5 3 10" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/><circle cx="8" cy="8" r="6" stroke="currentColor" stroke-width="1.5"/>',
      text: '已通过'
    },
    {
      class: 'status-draft',
      icon: '<path d="M11 4H4a2 2 0 0 0-2 2v8a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2V7l-3-3z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/><path d="M11 4v3h3" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>',
      text: '草稿'
    },
    {
      class: 'status-rejected',
      icon: '<circle cx="8" cy="8" r="6" stroke="currentColor" stroke-width="1.5"/><path d="M10 6L6 10M6 6l4 4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>',
      text: '已驳回'
    }
  ];
  
  let currentStatusIndex = 0;
  
  statusBadge.addEventListener('click', function(e) {
    e.stopPropagation();
    
    // 切换到下一个状态
    currentStatusIndex = (currentStatusIndex + 1) % statuses.length;
    const newStatus = statuses[currentStatusIndex];
    
    // 移除所有状态类
    statuses.forEach(s => statusBadge.classList.remove(s.class));
    
    // 添加新状态类
    statusBadge.classList.add(newStatus.class);
    
    // 更新图标和文本
    statusBadge.innerHTML = `
      <svg width="14" height="14" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
        ${newStatus.icon}
      </svg>
      ${newStatus.text}
    `;
    
    console.log('状态已切换为:', newStatus.text);
  });
}

// 显示飞书审批实例信息弹窗
async function showLarkInstanceModal(design) {
  // 检查是否有approval_instance_code
  const instanceCode = design.approval_instance_code;
  if (!instanceCode) {
    alert('该设计没有关联的审批实例');
    return;
  }
  
  // 确保弹窗元素存在，如果不存在则创建
  let modal = document.getElementById('larkInstanceModal');
  if (!modal) {
    modal = createLarkInstanceModal();
    document.body.appendChild(modal);
  }
  
  // 显示加载状态
  showLarkInstanceModalLoading(modal);
  modal.style.display = 'flex';
  document.body.style.overflow = 'hidden';
  
  try {
    // 调用接口获取飞书审批实例信息
    const response = await fetch(`${API_BASE_URL}/api/lark/instance/${instanceCode}`);
    const result = await response.json();
    
    if (result.success) {
      // 填充数据
      await fillLarkInstanceModal(result, design, modal);
    } else {
      // 显示错误信息
      showLarkInstanceModalError(modal, result.error || { msg: '获取审批实例信息失败' });
    }
  } catch (error) {
    console.error('获取飞书审批实例信息失败:', error);
    showLarkInstanceModalError(modal, { msg: error.message || '网络错误' });
  }
}

// 创建飞书审批实例弹窗元素
function createLarkInstanceModal() {
  const modal = document.createElement('div');
  modal.id = 'larkInstanceModal';
  modal.className = 'modal-overlay';
  modal.style.display = 'none';
  
  modal.innerHTML = `
    <div class="modal-container lark-instance-modal">
      <div class="modal-header">
        <h3 class="modal-title">审批实例详情</h3>
        <button class="modal-close-btn" onclick="closeLarkInstanceModal()" aria-label="关闭">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M18 6L6 18M6 6l12 12"/>
          </svg>
        </button>
      </div>
      <div class="modal-body lark-instance-modal-body">
        <div id="larkInstanceLoading" style="text-align: center; padding: 40px;">
          <div style="font-size: 16px; color: #666;">加载中...</div>
        </div>
        <div id="larkInstanceContent" style="display: none;"></div>
        <div id="larkInstanceError" style="display: none;"></div>
      </div>
    </div>
  `;
  
  // 点击遮罩层关闭弹窗
  modal.addEventListener('click', function(e) {
    if (e.target === modal) {
      closeLarkInstanceModal();
    }
  });
  
  return modal;
}

// 显示加载状态
function showLarkInstanceModalLoading(modal) {
  const loading = modal.querySelector('#larkInstanceLoading');
  const content = modal.querySelector('#larkInstanceContent');
  const error = modal.querySelector('#larkInstanceError');
  
  if (loading) loading.style.display = 'block';
  if (content) content.style.display = 'none';
  if (error) error.style.display = 'none';
}

// 显示错误信息
function showLarkInstanceModalError(modal, errorInfo) {
  const loading = modal.querySelector('#larkInstanceLoading');
  const content = modal.querySelector('#larkInstanceContent');
  const error = modal.querySelector('#larkInstanceError');
  
  if (loading) loading.style.display = 'none';
  if (content) content.style.display = 'none';
  if (error) {
    error.style.display = 'block';
    error.innerHTML = `
      <div style="text-align: center; padding: 40px; color: #ff4d4f;">
        <div style="font-size: 48px; margin-bottom: 16px;">⚠️</div>
        <div style="font-size: 16px; margin-bottom: 8px;">加载失败</div>
        <div style="font-size: 14px; color: #999;">${escapeHtml(errorInfo.msg || '未知错误')}</div>
      </div>
    `;
  }
}

// 填充飞书审批实例弹窗内容
async function fillLarkInstanceModal(result, design, modal) {
  const loading = modal.querySelector('#larkInstanceLoading');
  const content = modal.querySelector('#larkInstanceContent');
  const error = modal.querySelector('#larkInstanceError');
  
  if (loading) loading.style.display = 'none';
  if (error) error.style.display = 'none';
  if (content) {
    content.style.display = 'block';
    
    const status = result.status || 'UNKNOWN';
    const form = result.form || {};
    const taskList = result.task_list || [];
    const timeline = result.timeline || [];

    // 收集需要解析的用户ID
    const userIds = [];
    taskList.forEach(task => {
      if (task && task.user_id) {
        userIds.push(task.user_id);
      }
    });
    timeline.forEach(item => {
      if (item && item.user_id) {
        userIds.push(item.user_id);
      }
    });

    const userNameMap = await resolveUserNames(userIds);
    
    // 格式化状态显示
    const statusText = {
      'PENDING': '待审批',
      'APPROVED': '已批准',
      'REJECTED': '已拒绝',
      'CANCELED': '已取消',
      'DELETED': '已删除'
    }[status] || status;
    
    const statusClass = {
      'PENDING': 'status-pending',
      'APPROVED': 'status-approved',
      'REJECTED': 'status-rejected',
      'CANCELED': 'status-canceled',
      'DELETED': 'status-deleted'
    }[status] || 'status-unknown';
    
    // 格式化表单数据
    let formHtml = '';
    if (form) {
      console.log('原始form数据:', typeof form, form);
      
      // 先尝试解析字符串格式的JSON
      let parsedForm = form;
      if (typeof form === 'string') {
        try {
          parsedForm = JSON.parse(form);
          console.log('解析后的form（字符串->对象）:', parsedForm);
        } catch (e) {
          console.warn('form不是有效的JSON字符串:', e);
          // 如果解析失败，尝试直接使用字符串
          parsedForm = form;
        }
      }
      
      // 检查是否为数组格式（飞书表单格式）
      if (Array.isArray(parsedForm)) {
        console.log('识别为数组格式，使用formatFormArray，数组长度:', parsedForm.length);
        formHtml = formatFormArray(parsedForm);
      } else if (parsedForm && typeof parsedForm === 'object') {
        // 如果是对象，检查是否可能是序列化的数组
        const keys = Object.keys(parsedForm);
        console.log('form是对象，keys:', keys);
        
        if (keys.length === 0) {
          formHtml = '<div class="empty-json">暂无表单数据</div>';
        } else {
          // 检查对象是否包含数组特征（如第一个元素有id、name、type等字段）
          const firstKey = keys[0];
          const firstValue = parsedForm[firstKey];
          
          // 检查是否可能是对象化的数组（如 {0: {...}, 1: {...}}）
          const hasNumericKeys = keys.every(k => !isNaN(parseInt(k)));
          const looksLikeArray = hasNumericKeys && firstValue && typeof firstValue === 'object' && 
                                 (firstValue.hasOwnProperty('id') || firstValue.hasOwnProperty('name') || firstValue.hasOwnProperty('type'));
          
          if (looksLikeArray) {
            console.log('识别为对象化的数组，转换为数组格式');
            const arrayLike = Object.keys(parsedForm).sort((a, b) => parseInt(a) - parseInt(b)).map(k => parsedForm[k]);
            formHtml = formatFormArray(arrayLike);
          } else {
            // 尝试检查是否所有值都是对象且包含id字段（可能是数组被序列化为对象）
            const allValues = Object.values(parsedForm);
            const allAreFormFields = allValues.length > 0 && allValues.every(v => 
              v && typeof v === 'object' && (v.hasOwnProperty('id') || v.hasOwnProperty('name') || v.hasOwnProperty('type'))
            );
            
            if (allAreFormFields) {
              console.log('识别为表单字段对象集合，转换为数组格式');
              formHtml = formatFormArray(allValues);
            } else {
              console.log('使用默认JSON显示');
              formHtml = formatJsonForDisplay(parsedForm);
            }
          }
        }
      } else {
        console.log('form是其他类型，直接显示');
        formHtml = `<div class="json-display"><div class="json-item"><span class="json-value">${escapeHtml(String(form))}</span></div></div>`;
      }
      
      console.log('最终生成的formHtml长度:', formHtml.length);
    } else {
      formHtml = '<div class="empty-json">暂无表单数据</div>';
    }
    
    // 格式化任务列表
    let taskListHtml = '';
    if (Array.isArray(taskList) && taskList.length > 0) {
      taskListHtml = `
        <div class="task-list">
          ${taskList.map((task, index) => {
            const taskStatus = task.status || 'UNKNOWN';
            const taskStatusText = {
              'PENDING': '待处理',
              'APPROVED': '已同意',
              'REJECTED': '已拒绝',
              'CANCELED': '已取消',
              'TRANSFERRED': '已转交',
              'DONE': '已完成'
            }[taskStatus] || taskStatus;
            
            const taskStatusClass = {
              'PENDING': 'status-pending',
              'APPROVED': 'status-approved',
              'REJECTED': 'status-rejected',
              'CANCELED': 'status-canceled',
              'TRANSFERRED': 'status-transferred',
              'DONE': 'status-approved'
            }[taskStatus] || 'status-unknown';
            
            return `
              <div class="task-item">
                <div class="task-header">
                  <span class="task-index">任务 ${index + 1}</span>
                  <span class="status-badge ${taskStatusClass}">${escapeHtml(taskStatusText)}</span>
                </div>
                ${task.user_id ? `<div class="task-user">处理人: ${escapeHtml(userNameMap[task.user_id] || task.user_id)}</div>` : ''}
                ${task.comment ? `<div class="task-comment">备注: ${escapeHtml(task.comment)}</div>` : ''}
                ${task.create_time ? `<div class="task-time">创建时间: ${escapeHtml(task.create_time)}</div>` : ''}
                ${task.end_time ? `<div class="task-time">结束时间: ${escapeHtml(task.end_time)}</div>` : ''}
              </div>
            `;
          }).join('')}
        </div>
      `;
    } else {
      taskListHtml = '<div class="empty-json">暂无任务列表</div>';
    }
    
    // 格式化时间线
    let timelineHtml = '';
    if (Array.isArray(timeline) && timeline.length > 0) {
      timelineHtml = `
        <div class="timeline-list">
          ${timeline.map((item, index) => {
            const timelineType = item.type || 'UNKNOWN';
            const timelineTypeText = {
              'START': '开始',
              'APPROVE': '同意',
              'REJECT': '拒绝',
              'TRANSFER': '转交',
              'ADD_APPROVER': '添加审批人',
              'PASS': '通过',
              'CANCEL': '取消'
            }[timelineType] || timelineType;
            
            return `
              <div class="timeline-item">
                <div class="timeline-marker"></div>
                <div class="timeline-content">
                  <div class="timeline-header">
                    <span class="timeline-type">${escapeHtml(timelineTypeText)}</span>
                    ${item.create_time ? `<span class="timeline-time">${escapeHtml(item.create_time)}</span>` : ''}
                  </div>
                  ${item.user_id ? `<div class="timeline-user">操作人: ${escapeHtml(userNameMap[item.user_id] || item.user_id)}</div>` : ''}
                  ${item.comment ? `<div class="timeline-comment">${escapeHtml(item.comment)}</div>` : ''}
                </div>
              </div>
            `;
          }).join('')}
        </div>
      `;
    } else {
      timelineHtml = '<div class="empty-json">暂无时间线</div>';
    }
    
    content.innerHTML = `
      <div class="info-section">
        <div class="info-section-title">审批状态</div>
        <div class="info-section-content">
          <div class="status-display">
            <span class="status-badge ${statusClass}">${escapeHtml(statusText)}</span>
            <span class="status-code">(${escapeHtml(status)})</span>
          </div>
        </div>
      </div>
      <div class="info-section">
        <div class="info-section-title">表单信息</div>
        <div class="info-section-content">
          ${formHtml}
        </div>
      </div>
      <div class="info-section">
        <div class="info-section-title">任务列表</div>
        <div class="info-section-content">
          ${taskListHtml}
        </div>
      </div>
      <div class="info-section">
        <div class="info-section-title">时间线</div>
        <div class="info-section-content">
          ${timelineHtml}
        </div>
      </div>
      ${design.approval_instance_code ? `
        <div class="info-section">
          <div class="info-section-title">实例代码</div>
          <div class="info-section-content">
            <div class="json-display">
              <div class="json-item">
                <span class="json-key">instance_code:</span>
                <span class="json-value json-string">${escapeHtml(design.approval_instance_code)}</span>
              </div>
            </div>
          </div>
        </div>
      ` : ''}
    `;
  }
}

// 格式化表单数组（飞书表单格式）
function formatFormArray(formArray) {
  if (!Array.isArray(formArray) || formArray.length === 0) {
    return '<div class="empty-json">暂无表单数据</div>';
  }
  
  let html = '<div class="form-fields">';
  
  // 遍历字段，将text类型作为前一个字段的副文本
  for (let index = 0; index < formArray.length; index++) {
    const field = formArray[index];
    const fieldId = field.id || '';
    const fieldName = field.name || `字段${index + 1}`;
    const fieldType = field.type || 'unknown';
    const fieldValue = field.value;
    const fieldExt = field.ext;
    
    // 如果是text类型，跳过单独显示（会在前一个字段中显示为副文本）
    if (fieldType === 'text') {
      continue;
    }
    
    // 检查下一个字段是否是text类型，如果是则作为副文本
    let hintText = '';
    if (index + 1 < formArray.length && formArray[index + 1].type === 'text') {
      hintText = formArray[index + 1].value || '';
    }
    
    // 根据字段类型选择不同的显示方式
    let valueHtml = '';
    
    if (fieldType === 'attachmentV2' || fieldType === 'attachment') {
      // 附件类型：显示为链接列表
      if (Array.isArray(fieldValue) && fieldValue.length > 0) {
        valueHtml = '<div class="form-attachments">';
        fieldValue.forEach((url, idx) => {
          const fileName = fieldExt || `附件${idx + 1}`;
          valueHtml += `
            <div class="form-attachment-item">
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none" style="margin-right: 8px; flex-shrink: 0;">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" stroke="currentColor" stroke-width="1.5"/>
                <path d="M14 2v6h6M12 13H8M12 17H8M10 9H8" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
              </svg>
              <a href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer" class="form-attachment-link">
                ${escapeHtml(fileName)}
              </a>
            </div>
          `;
        });
        valueHtml += '</div>';
      } else {
        valueHtml = '<span class="form-value-empty">无附件</span>';
      }
    } else if (fieldType === 'input' || fieldType === 'textarea') {
      // 输入框类型：显示为普通文本
      if (fieldValue) {
        valueHtml = `<div class="form-input-value">${escapeHtml(String(fieldValue))}</div>`;
      } else {
        valueHtml = '<span class="form-value-empty">未填写</span>';
      }
    } else if (fieldType === 'number') {
      // 数字类型
      valueHtml = `<div class="form-number-value">${escapeHtml(String(fieldValue || ''))}</div>`;
    } else if (fieldType === 'date' || fieldType === 'dateTime') {
      // 日期类型
      valueHtml = `<div class="form-date-value">${escapeHtml(String(fieldValue || ''))}</div>`;
    } else {
      // 其他类型：使用JSON格式显示
      if (fieldValue !== null && fieldValue !== undefined) {
        if (typeof fieldValue === 'object') {
          valueHtml = formatJsonForDisplay(fieldValue);
        } else {
          valueHtml = `<div class="form-generic-value">${escapeHtml(String(fieldValue))}</div>`;
        }
      } else {
        valueHtml = '<span class="form-value-empty">未填写</span>';
      }
    }
    
    // 如果有副文本（说明），添加到值后面
    if (hintText) {
      valueHtml += `<div class="form-field-hint">${escapeHtml(hintText)}</div>`;
      // 跳过下一个text字段，因为已经合并显示了
      index++;
    }
    
    // 构建字段HTML（移除类型标签）
    html += `
      <div class="form-field-item">
        <div class="form-field-header">
          <span class="form-field-name">${escapeHtml(fieldName)}</span>
        </div>
        <div class="form-field-value">
          ${valueHtml}
        </div>
      </div>
    `;
  }
  
  html += '</div>';
  return html;
}

// 关闭飞书审批实例弹窗
function closeLarkInstanceModal() {
  const modal = document.getElementById('larkInstanceModal');
  if (modal) {
    modal.style.display = 'none';
    document.body.style.overflow = 'auto';
  }
}

// 设计信息和审批信息弹窗功能（保留用于其他场景）
function showDesignInfoModal(design) {
  // 确保弹窗元素存在，如果不存在则创建
  let modal = document.getElementById('designInfoModal');
  if (!modal) {
    modal = createDesignInfoModal();
    document.body.appendChild(modal);
  }
  
  // 填充数据
  fillDesignInfoModal(design, modal);
  
  // 显示弹窗
  modal.style.display = 'flex';
  document.body.style.overflow = 'hidden';
}

// 创建设计信息弹窗元素
function createDesignInfoModal() {
  const modal = document.createElement('div');
  modal.id = 'designInfoModal';
  modal.className = 'modal-overlay';
  modal.style.display = 'none';
  
  modal.innerHTML = `
    <div class="modal-container design-info-modal">
      <div class="modal-header">
        <h3 class="modal-title">设计详情</h3>
        <button class="modal-close-btn" onclick="closeDesignInfoModal()" aria-label="关闭">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M18 6L6 18M6 6l12 12"/>
          </svg>
        </button>
      </div>
      <div class="modal-body design-info-modal-body">
        <div class="info-section" id="designInfoSection" style="display: none;">
          <div class="info-section-title">设计信息</div>
          <div class="info-section-content" id="designInfoContent"></div>
        </div>
        <div class="info-section" id="approvalInfoSection" style="display: none;">
          <div class="info-section-title">审批信息</div>
          <div class="info-section-content" id="approvalInfoContent"></div>
        </div>
      </div>
    </div>
  `;
  
  // 点击遮罩层关闭弹窗
  modal.addEventListener('click', function(e) {
    if (e.target === modal) {
      closeDesignInfoModal();
    }
  });
  
  return modal;
}

// 填充弹窗内容
function fillDesignInfoModal(design, modal) {
  // 处理设计信息
  const designInfoSection = modal.querySelector('#designInfoSection');
  const designInfoContent = modal.querySelector('#designInfoContent');
  
  if (design.design_info) {
    try {
      const designInfo = typeof design.design_info === 'string' 
        ? JSON.parse(design.design_info) 
        : design.design_info;
      
      // 格式化显示设计信息
      designInfoContent.innerHTML = formatJsonForDisplay(designInfo);
      designInfoSection.style.display = 'block';
    } catch (e) {
      // 如果不是JSON，直接显示文本
      designInfoContent.textContent = design.design_info;
      designInfoSection.style.display = 'block';
    }
  } else {
    designInfoSection.style.display = 'none';
  }
  
  // 处理审批信息
  const approvalInfoSection = modal.querySelector('#approvalInfoSection');
  const approvalInfoContent = modal.querySelector('#approvalInfoContent');
  
  if (design.approval_info) {
    try {
      const approvalInfo = typeof design.approval_info === 'string' 
        ? JSON.parse(design.approval_info) 
        : design.approval_info;
      
      // 格式化显示审批信息
      approvalInfoContent.innerHTML = formatJsonForDisplay(approvalInfo);
      approvalInfoSection.style.display = 'block';
    } catch (e) {
      // 如果不是JSON，直接显示文本
      approvalInfoContent.textContent = design.approval_info;
      approvalInfoSection.style.display = 'block';
    }
  } else {
    approvalInfoSection.style.display = 'none';
  }
  
  // 如果两个信息都为空，显示提示
  if (!design.design_info && !design.approval_info) {
    // 确保两个section都隐藏
    designInfoSection.style.display = 'none';
    approvalInfoSection.style.display = 'none';
    
    // 检查是否已有空状态提示，如果没有则添加
    let emptyInfo = modal.querySelector('.empty-info');
    if (!emptyInfo) {
      const modalBody = modal.querySelector('.design-info-modal-body');
      emptyInfo = document.createElement('div');
      emptyInfo.className = 'empty-info';
      emptyInfo.textContent = '暂无详细信息';
      modalBody.appendChild(emptyInfo);
    }
    emptyInfo.style.display = 'block';
  } else {
    // 如果有信息，隐藏空状态提示
    const emptyInfo = modal.querySelector('.empty-info');
    if (emptyInfo) {
      emptyInfo.style.display = 'none';
    }
  }
}

// 格式化JSON对象为可读的HTML
function formatJsonForDisplay(obj) {
  if (!obj || typeof obj !== 'object') {
    return escapeHtml(String(obj || ''));
  }
  
  const keys = Object.keys(obj);
  if (keys.length === 0) {
    return '<div class="empty-json">空对象</div>';
  }
  
  let html = '<div class="json-display">';
  keys.forEach(key => {
    const value = obj[key];
    let valueHtml = '';
    
    if (value === null || value === undefined) {
      valueHtml = '<span class="json-null">null</span>';
    } else if (typeof value === 'object') {
      if (Array.isArray(value)) {
        valueHtml = `<div class="json-array">[数组，共 ${value.length} 项]</div>`;
      } else {
        valueHtml = formatJsonForDisplay(value);
      }
    } else if (typeof value === 'string') {
      valueHtml = `<span class="json-string">${escapeHtml(value)}</span>`;
    } else if (typeof value === 'number' || typeof value === 'boolean') {
      valueHtml = `<span class="json-number">${escapeHtml(String(value))}</span>`;
    } else {
      valueHtml = escapeHtml(String(value));
    }
    
    html += `
      <div class="json-item">
        <span class="json-key">${escapeHtml(key)}:</span>
        <span class="json-value">${valueHtml}</span>
      </div>
    `;
  });
  html += '</div>';
  
  return html;
}

// 关闭设计信息弹窗
function closeDesignInfoModal() {
  const modal = document.getElementById('designInfoModal');
  if (modal) {
    modal.style.display = 'none';
    document.body.style.overflow = 'auto';
  }
}

// 设计详情弹窗功能
function showDesignDetailModal() {
  const modal = document.getElementById('designDetailModal');
  if (modal) {
    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
  }
}

function closeDesignDetailModal() {
  const modal = document.getElementById('designDetailModal');
  if (modal) {
    modal.style.display = 'none';
    document.body.style.overflow = 'auto';
  }
  
  // 返回全部设计页签
  showDesignListView();
  
  // 更新左侧导航状态
  sidebarItems.forEach(i => i.classList.remove('active'));
  const allDesignItem = Array.from(sidebarItems).find(item => item.textContent.includes('全部设计'));
  if (allDesignItem) {
    allDesignItem.classList.add('active');
  }
}

// 提交审批函数
function submitApproval() {
  const approvalType = document.getElementById('approvalType')?.value;
  const approvalTitle = document.getElementById('approvalTitle')?.value;
  const approvalDesc = document.getElementById('approvalDesc')?.value;
  const approvalRemark = document.getElementById('approvalRemark')?.value;
  
  if (!approvalTitle || !approvalDesc) {
    alert('请填写审批标题和审批描述');
    return;
  }
  
  console.log('提交审批:', {
    type: approvalType,
    title: approvalTitle,
    description: approvalDesc,
    remark: approvalRemark
  });
  
  alert('审批已提交成功!');
  closeDesignDetailModal();
}

// 页面加载完成提示
console.log('设计管理系统已加载完成');
console.log('- 支持搜索功能');
console.log('- 支持状态和类型筛选');
console.log('- 支持侧边栏导航');
console.log('- 支持卡片交互');
console.log('- 支持右侧边栏折叠');
console.log('- 支持文件上传和管理');
console.log('- 支持三区域瀑布式详情视图');
console.log('- 支持发起审批弹窗');
