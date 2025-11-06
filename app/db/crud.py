import json
import logging
import base64
from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from app.db.models import SmitheryCookie, APICallLog

logger = logging.getLogger(__name__)

def _validate_cookie_format(cookie_data: str) -> bool:
    """验证 Cookie 格式是否正确（宽松验证）"""
    try:
        # 基本检查：非空且长度合理
        if not cookie_data or len(cookie_data) < 10:
            return False
        
        # 宽松验证：只要不是明显的错误格式即可
        return True
        
    except Exception as e:
        logger.error(f"Cookie 格式验证失败: {e}")
        return False

def get_all_cookies(db: Session) -> List[SmitheryCookie]:
    """获取所有 Cookie"""
    return db.query(SmitheryCookie).order_by(SmitheryCookie.created_at.desc()).all()

def get_active_cookies(db: Session) -> List[SmitheryCookie]:
    """获取所有启用的 Cookie"""
    return db.query(SmitheryCookie).filter(SmitheryCookie.is_active == True).order_by(SmitheryCookie.created_at.desc()).all()

def get_cookie_by_id(db: Session, cookie_id: int) -> Optional[SmitheryCookie]:
    """根据 ID 获取 Cookie"""
    return db.query(SmitheryCookie).filter(SmitheryCookie.id == cookie_id).first()

def get_cookie_by_name(db: Session, name: str) -> Optional[SmitheryCookie]:
    """根据名称获取 Cookie"""
    return db.query(SmitheryCookie).filter(SmitheryCookie.name == name).first()

def create_cookie(db: Session, name: str, cookie_data: str) -> SmitheryCookie:
    """创建新 Cookie"""
    # 验证格式
    if not _validate_cookie_format(cookie_data):
        raise ValueError("Cookie 格式不正确，应该是 base64- 开头或有效的 JSON 格式")
    
    # 检查名称是否已存在
    existing = get_cookie_by_name(db, name)
    if existing:
        raise ValueError(f"名称 '{name}' 已存在")
    
    db_cookie = SmitheryCookie(
        name=name,
        cookie_data=cookie_data,
        is_active=True
    )
    db.add(db_cookie)
    db.commit()
    db.refresh(db_cookie)
    logger.info(f"创建 Cookie: {name} (ID: {db_cookie.id})")
    return db_cookie

def update_cookie(db: Session, cookie_id: int, name: Optional[str] = None, cookie_data: Optional[str] = None) -> Optional[SmitheryCookie]:
    """更新 Cookie"""
    db_cookie = get_cookie_by_id(db, cookie_id)
    if not db_cookie:
        return None
    
    if name is not None:
        # 检查新名称是否与其他 Cookie 冲突
        existing = get_cookie_by_name(db, name)
        if existing and existing.id != cookie_id:
            raise ValueError(f"名称 '{name}' 已被使用")
        db_cookie.name = name
    
    if cookie_data is not None:
        # 验证格式
        if not _validate_cookie_format(cookie_data):
            raise ValueError("Cookie 格式不正确，应该是 base64- 开头或有效的 JSON 格式")
        db_cookie.cookie_data = cookie_data
    
    db_cookie.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_cookie)
    logger.info(f"更新 Cookie: {db_cookie.name} (ID: {cookie_id})")
    return db_cookie

def delete_cookie(db: Session, cookie_id: int) -> bool:
    """删除 Cookie"""
    db_cookie = get_cookie_by_id(db, cookie_id)
    if not db_cookie:
        return False
    
    db.delete(db_cookie)
    db.commit()
    logger.info(f"删除 Cookie: {db_cookie.name} (ID: {cookie_id})")
    return True

def toggle_cookie_status(db: Session, cookie_id: int) -> Optional[SmitheryCookie]:
    """切换 Cookie 启用/禁用状态"""
    db_cookie = get_cookie_by_id(db, cookie_id)
    if not db_cookie:
        return None
    
    db_cookie.is_active = not db_cookie.is_active
    db_cookie.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_cookie)
    status = "启用" if db_cookie.is_active else "禁用"
    logger.info(f"{status} Cookie: {db_cookie.name} (ID: {cookie_id})")
    return db_cookie

def get_cookie_count(db: Session) -> dict:
    """获取 Cookie 统计信息"""
    total = db.query(SmitheryCookie).count()
    active = db.query(SmitheryCookie).filter(SmitheryCookie.is_active == True).count()
    inactive = total - active
    return {
        "total": total,
        "active": active,
        "inactive": inactive
    }

def increment_cookie_usage(db: Session, cookie_id: int) -> None:
    """增加 Cookie 使用计数"""
    db_cookie = get_cookie_by_id(db, cookie_id)
    if db_cookie:
        db_cookie.usage_count += 1
        db_cookie.last_used_at = datetime.utcnow()
        db.commit()

def create_call_log(
    db: Session,
    cookie_id: int,
    model: str,
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
    status: str = "success",
    error_message: Optional[str] = None,
    duration_ms: Optional[int] = None
) -> APICallLog:
    """创建 API 调用日志"""
    log = APICallLog(
        cookie_id=cookie_id,
        model=model,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        status=status,
        error_message=error_message,
        duration_ms=duration_ms
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log

def get_call_logs(db: Session, limit: int = 100, cookie_id: Optional[int] = None) -> List[APICallLog]:
    """获取调用日志"""
    query = db.query(APICallLog).order_by(APICallLog.created_at.desc())
    if cookie_id:
        query = query.filter(APICallLog.cookie_id == cookie_id)
    return query.limit(limit).all()

def get_call_stats(db: Session) -> dict:
    """获取调用统计"""
    total_calls = db.query(APICallLog).count()
    success_calls = db.query(APICallLog).filter(APICallLog.status == "success").count()
    error_calls = total_calls - success_calls
    
    return {
        "total_calls": total_calls,
        "success_calls": success_calls,
        "error_calls": error_calls
    }

