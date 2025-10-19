import json
import logging
import cloudscraper
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Body
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.config import settings
from app.db.database import get_db
from app.db import crud
from app.middleware.auth import create_session, verify_admin_session, invalidate_session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["admin"])

# ==================== Pydantic 模型 ====================

class LoginRequest(BaseModel):
    password: str

class LoginResponse(BaseModel):
    success: bool
    token: Optional[str] = None
    message: str

class CookieCreate(BaseModel):
    name: str
    cookie_data: str

class CookieUpdate(BaseModel):
    name: Optional[str] = None
    cookie_data: Optional[str] = None

class CookieResponse(BaseModel):
    id: int
    name: str
    cookie_data: str
    is_active: bool
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True

# ==================== 认证端点 ====================

@router.post("/auth/verify", response_model=LoginResponse)
async def verify_password(request: LoginRequest):
    """验证管理密码并返回会话 token"""
    if not settings.API_MASTER_KEY:
        raise HTTPException(status_code=500, detail="服务器未配置管理密钥")
    
    if request.password == settings.API_MASTER_KEY:
        token = create_session()
        logger.info("管理员登录成功")
        return LoginResponse(
            success=True,
            token=token,
            message="登录成功"
        )
    else:
        logger.warning("管理员登录失败：密码错误")
        raise HTTPException(status_code=401, detail="密码错误")

@router.post("/auth/logout")
async def logout(token: str = Depends(verify_admin_session)):
    """注销当前会话"""
    invalidate_session(token)
    return {"success": True, "message": "已注销"}

# ==================== Cookie 管理端点 ====================

@router.get("/cookies")
async def get_cookies(
    token: str = Depends(verify_admin_session),
    db: Session = Depends(get_db)
):
    """获取所有 Cookie 列表"""
    cookies = crud.get_all_cookies(db)
    stats = crud.get_cookie_count(db)
    
    return {
        "success": True,
        "data": [
            {
                "id": c.id,
                "name": c.name,
                "cookie_data": c.cookie_data,
                "is_active": c.is_active,
                "created_at": c.created_at.isoformat(),
                "updated_at": c.updated_at.isoformat()
            }
            for c in cookies
        ],
        "stats": stats
    }

@router.post("/cookies")
async def create_cookie(
    cookie: CookieCreate,
    token: str = Depends(verify_admin_session),
    db: Session = Depends(get_db)
):
    """创建新 Cookie"""
    try:
        db_cookie = crud.create_cookie(db, cookie.name, cookie.cookie_data)
        
        # 触发配置重新加载
        from app.core.config import reload_cookies_from_db
        reload_cookies_from_db()
        
        return {
            "success": True,
            "message": "Cookie 创建成功",
            "data": {
                "id": db_cookie.id,
                "name": db_cookie.name,
                "cookie_data": db_cookie.cookie_data,
                "is_active": db_cookie.is_active,
                "created_at": db_cookie.created_at.isoformat(),
                "updated_at": db_cookie.updated_at.isoformat()
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"创建 Cookie 失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"创建失败: {str(e)}")

@router.put("/cookies/{cookie_id}")
async def update_cookie(
    cookie_id: int,
    cookie: CookieUpdate,
    token: str = Depends(verify_admin_session),
    db: Session = Depends(get_db)
):
    """更新 Cookie"""
    try:
        db_cookie = crud.update_cookie(
            db, 
            cookie_id, 
            name=cookie.name, 
            cookie_data=cookie.cookie_data
        )
        
        if not db_cookie:
            raise HTTPException(status_code=404, detail="Cookie 不存在")
        
        # 触发配置重新加载
        from app.core.config import reload_cookies_from_db
        reload_cookies_from_db()
        
        return {
            "success": True,
            "message": "Cookie 更新成功",
            "data": {
                "id": db_cookie.id,
                "name": db_cookie.name,
                "cookie_data": db_cookie.cookie_data,
                "is_active": db_cookie.is_active,
                "created_at": db_cookie.created_at.isoformat(),
                "updated_at": db_cookie.updated_at.isoformat()
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"更新 Cookie 失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"更新失败: {str(e)}")

@router.delete("/cookies/{cookie_id}")
async def delete_cookie(
    cookie_id: int,
    token: str = Depends(verify_admin_session),
    db: Session = Depends(get_db)
):
    """删除 Cookie"""
    success = crud.delete_cookie(db, cookie_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Cookie 不存在")
    
    # 触发配置重新加载
    from app.core.config import reload_cookies_from_db
    reload_cookies_from_db()
    
    return {
        "success": True,
        "message": "Cookie 删除成功"
    }

@router.patch("/cookies/{cookie_id}/toggle")
async def toggle_cookie(
    cookie_id: int,
    token: str = Depends(verify_admin_session),
    db: Session = Depends(get_db)
):
    """切换 Cookie 启用/禁用状态"""
    db_cookie = crud.toggle_cookie_status(db, cookie_id)
    
    if not db_cookie:
        raise HTTPException(status_code=404, detail="Cookie 不存在")
    
    # 触发配置重新加载
    from app.core.config import reload_cookies_from_db
    reload_cookies_from_db()
    
    status = "启用" if db_cookie.is_active else "禁用"
    return {
        "success": True,
        "message": f"Cookie 已{status}",
        "data": {
            "id": db_cookie.id,
            "name": db_cookie.name,
            "is_active": db_cookie.is_active
        }
    }

@router.get("/stats")
async def get_stats(
    token: str = Depends(verify_admin_session),
    db: Session = Depends(get_db)
):
    """获取统计信息"""
    stats = crud.get_cookie_count(db)
    return {
        "success": True,
        "data": stats
    }

@router.get("/api-key")
async def get_api_key(
    token: str = Depends(verify_admin_session)
):
    """获取当前 API 密钥"""
    return {
        "success": True,
        "api_key": settings.API_MASTER_KEY or "未配置"
    }

