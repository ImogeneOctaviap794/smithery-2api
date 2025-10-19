// 主应用逻辑

let currentApiKey = '';
let currentTab = 'cookie';

// 页面加载时检查登录状态
document.addEventListener('DOMContentLoaded', () => {
    if (!checkAuth()) {
        return;
    }
    
    // 加载数据
    loadCookies();
    loadApiKey();
});

/**
 * Tab 切换
 */
function switchTab(tab) {
    currentTab = tab;
    
    // 更新 Tab 样式
    document.getElementById('cookieTab').classList.toggle('tab-active', tab === 'cookie');
    document.getElementById('logTab').classList.toggle('tab-active', tab === 'log');
    
    // 切换显示区域
    document.getElementById('cookieSection').classList.toggle('hidden', tab !== 'cookie');
    document.getElementById('logSection').classList.toggle('hidden', tab !== 'log');
    
    if (tab === 'log') {
        loadLogs();
    }
}

/**
 * 加载 API 密钥
 */
async function loadApiKey() {
    try {
        const response = await getApiKey();
        if (response.success) {
            currentApiKey = response.api_key;
        }
    } catch (error) {
        console.error('加载 API 密钥失败:', error);
    }
}

/**
 * 显示 API 密钥模态框
 */
async function showApiKeyModal() {
    if (!currentApiKey) {
        await loadApiKey();
    }
    document.getElementById('apiKeyDisplay').textContent = currentApiKey || '未配置';
    document.getElementById('apiKeyModal').showModal();
}

/**
 * 关闭 API 密钥模态框
 */
function closeApiKeyModal() {
    document.getElementById('apiKeyModal').close();
}

/**
 * 加载 Cookie 列表
 */
async function loadCookies() {
    try {
        const response = await getCookies();
        
        if (response.success) {
            // 更新统计信息
            updateStats(response.data, response.stats);
            
            // 渲染卡片列表
            renderCookieCards(response.data);
        }
    } catch (error) {
        showNotification('加载失败: ' + error.message, 'error');
    }
}

/**
 * 更新统计卡片
 */
function updateStats(cookies, stats) {
    document.getElementById('totalCount').textContent = stats.total;
    document.getElementById('activeCount').textContent = stats.active;
    
    // 计算总调用次数
    const totalCalls = cookies.reduce((sum, c) => sum + (c.usage_count || 0), 0);
    document.getElementById('totalCalls').textContent = totalCalls;
}

/**
 * 渲染 Cookie 卡片列表
 */
