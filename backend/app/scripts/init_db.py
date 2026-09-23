"""数据库初始化脚本。

用法（在 backend 目录下执行）：
    python -m app.scripts.init_db

功能：建库建表 + 写入系统菜单 + 创建内置超级管理员（幂等）。
也可在应用启动时通过 AUTO_INIT_DB=True 自动执行。
"""

import logging

from app.models.seed import init_db_and_seed

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")

if __name__ == "__main__":
    init_db_and_seed()
    print("数据库初始化完成")