import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# 数据库文件路径
DATABASE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
os.makedirs(DATABASE_DIR, exist_ok=True)
DATABASE_URL = f"sqlite:///{os.path.join(DATABASE_DIR, 'smithery.db')}"

# 创建数据库引擎
engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False},  # SQLite 特定配置
    echo=False  # 设置为 True 可以看到 SQL 语句
)

# 创建 SessionLocal 类
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建 Base 类
Base = declarative_base()

def get_db() -> Session:
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """初始化数据库，创建所有表"""
    from app.db.models import SmitheryCookie  # 导入模型以注册到 Base
    Base.metadata.create_all(bind=engine)

