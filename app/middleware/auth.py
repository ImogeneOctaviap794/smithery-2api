import uuid
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict
from fastapi import Header, HTTPException, Depends

logger = logging.getLogger(__name__)

# 简单的内存会话存储（生产环境建议使用 Redis）
_sessions: Dict[str, dict] = {}

# Session 过期时间（小时）
SESSION_EXPIRE_HOURS = 24

def create_session() -> str:
    """创建新的会话 token"""
    token = str(uuid.uuid4())
    _sessions[token] = {
        "created_at": datetime.utcnow(),
        "expires_at": datetime.utcnow() + timedelta(hours=SESSION_EXPIRE_HOURS)
    }
    logger.info(f"创建新会话: {token[:8]}...")
    return token

def validate_session(token: str) -> bool:
    """验证会话 token 是否有效"""
    if token not in _sessions:
        return False
    
    session = _sessions[token]
    if datetime.utcnow() > session["expires_at"]:
        # 会话已过期，删除
        del _sessions[token]
        logger.info(f"会话已过期: {token[:8]}...")
        return False
    
    return True

def invalidate_session(token: str) -> bool:
    """注销会话"""
    if token in _sessions:
        del _sessions[token]
        logger.info(f"注销会话: {token[:8]}...")
        return True
    return False

def cleanup_expired_sessions():
    """清理过期的会话"""
    now = datetime.utcnow()
    expired = [token for token, session in _sessions.items() if now > session["expires_at"]]
    for token in expired:
        del _sessions[token]
    if expired:
        logger.info(f"清理了 {len(expired)} 个过期会话")

async def verify_admin_session(authorization: Optional[str] = Header(None)) -> str:
    """验证管理员会话的依赖项"""
    if not authorization:
        raise HTTPException(status_code=401, detail="缺少认证令牌")
    
    # 支持 Bearer token 格式
    if authorization.lower().startswith("bearer "):
        token = authorization[7:]
    else:
        token = authorization
    
    # 清理过期会话
    cleanup_expired_sessions()
    
    if not validate_session(token):
        raise HTTPException(status_code=401, detail="无效或已过期的会话令牌")
    
    return token

