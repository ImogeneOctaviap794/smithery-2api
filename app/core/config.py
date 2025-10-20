import os
import json
import logging
import base64
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional, Dict

# 获取一个日志记录器实例
logger = logging.getLogger(__name__)

# 全局标志，用于避免循环导入
_db_initialized = False

class AuthCookie:
    """
    处理并生成 Smithery.ai 所需的认证 Cookie。
    Cookie 可能包含多个分段（.0, .1 等），需要全部包含
    """
    def __init__(self, cookie_value: str):
        """
        cookie_value 格式：
        - 单段：base64-xxx
        - 多段（用 | 分隔）：base64-xxx|part1_value
        """
        # 检查是否有多段
        if '|' in cookie_value:
            parts = cookie_value.split('|')
            # 构造多段 Cookie
            cookie_parts = []
            for i, part in enumerate(parts):
                cookie_parts.append(f"sb-spjawbfpwezjfmicopsl-auth-token.{i}={part}")
            self.header_cookie_string = "; ".join(cookie_parts)
        else:
            # 单段 Cookie
            cookie_name = "sb-spjawbfpwezjfmicopsl-auth-token.0"
            self.header_cookie_string = f"{cookie_name}={cookie_value}"
        
        logger.debug(f"初始化 Cookie (长度: {len(self.header_cookie_string)})")

    def __repr__(self):
        return f"<AuthCookie>"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding='utf-8',
        extra="ignore"
    )

    APP_NAME: str = "smithery-2api"
    APP_VERSION: str = "1.0.0"
    DESCRIPTION: str = "一个将 smithery.ai 转换为兼容 OpenAI 格式 API 的高性能代理，支持多账号、上下文和工具调用。"

    CHAT_API_URL: str = "https://smithery.ai/api/chat"
    TOKEN_REFRESH_URL: str = "https://spjawbfpwezjfmicopsl.supabase.co/auth/v1/token?grant_type=refresh_token"
    SUPABASE_API_KEY: str = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNwamF3YmZwd2V6amZtaWNvcHNsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzQxNDc0MDUsImV4cCI6MjA0OTcyMzQwNX0.EBIg7_F2FZh4KZ3UNwZdBRjpp2fgHqXGJOvOSQ053MU"

    API_MASTER_KEY: Optional[str] = None
    
    AUTH_COOKIES: List[AuthCookie] = []

    API_REQUEST_TIMEOUT: int = 180
    NGINX_PORT: int = 8088
    SESSION_CACHE_TTL: int = 3600

    KNOWN_MODELS: List[str] = [
        "claude-haiku-4.5", "claude-sonnet-4.5", "gpt-5", "gpt-5-mini", 
        "gpt-5-nano", "gemini-2.5-flash-lite", "gemini-2.5-pro", "glm-4.6", 
        "grok-4-fast-non-reasoning", "grok-4-fast-reasoning", "kimi-k2", "deepseek-reasoner"
    ]

    def __init__(self, **values):
        super().__init__(**values)
        self._load_cookies()
    
    def _load_cookies_from_env(self):
        """从环境变量加载 Cookie（向后兼容）"""
        cookies = []
        i = 1
        while True:
            cookie_str = os.getenv(f"SMITHERY_COOKIE_{i}")
            if cookie_str:
                try:
                    cookies.append(AuthCookie(cookie_str))
                    logger.info(f"从环境变量加载 SMITHERY_COOKIE_{i}")
                except ValueError as e:
                    logger.warning(f"无法加载或解析 SMITHERY_COOKIE_{i}: {e}")
                i += 1
            else:
                break
        return cookies
    
    def _load_cookies_from_db(self):
        """从数据库加载启用的 Cookie"""
        global _db_initialized
        if not _db_initialized:
            return []
        
        try:
            from app.db.database import SessionLocal
            from app.db import crud
            
            db = SessionLocal()
            try:
                db_cookies = crud.get_active_cookies(db)
                cookies = []
                for db_cookie in db_cookies:
                    try:
                        cookies.append(AuthCookie(db_cookie.cookie_data))
                        logger.info(f"从数据库加载 Cookie: {db_cookie.name}")
                    except ValueError as e:
                        logger.warning(f"无法解析数据库中的 Cookie {db_cookie.name}: {e}")
                return cookies
            finally:
                db.close()
        except Exception as e:
            logger.error(f"从数据库加载 Cookie 失败: {e}")
            return []
    
    def _load_cookies(self):
        """加载 Cookie：优先从数据库，否则从环境变量"""
        # 先尝试从数据库加载
        db_cookies = self._load_cookies_from_db()
        
        if db_cookies:
            self.AUTH_COOKIES = db_cookies
            logger.info(f"从数据库加载了 {len(db_cookies)} 个 Cookie")
        else:
            # 如果数据库没有，从环境变量加载
            env_cookies = self._load_cookies_from_env()
            self.AUTH_COOKIES = env_cookies
            
            if env_cookies:
                logger.info(f"从环境变量加载了 {len(env_cookies)} 个 Cookie")
            else:
                logger.warning("未找到任何 Cookie 配置（数据库和环境变量均为空）")
    
    def reload_cookies(self):
        """重新加载 Cookie"""
        logger.info("重新加载 Cookie 配置...")
        self._load_cookies()
        logger.info(f"Cookie 重新加载完成，当前有 {len(self.AUTH_COOKIES)} 个可用")

settings = Settings()

def reload_cookies_from_db():
    """全局函数：重新从数据库加载 Cookie"""
    global settings
    settings.reload_cookies()

def mark_db_initialized():
    """标记数据库已初始化"""
    global _db_initialized
    _db_initialized = True
    # 初始化后立即尝试加载数据库中的 Cookie
    settings.reload_cookies()
