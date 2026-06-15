"""
Football Quant OS - API 配置管理模块

统一管理所有外部 API 的 Token 和配置
支持环境变量、配置文件、代码注入三种方式
"""

import os
import json
from pathlib import Path
from typing import Dict, Optional
from dataclasses import dataclass, asdict


@dataclass
class APIConfig:
    """API 配置数据类"""
    api_football_key: Optional[str] = None
    football_data_org_key: Optional[str] = None
    api_football_base_url: str = "https://v3.football.api-sports.io"
    football_data_org_base_url: str = "https://api.football-data.org/v4"
    request_timeout: int = 30
    cache_ttl: int = 3600  # 缓存1小时
    rate_limit_delay: float = 1.0  # 请求间隔(秒)


class ConfigManager:
    """
    配置管理器
    
    加载顺序 (优先级从高到低):
    1. 环境变量 (API_FOOTBALL_KEY, FOOTBALL_DATA_ORG_KEY)
    2. 配置文件 (config/api_keys.json)
    3. 代码直接设置
    """
    
    CONFIG_FILE = Path(__file__).parent.parent / 'config' / 'api_keys.json'
    
    def __init__(self):
        self._config = APIConfig()
        self._load_from_env()
        self._load_from_file()
    
    def _load_from_env(self):
        """从环境变量加载"""
        self._config.api_football_key = os.getenv('API_FOOTBALL_KEY', self._config.api_football_key)
        self._config.football_data_org_key = os.getenv('FOOTBALL_DATA_ORG_KEY', self._config.football_data_org_key)
    
    def _load_from_file(self):
        """从配置文件加载"""
        if self.CONFIG_FILE.exists():
            try:
                with open(self.CONFIG_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 只更新非None的值
                if data.get('api_football_key') and not self._config.api_football_key:
                    self._config.api_football_key = data['api_football_key']
                if data.get('football_data_org_key') and not self._config.football_data_org_key:
                    self._config.football_data_org_key = data['football_data_org_key']
                if 'request_timeout' in data:
                    self._config.request_timeout = data['request_timeout']
                if 'cache_ttl' in data:
                    self._config.cache_ttl = data['cache_ttl']
            except Exception as e:
                print(f"ConfigManager: Failed to load config file: {e}")
    
    def save_to_file(self):
        """保存配置到文件"""
        self.CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(self.CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(asdict(self._config), f, indent=2, ensure_ascii=False)
    
    def set_api_key(self, service: str, key: str):
        """
        设置 API Key
        
        Args:
            service: 'api_football' 或 'football_data_org'
            key: API Key 字符串
        """
        if service == 'api_football':
            self._config.api_football_key = key
        elif service == 'football_data_org':
            self._config.football_data_org_key = key
        else:
            raise ValueError(f"Unknown service: {service}")
    
    def get_config(self) -> APIConfig:
        """获取当前配置"""
        return self._config
    
    def has_api_key(self, service: str) -> bool:
        """检查是否有 API Key"""
        if service == 'api_football':
            return bool(self._config.api_football_key)
        elif service == 'football_data_org':
            return bool(self._config.football_data_org_key)
        return False
    
    def get_api_key(self, service: str) -> Optional[str]:
        """获取 API Key"""
        if service == 'api_football':
            return self._config.api_football_key
        elif service == 'football_data_org':
            return self._config.football_data_org_key
        return None


# 全局配置实例
_config_manager = None

def get_config_manager() -> ConfigManager:
    """获取全局配置管理器"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


def configure_api_key(service: str, key: str, save: bool = True):
    """
    便捷函数：设置 API Key
    
    Args:
        service: 'api_football' 或 'football_data_org'
        key: API Key
        save: 是否保存到配置文件
    
    Example:
        configure_api_key('api_football', 'your-key-here')
        configure_api_key('football_data_org', 'your-key-here')
    """
    manager = get_config_manager()
    manager.set_api_key(service, key)
    if save:
        manager.save_to_file()
    print(f"API key for {service} configured successfully")


def check_api_status() -> Dict[str, bool]:
    """
    检查所有 API 配置状态
    
    Returns:
        {'api_football': True/False, 'football_data_org': True/False}
    """
    manager = get_config_manager()
    return {
        'api_football': manager.has_api_key('api_football'),
        'football_data_org': manager.has_api_key('football_data_org')
    }


# 创建配置模板文件
def create_config_template():
    """创建 API 配置模板"""
    template = {
        "api_football_key": "YOUR_API_FOOTBALL_KEY_HERE",
        "football_data_org_key": "YOUR_FOOTBALL_DATA_ORG_KEY_HERE",
        "request_timeout": 30,
        "cache_ttl": 3600,
        "rate_limit_delay": 1.0,
        "notes": {
            "api_football": "Get free key at https://www.api-football.com/ (100 calls/day)",
            "football_data_org": "Get free key at https://www.football-data.org/ (register required)",
            "rate_limit": "100 calls/day for API-Football free tier"
        }
    }
    
    template_file = Path(__file__).parent.parent / 'config' / 'api_keys_template.json'
    template_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(template_file, 'w', encoding='utf-8') as f:
        json.dump(template, f, indent=2, ensure_ascii=False)
    
    return template_file


if __name__ == '__main__':
    # 创建模板
    template_path = create_config_template()
    print(f"Config template created at: {template_path}")
    
    # 检查状态
    status = check_api_status()
    print(f"\nAPI Status:")
    for service, configured in status.items():
        icon = "OK" if configured else "OFF"
        print(f"  {icon} {service}: {'configured' if configured else 'not configured'}")
