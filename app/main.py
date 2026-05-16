#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Football Quant OS - FastAPI入口
Naga Core v4.1 生产级服务化架构
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

from fastapi import FastAPI
from app.api import router

app = FastAPI(
    title="Football Quant OS",
    description="Naga Core 体育量化投资系统 - 生产级API",
    version="4.1.0"
)

app.include_router(router, prefix="/api/v1")

@app.get("/")
async def root():
    return {
        "status": "running",
        "system": "Football Quant OS",
        "version": "4.1.0",
        "engine": "Naga Core"
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "agents": 9, "models": 5}
