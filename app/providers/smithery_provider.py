import json
import time
import logging
import uuid
import httpx
from typing import Dict, Any, AsyncGenerator, List

from fastapi import HTTPException
from fastapi.responses import StreamingResponse, JSONResponse

from app.core.config import settings
from app.providers.base_provider import BaseProvider
from app.utils.sse_utils import create_sse_data, create_chat_completion_chunk, DONE_CHUNK

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - [%(levelname)s] - %(message)s')
logger = logging.getLogger(__name__)

class SmitheryProvider(BaseProvider):
    def __init__(self):
        # 使用 httpx 异步客户端，启用 HTTP/2
        self.client = httpx.AsyncClient(
            http2=True,
            timeout=httpx.Timeout(180.0, connect=10.0),
            follow_redirects=True,
            limits=httpx.Limits(max_keepalive_connections=10, max_connections=100)
        )
        self.cookie_index = 0
        self.current_cookie_id = None  # 记录当前使用的 cookie ID
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    def _get_cookie(self) -> str:
        """从数据库轮换获取 Cookie 并记录使用"""
        try:
            from app.db.database import SessionLocal
            from app.db import crud
            
            db = SessionLocal()
            try:
                active_cookies = crud.get_active_cookies(db)
                
                if not active_cookies:
                    # 回退到环境变量
                    if settings.AUTH_COOKIES:
                        auth_cookie_obj = settings.AUTH_COOKIES[self.cookie_index]
                        self.cookie_index = (self.cookie_index + 1) % len(settings.AUTH_COOKIES)
                        self.current_cookie_id = None
                        return auth_cookie_obj.header_cookie_string
                    else:
                        raise HTTPException(
                            status_code=503,
                            detail="服务暂时不可用：未配置任何 Cookie。"
                        )
                
                # 轮询选择
                db_cookie = active_cookies[self.cookie_index % len(active_cookies)]
                self.cookie_index = (self.cookie_index + 1) % len(active_cookies)
                self.current_cookie_id = db_cookie.id
                
                # 构造 AuthCookie 对象
                from app.core.config import AuthCookie
                auth_cookie = AuthCookie(db_cookie.cookie_data)
                
                return auth_cookie.header_cookie_string
            finally:
                db.close()
        except Exception as e:
            logger.error(f"获取 Cookie 失败: {e}")
            raise HTTPException(status_code=503, detail=f"获取 Cookie 失败: {str(e)}")

    def _convert_messages_to_smithery_format(self, openai_messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        将客户端发来的 OpenAI 格式消息列表转换为 Smithery.ai 后端所需的格式。
        例如: {"role": "user", "content": "你好"} -> {"role": "user", "parts": [{"type": "text", "text": "你好"}]}
        """
        smithery_messages = []
        for msg in openai_messages:
            role = msg.get("role")
            content = msg.get("content", "")
            
            # 忽略格式不正确或内容为空的消息
            if not role or not isinstance(content, str):
                continue
                
            smithery_messages.append({
                "role": role,
                "parts": [{"type": "text", "text": content}],
                "id": f"msg-{uuid.uuid4().hex[:16]}"
            })
        return smithery_messages

    async def chat_completion(self, request_data: Dict[str, Any]) -> StreamingResponse:
        """
        处理聊天补全请求。
        此实现为无状态模式，完全依赖客户端发送的完整对话历史。
        """
        
        # 1. 直接从客户端请求中获取完整的消息历史
        messages_from_client = request_data.get("messages", [])
        
        # 2. 将其转换为 Smithery.ai 后端所需的格式
        smithery_formatted_messages = self._convert_messages_to_smithery_format(messages_from_client)
        
        # 3. 准备请求
        model = request_data.get("model", "claude-haiku-4.5")
        payload = self._prepare_payload(model, smithery_formatted_messages)
        headers = self._prepare_headers()
        
        request_id = f"chatcmpl-{uuid.uuid4()}"
        start_time = time.time()
        cookie_id = self.current_cookie_id

        async def stream_generator() -> AsyncGenerator[bytes, None]:
            completion_tokens = 0
            http_error_handled = False
            
            try:
                # 使用 httpx 异步发送流式请求
                async with self.client.stream(
                    "POST",
                    settings.CHAT_API_URL,
                    headers=headers,
                    json=payload,
                ) as response:
                    
                    # 检查认证和权限错误（在开始流式传输前）
                    if response.status_code == 401:
                        http_error_handled = True
                        logger.error("认证失败：Cookie 可能已过期")
                        raise HTTPException(status_code=401, detail="认证失败，Cookie可能已过期")
                    elif response.status_code == 403:
                        http_error_handled = True
                        logger.error("权限不足")
                        raise HTTPException(status_code=403, detail="权限不足")
                    elif response.status_code >= 400:
                        http_error_handled = True
                        error_text = await response.aread()
                        logger.error(f"Smithery API 错误: {response.status_code} - {error_text[:200]}")
                        raise HTTPException(
                            status_code=response.status_code,
                            detail=f"上游API错误 ({response.status_code}): {error_text[:100].decode('utf-8', errors='ignore')}"
                        )

                    # 流式处理 - 逐行实时转发
                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        
                        # 立即处理，不积累
                        if line.startswith("data:"):
                            content = line[5:].strip()
                            if content == "[DONE]":
                                break
                            try:
                                data = json.loads(content)
                                if data.get("type") == "text-delta":
                                    delta_content = data.get("delta", "")
                                    if delta_content:
                                        completion_tokens += len(delta_content)  # 粗略统计
                                        chunk_data = create_chat_completion_chunk(request_id, model, delta_content)
                                        yield create_sse_data(chunk_data)
                            except json.JSONDecodeError:
                                # 静默跳过无法解析的数据
                                pass
                
                    # 发送结束标志
                    final_chunk = create_chat_completion_chunk(request_id, model, "", "stop")
                    yield create_sse_data(final_chunk)
                    yield DONE_CHUNK
                    
                    # 记录成功调用日志
                    duration_ms = int((time.time() - start_time) * 1000)
                    self._log_api_call(cookie_id, model, len(str(messages_from_client)), completion_tokens, "success", None, duration_ms)

            except HTTPException:
                # HTTP 异常直接向上抛出，不包装成 SSE
                duration_ms = int((time.time() - start_time) * 1000)
                self._log_api_call(cookie_id, model, len(str(messages_from_client)), 0, "error", "HTTP错误", duration_ms)
                raise
            except Exception as e:
                # 只有流式传输中的错误才包装成 SSE 响应
                logger.error(f"流式传输错误: {e}", exc_info=True)
                error_message = f"流式传输错误: {str(e)}"
                error_chunk = create_chat_completion_chunk(request_id, model, error_message, "stop")
                yield create_sse_data(error_chunk)
                yield DONE_CHUNK
                
                # 记录失败日志
                duration_ms = int((time.time() - start_time) * 1000)
                self._log_api_call(cookie_id, model, len(str(messages_from_client)), 0, "error", str(e), duration_ms)

        return StreamingResponse(
            stream_generator(), 
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",  # 禁用 Nginx 缓冲
            }
        )

    def _prepare_headers(self) -> Dict[str, str]:
        """准备请求头，包含动态的用户ID和会话ID"""
        # 获取当前Cookie并解析用户ID
        cookie_str = self._get_cookie()
        
        # 尝试从当前使用的Cookie中获取用户ID
        user_id = None
        try:
            from app.db.database import SessionLocal
            from app.db import crud
            if self.current_cookie_id:
                db = SessionLocal()
                try:
                    db_cookie = crud.get_cookie_by_id(db, self.current_cookie_id)
                    if db_cookie:
                        from app.core.config import AuthCookie
                        auth_obj = AuthCookie(db_cookie.cookie_data)
                        user_id = auth_obj.user_id
                finally:
                    db.close()
        except:
            pass
        
        # 如果无法获取用户ID，使用默认值
        if not user_id:
            user_id = "00000000-0000-0000-0000-000000000000"
        
        # 生成随机的会话ID和窗口ID（ULID格式）
        import random
        session_id = f"019a{random.randint(1000, 9999):04x}-{random.randint(1000, 9999):04x}-{random.randint(1000, 9999):04x}-{random.randint(1000, 9999):04x}-{random.randint(100000000000, 999999999999):012x}"
        window_id = f"019a{random.randint(1000, 9999):04x}-{random.randint(1000, 9999):04x}-{random.randint(1000, 9999):04x}-{random.randint(1000, 9999):04x}-{random.randint(100000000000, 999999999999):012x}"
        
        # 模拟真实浏览器请求头
        return {
            "Accept": "*/*",
            "Accept-Language": "zh-CN,zh-TW;q=0.9,zh;q=0.8,en;q=0.7",
            "Cache-Control": "no-cache",
            "Content-Type": "application/json",
            "Cookie": cookie_str,
            "Origin": "https://smithery.ai",
            "Pragma": "no-cache",
            "Priority": "u=1, i",
            "Referer": "https://smithery.ai/chat",
            "Sec-Ch-Ua": '"Google Chrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"macOS"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
            "X-Posthog-Distinct-Id": user_id,
            "X-Posthog-Session-Id": session_id,
            "X-Posthog-Window-Id": window_id
        }

    def _prepare_payload(self, model: str, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        return {
            "messages": messages,
            "tools": [],
            "model": model,
            "systemPrompt": "You are a helpful assistant."
        }
    
    def _log_api_call(self, cookie_id, model, prompt_tokens, completion_tokens, status, error_message, duration_ms):
        """记录 API 调用日志到数据库"""
        if not cookie_id:
            return
        
        try:
            from app.db.database import SessionLocal
            from app.db import crud
            
            db = SessionLocal()
            try:
                # 创建调用日志
                crud.create_call_log(
                    db=db,
                    cookie_id=cookie_id,
                    model=model,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    status=status,
                    error_message=error_message,
                    duration_ms=duration_ms
                )
                
                # 更新 Cookie 使用计数
                crud.increment_cookie_usage(db, cookie_id)
                
                logger.info(f"记录调用日志: Cookie#{cookie_id}, Model={model}, Status={status}")
            finally:
                db.close()
        except Exception as e:
            logger.error(f"记录调用日志失败: {e}")

    async def get_models(self) -> JSONResponse:
        # 检查是否有可用的 Cookie
        if not settings.AUTH_COOKIES:
            raise HTTPException(
                status_code=503,
                detail="服务暂时不可用：未配置任何 Cookie。请通过管理页面 (http://localhost:8088/admin/) 添加 Cookie。"
            )
        
        model_data = {
            "object": "list",
            "data": [
                {"id": name, "object": "model", "created": int(time.time()), "owned_by": "lzA6"}
                for name in settings.KNOWN_MODELS
            ]
        }
        return JSONResponse(content=model_data)
