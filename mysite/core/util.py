import yaml
import os
from pathlib import Path
import re
import logging


def load_yaml_file(path):
    with open(path, 'r') as f:
        res = yaml.safe_load(f)
    return res

def _write_file(path, file_content):
    root = os.path.split(path)[0]
    Path(root).mkdir(parents=True, exist_ok=True)
    logging.info(f'Writing text to {path}')
    with open(path, "w") as f:
        f.write(file_content)

def is_valid_email(email):
    # 定义邮箱格式的正则表达式
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    
    # 使用re.match()函数进行匹配
    if re.match(pattern, email):
        return True
    else:
        return False