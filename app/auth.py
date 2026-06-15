#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
轻量认证模块 - P0 安全修复

规则：
- 开发模式 (AUTH_MODE=dev): localhost/127.0.0.1 免认证，其他需传 X-API-Key
- 生产模式 (AUTH_MODE=prod): 所有请求强制认证
- 白名单路径：/health, /docs, /openapi.json, /redoc 永远免认证

使用方式：
  from app.auth import require_auth
  
  @router.get("/protected")
  async def protected(request: Request, api_key: str = Depends(require_auth)):
      ...
"""

from fastapi import Request, HTTPException, Header, Depends
from fastapi.security import APIKeyHeader
from typing import Optional

from core.config import config

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


class AuthManager:
    """轻量认证管理器"""
    
    @staticmethod
    def is_localhost(request: Request) -> bool:
        """检查请求是否来自本地"""
        host = request.headers.get('host', '')
        remote_addr = request.client.host if request.client else ''
        return (
            host.startswith('localhost') or 
            host.startswith('127.0.0.1') or
            remote_addr == '127.0.0.1' or
            remote_addr == '::1'
        )
    
    @staticmethod
    def is_whitelist_path(path: str) -> bool:
        """检查路径是否在白名单"""
        return any(path.startswith(w) for w in config.AUTH_WHITELIST)
    
    @staticmethod
    def verify_key(api_key: str) -> bool:
        """验证 API Key"""
        if not api_key:
            return False
        valid_key = config.get_api_key()
        return api_key == valid_key
    
    @classmethod
    def require_auth(cls, request: Request, api_key: Optional[str] = Header(None, alias="X-API-Key")):
        """
        认证依赖注入函数
        
        使用方式：
            @router.get("/path")
            async def endpoint(request: Request, _=Depends(AuthManager.require_auth)):
                ...
        """
        # 1. 白名单路径免认证
        if cls.is_whitelist_path(request.url.path):
            return True
        
        # 2. 开发模式 + localhost 免认证
        if config.is_dev_mode() and cls.is_localhost(request):
            return True
        
        # 3. 验证 API Key
        if api_key and cls.verify_key(api_key):
            return True
        
        # 4. 认证失败
        mode_desc = "开发模式" if config.is_dev_mode() else "生产模式"
        raise HTTPException(
            status_code=401,
            detail={
                "error": "Unauthorized",
                "mode": config.AUTH_MODE,
                "message": f"当前为{mode_desc}，请提供有效的 X-API-Key",
                "hint": "Header: X-API-Key: your_key"
            }
        )


# 便捷导出
require_auth = AuthManager.require_auth


# ========== 输入验证工具 ==========

import re
from typing import Any


class InputValidator:
    """输入验证器"""
    
    # 安全的 match_id 格式：7-10位数字
    MATCH_ID_PATTERN = re.compile(r'^\d{7,10}$')
    
    # 安全的球队代码：2-4位大写字母
    TEAM_CODE_PATTERN = re.compile(r'^[A-Z]{2,4}$')
    
    # 日期格式：YYYY-MM-DD
    DATE_PATTERN = re.compile(r'^\d{4}-\d{2}-\d{2}$')
    
    # 防止路径遍历
    PATH_TRAVERSAL_PATTERN = re.compile(r'\.\.[\/\\]')
    
    @classmethod
    def validate_match_id(cls, match_id: str) -> str:
        """验证 match_id，防止 SSRF/路径遍历"""
        if not match_id or not isinstance(match_id, str):
            raise HTTPException(status_code=400, detail="match_id 不能为空")
        
        # 检查路径遍历
        if cls.PATH_TRAVERSAL_PATTERN.search(match_id):
            raise HTTPException(status_code=400, detail="match_id 包含非法字符")
        
        # 检查格式（如果是数字格式）
        if not cls.MATCH_ID_PATTERN.match(match_id):
            raise HTTPException(status_code=400, detail="match_id 格式应为 7-10 位数字")
        
        return match_id
    
    @classmethod
    def validate_team_code(cls, code: str) -> str:
        """验证球队代码"""
        if not code or not isinstance(code, str):
            raise HTTPException(status_code=400, detail="球队代码不能为空")
        
        code = code.upper().strip()
        
        if not cls.TEAM_CODE_PATTERN.match(code):
            raise HTTPException(status_code=400, detail="球队代码应为 2-4 位大写字母")
        
        return code
    
    @classmethod
    def validate_date(cls, date_str: str) -> str:
        """验证日期格式"""
        if not date_str or not isinstance(date_str, str):
            raise HTTPException(status_code=400, detail="日期不能为空")
        
        if not cls.DATE_PATTERN.match(date_str):
            raise HTTPException(status_code=400, detail="日期格式应为 YYYY-MM-DD")
        
        return date_str
    
    @classmethod
    def validate_odds(cls, odds: Any) -> dict:
        """验证赔率数据"""
        if not isinstance(odds, dict):
            raise HTTPException(status_code=400, detail="赔率数据应为字典")
        
        required_keys = ['home', 'draw', 'away']
        for key in required_keys:
            if key not in odds:
                raise HTTPException(status_code=400, detail=f"赔率数据缺少 {key}")
            
            val = odds[key]
            if not isinstance(val, (int, float)) or val <= 1.0:
                raise HTTPException(status_code=400, detail=f"{key} 赔率必须大于 1.0")
        
        return odds
    
    @classmethod
    def sanitize_string(cls, s: str, max_length: int = 100) -> str:
        """清理字符串输入"""
        if not isinstance(s, str):
            return ""
        
        # 截断过长输入
        s = s[:max_length]
        
        # 移除控制字符
        s = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', s)
        
        return s.strip()


# 便捷导出
validator = InputValidator()
