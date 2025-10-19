// API 调用封装

const API_BASE = '/api/admin';

/**
 * 通用 API 请求函数
 */
async function apiRequest(url, options = {}) {
    const token = getToken();
    
    const defaultHeaders = {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
    };
    
    const config = {
        ...options,
        headers: {
            ...defaultHeaders,
            ...options.headers
        }
    };
    
    try {
        const response = await fetch(url, config);
        
        // 如果是 401，说明未授权，跳转到登录页
        if (response.status === 401) {
            clearToken();
            window.location.href = '/admin/login.html';
            throw new Error('未授权，请重新登录');
        }
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.detail || data.message || '请求失败');
        }
        
        return data;
    } catch (error) {
        console.error('API 请求失败:', error);
        throw error;
    }
}

/**
 * 获取所有 Cookie
 */
async function getCookies() {
    return await apiRequest(`${API_BASE}/cookies`);
}

/**
 * 创建 Cookie
 */
async function createCookie(name, cookieData) {
    return await apiRequest(`${API_BASE}/cookies`, {
        method: 'POST',
        body: JSON.stringify({ name, cookie_data: cookieData })
    });
}

/**
 * 更新 Cookie
 */
async function updateCookie(id, name, cookieData) {
    const body = {};
    if (name !== undefined) body.name = name;
    if (cookieData !== undefined) body.cookie_data = cookieData;
    
    return await apiRequest(`${API_BASE}/cookies/${id}`, {
        method: 'PUT',
        body: JSON.stringify(body)
    });
}

/**
 * 删除 Cookie
 */
async function deleteCookie(id) {
    return await apiRequest(`${API_BASE}/cookies/${id}`, {
        method: 'DELETE'
    });
}

/**
 * 切换 Cookie 状态
 */
async function toggleCookie(id) {
    return await apiRequest(`${API_BASE}/cookies/${id}/toggle`, {
        method: 'PATCH'
    });
}

/**
 * 获取统计信息
 */
async function getStats() {
    return await apiRequest(`${API_BASE}/stats`);
}

/**
 * 获取 API 密钥
 */
async function getApiKey() {
    return await apiRequest(`${API_BASE}/api-key`);
}

