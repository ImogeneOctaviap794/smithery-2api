#!/usr/bin/env python3
"""
数据库迁移脚本
用于从旧版本数据库升级到新版本（添加 usage_count 和 last_used_at 字段）
"""

import sqlite3
import sys
from pathlib import Path

DB_PATH = "data/smithery.db"

def migrate():
    if not Path(DB_PATH).exists():
        print("数据库文件不存在，跳过迁移")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # 检查列是否已存在
        cursor.execute("PRAGMA table_info(smithery_cookies)")
        columns = [row[1] for row in cursor.fetchall()]
        
        # 添加 usage_count 列
        if 'usage_count' not in columns:
            print("添加 usage_count 列...")
            cursor.execute("ALTER TABLE smithery_cookies ADD COLUMN usage_count INTEGER DEFAULT 0 NOT NULL")
            print("✓ usage_count 列添加成功")
        else:
            print("usage_count 列已存在")
        
        # 添加 last_used_at 列
        if 'last_used_at' not in columns:
            print("添加 last_used_at 列...")
            cursor.execute("ALTER TABLE smithery_cookies ADD COLUMN last_used_at DATETIME")
            print("✓ last_used_at 列添加成功")
        else:
            print("last_used_at 列已存在")
        
        # 创建 api_call_logs 表（如果不存在）
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS api_call_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cookie_id INTEGER NOT NULL,
                model VARCHAR(50) NOT NULL,
                prompt_tokens INTEGER DEFAULT 0,
                completion_tokens INTEGER DEFAULT 0,
                status VARCHAR(20) DEFAULT 'success',
                error_message TEXT,
                duration_ms INTEGER,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (cookie_id) REFERENCES smithery_cookies (id) ON DELETE CASCADE
            )
        """)
        print("✓ api_call_logs 表检查/创建成功")
        
        # 创建索引
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_call_logs_cookie_id ON api_call_logs(cookie_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_call_logs_model ON api_call_logs(model)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_call_logs_created_at ON api_call_logs(created_at)")
        print("✓ 索引创建成功")
        
        conn.commit()
        print("\n数据库迁移完成！")
        
    except Exception as e:
        print(f"迁移失败: {e}", file=sys.stderr)
        conn.rollback()
        sys.exit(1)
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()

