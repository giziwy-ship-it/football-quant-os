#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
500.com 实时赔率抓取器 - Playwright 专业版 (v2.0)
高鲁棒性、反检测、生产就绪版本

升级特性:
- Context Manager 管理浏览器生命周期
- Stealth 模式（隐藏 Playwright 特征）
- 智能等待策略
- 错误重试 + 指数退避
- 无头/有头模式切换
- 结构化返回数据
- 请求拦截（加速加载）
- 随机延迟 + 鼠标移动模拟
"""

import argparse
import json
import random
import re
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable
from contextlib import contextmanager

from playwright.sync_api import (
    sync_playwright, TimeoutError as PlaywrightTimeout,
    Browser, BrowserContext, Page, Route
)


# ============================================================
# 配置类
# ============================================================

@dataclass
class FetcherConfig:
    """抓取器配置"""
    headless: bool = True
    stealth: bool = True
    timeout: int = 30000
    wait_until: str = "networkidle"
    max_retries: int = 3
    retry_delay_base: float = 2.0
    user_agent: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    viewport: Dict[str, int] = field(default_factory=lambda: {"width": 1920, "height": 1080})
    intercept_resources: bool = True  # 拦截图片/字体加速
    random_delay: bool = True
    mouse_movement: bool = True
    save_screenshot_on_error: bool = False
    screenshot_dir: str = "logs/screenshots"


# ============================================================
# Stealth 注入脚本
# ============================================================

STEALTH_SCRIPT = """
// 隐藏 Playwright 特征
Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
Object.defineProperty(navigator, 'languages', { get: () => ['zh-CN', 'zh', 'en'] });
window.chrome = { runtime: {} };
Object.defineProperty(window, 'chrome', { get: () => ({ runtime: {} }) });

// 覆盖 Permissions API
const originalQuery = window.navigator.permissions.query;
window.navigator.permissions.query = (parameters) => (
    parameters.name === 'notifications' 
        ? Promise.resolve({ state: Notification.permission })
        : originalQuery(parameters)
);

