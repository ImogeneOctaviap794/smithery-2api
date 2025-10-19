from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.db.database import Base

class SmitheryCookie(Base):
    """Smithery Cookie 数据模型"""
    __tablename__ = "smithery_cookies"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    cookie_data = Column(Text(length=50000), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    usage_count = Column(Integer, default=0, nullable=False)  # 使用次数统计
    last_used_at = Column(DateTime, nullable=True)  # 最后使用时间
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # 关联调用日志
    call_logs = relationship("APICallLog", back_populates="cookie", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<SmitheryCookie(id={self.id}, name='{self.name}', usage_count={self.usage_count})>"


class APICallLog(Base):
    """API 调用日志"""
    __tablename__ = "api_call_logs"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    cookie_id = Column(Integer, ForeignKey("smithery_cookies.id"), nullable=False, index=True)
    model = Column(String(50), nullable=False, index=True)  # 使用的模型
    prompt_tokens = Column(Integer, default=0)  # 提示词 token 数
    completion_tokens = Column(Integer, default=0)  # 完成 token 数
    status = Column(String(20), default="success")  # success, error
    error_message = Column(Text, nullable=True)  # 错误信息
    duration_ms = Column(Integer, nullable=True)  # 请求耗时（毫秒）
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # 关联 Cookie
    cookie = relationship("SmitheryCookie", back_populates="call_logs")
    
    def __repr__(self):
        return f"<APICallLog(id={self.id}, model='{self.model}', status='{self.status}')>"

