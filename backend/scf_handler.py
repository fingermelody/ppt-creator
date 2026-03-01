"""
SCF Web 函数入口
"""

import sys
import os

# 添加 layer 路径
layer_path = "/opt/python"
if os.path.exists(layer_path):
    sys.path.insert(0, layer_path)

# 添加用户代码路径
user_path = "/var/user"
if os.path.exists(user_path):
    sys.path.insert(0, user_path)

# 添加临时依赖路径
pip_packages = "/tmp/pip_packages"
if os.path.exists(pip_packages):
    sys.path.insert(0, pip_packages)

from mangum import Mangum
from app.main import app

# 创建 Mangum handler
handler = Mangum(app, lifespan="off")
