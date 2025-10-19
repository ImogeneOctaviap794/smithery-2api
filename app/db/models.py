from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from app.db.database import Base

class SmitheryCookie(Base):
    """Smithery Cookie 数据模型"""
    __tablename__ = "smithery_cookies"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    cookie_data = Column(Text(length=50000), nullable=False)  # 支持超长 Cookie
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<SmitheryCookie(id={self.id}, name='{self.name}', is_active={self.is_active})>"

