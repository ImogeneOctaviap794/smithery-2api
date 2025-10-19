// 认证相关函数

/**
 * 获取存储的 token
 */
function getToken() {
    return localStorage.getItem('admin_token');
}

/**
 * 保存 token
 */
function saveToken(token) {
    localStorage.setItem('admin_token', token);
}

/**
 * 清除 token
 */
function clearToken() {
    localStorage.removeItem('admin_token');
}

/**
 * 检查是否已登录
 */
function isLoggedIn() {
    return !!getToken();
}

/**
 * 登出
 */
async function logout() {
    const token = getToken();
    
    if (token) {
        try {
            await fetch('/api/admin/auth/logout', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
        } catch (error) {
            console.error('登出请求失败:', error);
        }
    }
    
    clearToken();
    window.location.href = '/admin/login.html';
}

/**
 * 检查登录状态并重定向
 */
function checkAuth() {
    if (!isLoggedIn()) {
        window.location.href = '/admin/login.html';
        return false;
    }
    return true;
}

