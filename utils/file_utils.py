"""
파일 기본 처리 유틸리티
"""
import os
from typing import Dict, Any

def ensure_directory_exists(dir_path: str) -> None:
    """
    디렉토리가 없으면 생성
    
    Args:
        dir_path: 생성할 디렉토리 경로
    """
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
        print(f"디렉토리 생성: {dir_path}")