function renderCookieCards(cookies) {
    const container = document.getElementById('cookieList');
    
    if (cookies.length === 0) {
        container.innerHTML = `
            <div class="col-span-full text-center p-8 text-base-content/60">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-16 w-16 mx-auto mb-4 opacity-50" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
                </svg>
                <p class="text-lg">暂无 Cookie</p>
                <p class="text-sm mt-2">点击右上角按钮添加第一个 Cookie</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = cookies.map(cookie => `
        <div class="card bg-base-100 shadow-xl">
            <div class="card-body">
                <div class="flex justify-between items-start">
                    <h2 class="card-title">${escapeHtml(cookie.name)}</h2>
                    ${cookie.is_active 
                        ? '<span class="badge badge-success gap-2"><svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>启用</span>' 
                        : '<span class="badge badge-warning gap-2"><svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 9v6m4-6v6m7-3a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>禁用</span>'}
                </div>
                
                <div class="divider my-2"></div>
                
                <div class="stats stats-vertical shadow bg-base-200 w-full">
                    <div class="stat py-3">
                        <div class="stat-figure text-primary">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                            </svg>
                        </div>
                        <div class="stat-title">调用次数</div>
                        <div class="stat-value text-primary text-2xl">${cookie.usage_count || 0}</div>
                        <div class="stat-desc">${cookie.last_used_at ? '最后使用: ' + formatDateShort(cookie.last_used_at) : '从未使用'}</div>
                    </div>
                </div>
                
                <div class="text-sm text-base-content/60 mt-2">
                    <div class="flex items-center gap-2">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        创建于: ${formatDateShort(cookie.created_at)}
                    </div>
                </div>
                
                <div class="card-actions justify-end mt-4">
                    <button class="btn btn-sm btn-ghost" onclick="toggleCookieById(${cookie.id})" title="${cookie.is_active ? '禁用' : '启用'}">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="${cookie.is_active ? 'M10 9v6m4-6v6m7-3a9 9 0 11-18 0 9 9 0 0118 0z' : 'M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z'}" />
                        </svg>
                    </button>
                    <button class="btn btn-sm btn-error" onclick="deleteCookieById(${cookie.id})" title="删除">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                        </svg>
                    </button>
                </div>
            </div>
        </div>
    `).join('');
}

/**
 * 显示添加模态框
 */
function showAddModal() {
    document.getElementById('addName').value = '';
    document.getElementById('addCookieData').value = '';
    document.getElementById('addModal').showModal();
}

/**
 * 关闭添加模态框
 */
function closeAddModal() {
    document.getElementById('addModal').close();
}

/**
 * 提交添加
 */
async function submitAdd() {
    const name = document.getElementById('addName').value.trim();
    const cookieData = document.getElementById('addCookieData').value.trim();
    
    if (!name) {
        showNotification('请输入名称', 'warning');
        return;
    }
    
    if (!cookieData.startsWith('base64-') && !cookieData.startsWith('{')) {
        showNotification('Cookie 格式不正确，应该是 base64- 开头', 'error');
        return;
    }
    
    try {
        await createCookie(name, cookieData);
        showNotification('Cookie 添加成功', 'success');
        closeAddModal();
        loadCookies();
    } catch (error) {
        showNotification('添加失败: ' + error.message, 'error');
    }
}

/**
 * 删除 Cookie
 */
async function deleteCookieById(id) {
    if (!confirm('确定要删除这个 Cookie 吗？')) {
        return;
    }
    
    try {
        await deleteCookie(id);
        showNotification('Cookie 删除成功', 'success');
        loadCookies();
    } catch (error) {
        showNotification('删除失败: ' + error.message, 'error');
    }
}

/**
 * 切换 Cookie 状态
 */
async function toggleCookieById(id) {
    try {
        const response = await toggleCookie(id);
        showNotification(response.message, 'success');
        loadCookies();
    } catch (error) {
        showNotification('操作失败: ' + error.message, 'error');
    }
}

/**
 * 加载调用日志
 */
async function loadLogs() {
    try {
        const response = await getCallLogs();
        
        if (response.success) {
            renderLogTable(response.data);
        }
    } catch (error) {
        showNotification('加载日志失败: ' + error.message, 'error');
    }
}

/**
 * 刷新日志
 */
function refreshLogs() {
    loadLogs();
}

/**
 * 渲染日志表格
 */
function renderLogTable(logs) {
    const tbody = document.getElementById('logTableBody');
    
    if (logs.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6" class="text-center text-base-content/60 py-8">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-12 w-12 mx-auto mb-2 opacity-50" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    <p>暂无调用日志</p>
                </td>
            </tr>
        `;
        return;
    }
    
    tbody.innerHTML = logs.map(log => `
        <tr>
            <td class="whitespace-nowrap">${formatDateShort(log.created_at)}</td>
            <td><span class="badge badge-outline">${escapeHtml(log.cookie_name)}</span></td>
            <td><span class="badge badge-primary">${escapeHtml(log.model)}</span></td>
            <td>
                ${log.status === 'success' 
                    ? '<span class="badge badge-success gap-1"><svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" /></svg>成功</span>' 
                    : '<span class="badge badge-error gap-1"><svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>失败</span>'}
            </td>
            <td>${log.duration_ms ? log.duration_ms + 'ms' : '-'}</td>
            <td class="text-sm">${log.prompt_tokens || 0} / ${log.completion_tokens || 0}</td>
        </tr>
    `).join('');
}

/**
 * 显示通知 (使用 DaisyUI toast)
 */
function showNotification(message, type = 'info') {
    const alertTypes = {
        success: 'alert-success',
        error: 'alert-error',
        warning: 'alert-warning',
        info: 'alert-info'
    };
    
    // 创建 toast 容器（如果不存在）
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast toast-top toast-end';
        document.body.appendChild(container);
    }
    
    const alert = document.createElement('div');
    alert.className = `alert ${alertTypes[type] || alertTypes.info}`;
    alert.innerHTML = `<span>${escapeHtml(message)}</span>`;
    
    container.appendChild(alert);
    
    // 3秒后移除
    setTimeout(() => {
        alert.style.opacity = '0';
        alert.style.transition = 'opacity 0.3s';
        setTimeout(() => alert.remove(), 300);
    }, 3000);
}

/**
 * 格式化日期（简短）- 北京时间
 */
function formatDateShort(dateString) {
    if (!dateString) return '-';
    
    // 解析 UTC 时间
    const utcDate = new Date(dateString.endsWith('Z') ? dateString : dateString + 'Z');
    
    // 获取北京时间的当前时刻
    const now = new Date();
    const bjNow = new Date(now.toLocaleString('zh-CN', { timeZone: 'Asia/Shanghai' }));
    const bjDate = new Date(utcDate.toLocaleString('zh-CN', { timeZone: 'Asia/Shanghai' }));
    
    const diff = bjNow - bjDate;
    const seconds = Math.floor(diff / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);
    
    if (days > 7) {
        return utcDate.toLocaleString('zh-CN', {
            timeZone: 'Asia/Shanghai',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        });
    } else if (days > 0) {
        return `${days}天前`;
    } else if (hours > 0) {
        return `${hours}小时前`;
    } else if (minutes > 0) {
        return `${minutes}分钟前`;
    } else if (seconds > 5) {
        return `${seconds}秒前`;
    } else {
        return '刚刚';
    }
}

/**
 * 转义 HTML 特殊字符
 */
function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return String(text).replace(/[&<>"']/g, m => map[m]);
}
