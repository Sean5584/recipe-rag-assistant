"""
RAG系统配置文件
"""

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, Any

APP_DIR = Path(__file__).resolve().parent

@dataclass
class RAGConfig:
    """RAG系统配置类"""

    # 路径配置
    data_path: str = str(APP_DIR.parent / "data" / "recipes")
    index_save_path: str = str(APP_DIR / "vector_index" / "citations-v1")

    # 模型配置
    embedding_model: str = "BAAI/bge-small-zh-v1.5"
    llm_model: str = "kimi-k2.6"

    # 检索配置
    top_k: int = 3

    # 生成配置
    temperature: float = 1.0  # kimi-k2.6 仅接受 1.0
    max_tokens: int = 2048

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'RAGConfig':
        """从字典创建配置对象"""
        return cls(**config_dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)

# 默认配置实例
DEFAULT_CONFIG = RAGConfig()