// 覆盖 WebGL 指纹
const getParameter = WebGLRenderingContext.prototype.getParameter;
WebGLRenderingContext.prototype.getParameter = function(parameter) {
    if (parameter === 37445) return 'Intel Inc.';
    if (parameter === 37446) return 'Intel Iris OpenGL Engine';
    return getParameter(parameter);
};
"""


# ============================================================
# 请求拦截器
# ============================================================

BLOCKED_RESOURCE_TYPES = [
    "image", "font", "media", "stylesheet"
]

BLOCKED_URL_PATTERNS = [
    re.compile(r"\.(jpg|jpeg|png|gif|webp|svg|ico)$", re.I),
    re.compile(r"\.(woff|woff2|ttf|otf|eot)$", re.I),
    re.compile(r"\.(mp3|mp4|wav|ogg|webm)$", re.I),
    re.compile(r"google-analytics"),
    re.compile(r"googletagmanager"),
    re.compile(r"doubleclick"),
    re.compile(r"facebook\\.com/tr"),
]


def should_block_route(route: Route) -> bool:
    """判断是否应该拦截请求"""
    resource_type = route.request.resource_type
    url = route.request.url
    
    if resource_type in BLOCKED_RESOURCE_TYPES:
        return True
    
    for pattern in BLOCKED_URL_PATTERNS:
        if pattern.search(url):
            return True
    
    return False


# ============================================================
# 主抓取器类
# ============================================================

class OddsFetcherPlaywrightPro:
    """Playwright 专业版赔率抓取器"""
    
    BASE = "https://odds.500.com/fenxi"
    
    def __init__(self, config: Optional[FetcherConfig] = None):
        self.config = config or FetcherConfig()
        self._playwright = None
        self._browser: Optional[Browser] = None
        
    # --------------------------------------------------------
    # Context Manager 支持
    # --------------------------------------------------------
    
    def __enter__(self):
        self._playwright = sync_playwright().start()
        launch_args = {
            "headless": self.config.headless,
            "args": [
                "--disable-blink-features=AutomationControlled",
                "--disable-web-security",
                "--disable-features=IsolateOrigins,site-per-process",
            ]
        }
        self._browser = self._playwright.chromium.launch(**launch_args)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._browser:
            self._browser.close()
        if self._playwright:
            self._playwright.stop()
    
    @contextmanager
    def _new_context(self) -> BrowserContext:
        """创建新的浏览器上下文（隔离 cookies/storage）"""
        if not self._browser:
            raise RuntimeError("Browser not initialized. Use 'with' statement.")
        
        context = self._browser.new_context(
            user_agent=self.config.user_agent,
            viewport=self.config.viewport,
            locale="zh-CN",
            timezone_id="Asia/Shanghai",
            geolocation={"latitude": 31.2304, "longitude": 121.4737},  # 上海
            permissions=["geolocation"],
            java_script_enabled=True,
        )
        
        try:
            yield context
        finally:
            context.close()
    
    # --------------------------------------------------------
    # 核心抓取方法
    # --------------------------------------------------------
    
    def fetch_european_odds(self, match_id: str) -> Dict[str, Any]:
        """
        抓取欧赔数据（带重试机制）
        
        Returns:
            {
                "match_id": str,
                "source": str,
                "success": bool,
                "average": {"home": float, "draw": float, "away": float} | None,
                "companies": [{"company": str, "home": float, "draw": float, "away": float}],
                "url": str,
                "fetched_at": str,
                "attempts": int,
                "stealth_applied": bool,
                "intercepted_resources": int,
                "error": str | None
            }
        """
        url = f"{self.BASE}/ouzhi-{match_id}.shtml"
        
        result = {
            "match_id": match_id,
            "source": "500.com (Playwright Pro v2.0)",
            "success": False,
            "average": None,
            "companies": [],
            "url": url,
            "fetched_at": datetime.now().isoformat(),
            "attempts": 0,
            "stealth_applied": self.config.stealth,
            "intercepted_resources": 0,
            "error": None
        }
        
        for attempt in range(1, self.config.max_retries + 1):
            result["attempts"] = attempt
            try:
                with self._new_context() as context:
                    page = context.new_page()
                    
                    # 设置请求拦截
                    if self.config.intercept_resources:
                        intercepted_count = [0]
                        def handle_route(route: Route):
                            if should_block_route(route):
                                intercepted_count[0] += 1
                                route.abort()
                            else:
                                route.continue_()
                        page.route("**/*", handle_route)
                    
                    # 注入 Stealth 脚本
                    if self.config.stealth:
                        page.add_init_script(STEALTH_SCRIPT)
                    
                    # 随机延迟（模拟真人）
                    if self.config.random_delay:
                        time.sleep(random.uniform(0.5, 2.0))
                    
                    # 导航到页面
                    page.goto(url, wait_until=self.config.wait_until, timeout=self.config.timeout)
                    
                    # 模拟鼠标移动（反检测）
                    if self.config.mouse_movement:
                        self._simulate_human_behavior(page)
                    
                    # 智能等待策略
                    self._smart_wait(page)
                    
                    # 提取数据
                    data = self._extract_odds_data(page)
                    
                    if data["average"] or data["companies"]:
                        result.update(data)
                        result["success"] = True
                        if self.config.intercept_resources:
                            result["intercepted_resources"] = intercepted_count[0]
                        return result
                    
                    # 数据为空，可能是反爬阻止
                    raise ValueError("No odds data found on page")
                    
            except Exception as e:
                result["error"] = f"Attempt {attempt}: {str(e)}"
                
                # 截图保存（调试用）
                if self.config.save_screenshot_on_error and 'page' in locals():
                    self._save_screenshot(page, match_id, attempt)
                
                if attempt < self.config.max_retries:
                    # 指数退避
                    delay = self.config.retry_delay_base * (2 ** (attempt - 1))
                    delay += random.uniform(0, 1)  # 添加 jitter
                    time.sleep(delay)
                else:
                    break
        
        return result
    
    # --------------------------------------------------------
    # 辅助方法
    # --------------------------------------------------------
    
    def _simulate_human_behavior(self, page: Page):
        """模拟人类行为：鼠标移动、随机滚动"""
        try:
            # 随机鼠标移动
            for _ in range(random.randint(2, 5)):
                x = random.randint(100, 1800)
                y = random.randint(100, 900)
                page.mouse.move(x, y)
                time.sleep(random.uniform(0.1, 0.3))
            
            # 随机滚动
            scroll_amount = random.randint(200, 600)
            page.mouse.wheel(0, scroll_amount)
            time.sleep(random.uniform(0.2, 0.5))
            
        except Exception:
            pass  # 模拟行为失败不影响主流程
    
    def _smart_wait(self, page: Page):
        """智能等待策略"""
        # 策略1: 等待特定选择器
        selectors = [
            "table#datatb",
            "tr:has-text('平均')",
            "[class*='ouzhi']",
            "[class*='odds']"
        ]
        
        for selector in selectors:
            try:
                page.wait_for_selector(selector, timeout=5000)
                return
            except PlaywrightTimeout:
                continue
        
        # 策略2: 等待网络空闲
        page.wait_for_load_state("networkidle", timeout=5000)
    
    def _extract_odds_data(self, page: Page) -> Dict[str, Any]:
        """从页面提取赔率数据"""
        data = {"average": None, "companies": []}
        
        # 使用 page.evaluate 直接提取（比 BeautifulSoup 更快）
        odds_data = page.evaluate("""
            () => {
                const result = { average: null, companies: [] };
                
                // 查找平均赔率行
                const rows = document.querySelectorAll('tr');
                for (const row of rows) {
                    const text = row.textContent || '';
                    if (text.includes('平均') || text.includes('Avg')) {
                        const cells = row.querySelectorAll('td');
                        if (cells.length >= 4) {
                            const nums = [];
                            for (const cell of cells) {
                                const val = parseFloat(cell.textContent);
                                if (!isNaN(val) && val > 1) nums.push(val);
                            }
                            if (nums.length >= 3) {
                                result.average = { home: nums[0], draw: nums[1], away: nums[2] };
                                result.companies.push({
                                    company: '平均', home: nums[0], draw: nums[1], away: nums[2]
                                });
                            }
                        }
                        break;
                    }
                }
                
                return result;
            }
        """)
        
        if odds_data and odds_data.get("average"):
            data["average"] = odds_data["average"]
            data["companies"] = odds_data.get("companies", [])
        
        # Fallback: 使用正则表达式提取
        if not data["average"]:
            html = page.content()
            nums = re.findall(r'(\d+\.\d{2})', html)
            if len(nums) >= 3:
                data["average"] = {
                    "home": float(nums[0]),
                    "draw": float(nums[1]),
                    "away": float(nums[2])
                }
        
        return data
    
    def _save_screenshot(self, page: Page, match_id: str, attempt: int):
        """保存错误截图"""
        import os
        os.makedirs(self.config.screenshot_dir, exist_ok=True)
        path = f"{self.config.screenshot_dir}/error_{match_id}_attempt{attempt}.png"
        try:
            page.screenshot(path=path, full_page=True)
        except Exception:
            pass
    
    # --------------------------------------------------------
    # 便捷方法
    # --------------------------------------------------------
    
    def get_odds(self, match_id: str) -> Dict[str, Any]:
        """便捷入口"""
        return self.fetch_european_odds(match_id)
    
    def get_odds_batch(self, match_ids: List[str]) -> List[Dict[str, Any]]:
        """批量抓取（串行，避免被封）"""
        results = []
        for i, match_id in enumerate(match_ids):
            if i > 0:
                time.sleep(random.uniform(2, 5))  # 批次间延迟
            result = self.get_odds(match_id)
            results.append(result)
        return results


# ============================================================
# 快捷函数（无需 Context Manager）
# ============================================================

def fetch_odds(match_id: str, **kwargs) -> Dict[str, Any]:
    """
    快捷抓取函数（自动管理浏览器生命周期）
    
    Args:
        match_id: 比赛ID
        **kwargs: 传给 FetcherConfig 的参数
        
    Returns:
        赔率数据字典
    """
    config = FetcherConfig(**kwargs)
    with OddsFetcherPlaywrightPro(config) as fetcher:
        return fetcher.get_odds(match_id)


# ============================================================
# CLI
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="500.com 赔率抓取器 - Playwright Pro v2.0")
    parser.add_argument('--match-id', required=True, help='比赛ID (如: 1359233)')
    parser.add_argument('--format', choices=['json', 'text'], default='json')
    parser.add_argument('--headless', action='store_true', default=True, help='无头模式')
    parser.add_argument('--no-headless', action='store_true', dest='headless', const=False, 
                        nargs=0, help='有头模式（调试用）')
    parser.add_argument('--stealth', action='store_true', default=True, help='启用 stealth')
    parser.add_argument('--no-stealth', action='store_true', dest='stealth', const=False,
                        nargs=0, help='禁用 stealth')
    parser.add_argument('--max-retries', type=int, default=3, help='最大重试次数')
    parser.add_argument('--intercept', action='store_true', default=True, help='拦截资源')
    parser.add_argument('--no-intercept', action='store_true', dest='intercept', const=False,
                        nargs=0, help='不拦截资源')
    parser.add_argument('--screenshot-on-error', action='store_true', default=False,
                        help='错误时保存截图')
    
    args = parser.parse_args()
    
    config = FetcherConfig(
        headless=args.headless,
        stealth=args.stealth,
        max_retries=args.max_retries,
        intercept_resources=args.intercept,
        save_screenshot_on_error=args.screenshot_on_error
    )
    
    print(f"[Config] headless={config.headless}, stealth={config.stealth}, "
          f"retries={config.max_retries}, intercept={config.intercept_resources}")
    
    with OddsFetcherPlaywrightPro(config) as fetcher:
        result = fetcher.get_odds(args.match_id)
    
    if args.format == 'json':
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"Match: {result['match_id']}")
        print(f"Success: {result['success']}")
        if result['average']:
            print(f"Average Odds: {result['average']['home']} / "
                  f"{result['average']['draw']} / {result['average']['away']}")
        print(f"Attempts: {result['attempts']}")
        if result['error']:
            print(f"Error: {result['error']}")


if __name__ == '__main__':
    main()
