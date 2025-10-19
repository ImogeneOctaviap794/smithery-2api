// 主应用逻辑

let currentEditId = null;
let currentApiKey = '';

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
    document.getElementById('currentApiKey').value = currentApiKey || '未配置';
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
            updateStats(response.stats);
            
            // 渲染表格
            renderCookieTable(response.data);
        }
    } catch (error) {
        showToast('加载失败: ' + error.message, 'error');
    }
}

/**
 * 更新统计卡片
 */
function updateStats(stats) {
    document.getElementById('totalCount').textContent = stats.total;
    document.getElementById('activeCount').textContent = stats.active;
    document.getElementById('inactiveCount').textContent = stats.inactive;
}

/**
 * 渲染 Cookie 表格
 */
function renderCookieTable(cookies) {
    const tbody = document.getElementById('cookieTableBody');
    
    if (cookies.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6" class="text-center text-base-content/60">
                    暂无 Cookie，点击右上角按钮添加
                </td>
            </tr>
        `;
        return;
    }
    
    tbody.innerHTML = cookies.map(cookie => `
        <tr>
            <td>${cookie.id}</td>
            <td class="font-semibold">${escapeHtml(cookie.name)}</td>
            <td>
                ${cookie.is_active 
                    ? '<span class="badge badge-success">启用</span>' 
                    : '<span class="badge badge-warning">禁用</span>'}
            </td>
            <td>${formatDate(cookie.created_at)}</td>
            <td>${formatDate(cookie.updated_at)}</td>
            <td>
                <div class="flex gap-2">
                    <button class="btn btn-sm btn-warning" onclick="toggleCookieById(${cookie.id})" title="${cookie.is_active ? '禁用' : '启用'}">
                        ${cookie.is_active ? '⏸️' : '▶️'}
                    </button>
                    <button class="btn btn-sm btn-primary" onclick="editCookie(${cookie.id})" title="编辑">
                        ✏️
                    </button>
                    <button class="btn btn-sm btn-error" onclick="deleteCookieById(${cookie.id})" title="删除">
                        🗑️
                    </button>
                </div>
            </td>
        </tr>
    `).join('');
}

/**
 * 显示添加模态框
 */
function showAddModal() {
    currentEditId = null;
    document.getElementById('modalTitle').textContent = '添加 Cookie';
    document.getElementById('cookieId').value = '';
    document.getElementById('cookieName').value = '';
    document.getElementById('cookieData').value = '';
    document.getElementById('cookieModal').showModal();
}

/**
 * 编辑 Cookie
 */
async function editCookie(id) {
    try {
        const response = await getCookies();
        const cookie = response.data.find(c => c.id === id);
        
        if (!cookie) {
            showToast('Cookie 不存在', 'error');
            return;
        }
        
        currentEditId = id;
        document.getElementById('modalTitle').textContent = '编辑 Cookie';
        document.getElementById('cookieId').value = id;
        document.getElementById('cookieName').value = cookie.name;
        document.getElementById('cookieData').value = cookie.cookie_data;
        document.getElementById('cookieModal').showModal();
    } catch (error) {
        showToast('加载 Cookie 失败: ' + error.message, 'error');
    }
}

/**
 * 关闭模态框
 */
function closeModal() {
    document.getElementById('cookieModal').close();
}

/**
 * 保存 Cookie（表单提交）
 */
document.getElementById('cookieForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const name = document.getElementById('cookieName').value.trim();
    const cookieData = document.getElementById('cookieData').value.trim();
    
    // 验证格式（base64- 开头或者是 JSON）
    if (!cookieData.startsWith('base64-') && !cookieData.startsWith('{')) {
        showToast('Cookie 格式不正确，应该是 base64- 开头或 JSON 格式', 'error');
        return;
    }
    
    try {
        if (currentEditId) {
            // 更新
            await updateCookie(currentEditId, name, cookieData);
            showToast('Cookie 更新成功', 'success');
        } else {
            // 创建
            await createCookie(name, cookieData);
            showToast('Cookie 添加成功', 'success');
        }
        
        closeModal();
        loadCookies();
    } catch (error) {
        showToast('保存失败: ' + error.message, 'error');
    }
});

/**
 * 删除 Cookie
 */
async function deleteCookieById(id) {
    if (!confirm('确定要删除这个 Cookie 吗？')) {
        return;
    }
    
    try {
        await deleteCookie(id);
        showToast('Cookie 删除成功', 'success');
        loadCookies();
    } catch (error) {
        showToast('删除失败: ' + error.message, 'error');
    }
}

/**
 * 切换 Cookie 状态
 */
async function toggleCookieById(id) {
    try {
        const response = await toggleCookie(id);
        showToast(response.message, 'success');
        loadCookies();
    } catch (error) {
        showToast('操作失败: ' + error.message, 'error');
    }
}


/**
 * 显示 Toast 通知
 */
function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    
    const alertClasses = {
        success: 'alert-success',
        error: 'alert-error',
        warning: 'alert-warning',
        info: 'alert-info'
    };
    
    const icons = {
        success: '✅',
        error: '❌',
        warning: '⚠️',
        info: 'ℹ️'
    };
    
    const toast = document.createElement('div');
    toast.className = `alert ${alertClasses[type] || alertClasses.info} shadow-lg`;
    toast.innerHTML = `
        <div>
            <span>${icons[type] || icons.info} ${escapeHtml(message)}</span>
        </div>
    `;
    
    container.appendChild(toast);
    
    // 3秒后自动消失
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transition = 'opacity 0.3s';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

/**
 * 格式化日期
 */
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    });
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
    return text.replace(/[&<>"']/g, m => map[m]);
}

