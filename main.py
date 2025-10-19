import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Request, HTTPException, Depends, Header
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import settings, mark_db_initialized
from app.providers.smithery_provider import SmitheryProvider
from app.routers import admin
from app.db.database import init_db

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

provider = SmitheryProvider()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"应用启动中... {settings.APP_NAME} v{settings.APP_VERSION}")
    
    # 初始化数据库
    logger.info("初始化数据库...")
    init_db()
    mark_db_initialized()
    logger.info("数据库初始化完成")
    
    # 检查 Cookie 配置
    if not settings.AUTH_COOKIES:
        logger.warning("=" * 80)
        logger.warning("⚠️  未找到任何 Cookie 配置")
        logger.warning("请访问管理页面添加 Cookie 后才能使用 API 功能")
        logger.warning(f"管理页面地址: http://localhost:{settings.NGINX_PORT}/admin/login.html")
        logger.warning("=" * 80)
    else:
        logger.info(f"✅ 已加载 {len(settings.AUTH_COOKIES)} 个 Cookie")
    
    logger.info("服务已进入 'Cloudscraper' 模式，将自动处理 Cloudflare 挑战。")
    logger.info(f"🚀 服务已启动: http://localhost:{settings.NGINX_PORT}")
    logger.info(f"📋 管理页面: http://localhost:{settings.NGINX_PORT}/admin/login.html")
    logger.info(f"📖 API 文档: http://localhost:{settings.NGINX_PORT}/docs")
    yield
    logger.info("应用关闭。")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=settings.DESCRIPTION,
    lifespan=lifespan
)

# 注册管理 API 路由
app.include_router(admin.router)

# 挂载静态文件
import os
static_dir = os.path.join(os.path.dirname(__file__), "app", "static")
if os.path.exists(static_dir):
    app.mount("/admin", StaticFiles(directory=static_dir, html=True), name="static")

async def verify_api_key(authorization: Optional[str] = Header(None)):
    if not settings.API_MASTER_KEY:
        raise HTTPException(status_code=503, detail="服务未配置 API 密钥")
    
    if not authorization or "bearer" not in authorization.lower():
        raise HTTPException(status_code=401, detail="需要 Bearer Token 认证")
    
    token = authorization.split(" ")[-1]
    if token != settings.API_MASTER_KEY:
        raise HTTPException(status_code=403, detail="无效的 API Key")

@app.post("/v1/chat/completions", dependencies=[Depends(verify_api_key)])
async def chat_completions(request: Request) -> StreamingResponse:
    try:
        request_data = await request.json()
        return await provider.chat_completion(request_data)
    except Exception as e:
        logger.error(f"处理聊天请求时发生顶层错误: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"内部服务器错误: {str(e)}")

@app.get("/v1/models", dependencies=[Depends(verify_api_key)], response_class=JSONResponse)
async def list_models():
    return await provider.get_models()

@app.get("/", summary="根路径")
def root():
    cookie_count = len(settings.AUTH_COOKIES)
    return {
        "message": f"欢迎来到 {settings.APP_NAME} v{settings.APP_VERSION}",
        "status": "running",
        "cookies_configured": cookie_count,
        "admin_panel": f"http://localhost:{settings.NGINX_PORT}/admin/login.html",
        "note": "请访问管理页面添加 Cookie" if cookie_count == 0 else "服务运行正常"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8088)
