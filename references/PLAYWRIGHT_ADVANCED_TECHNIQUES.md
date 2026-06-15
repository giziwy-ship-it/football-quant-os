# Playwright 高级技巧探索指南
# Football Quant OS - 反检测与生产级抓取

---

## 1. Stealth / 反检测

### 1.1 为什么要隐藏 Playwright 特征？

现代网站通过以下方式检测自动化工具：
- `navigator.webdriver` = true
- `window.chrome` 缺失
- plugins/languages 异常
- WebGL 指纹
- 行为分析（鼠标轨迹、滚动模式）

### 1.2 Stealth 实现

```python
# 1. 注入脚本隐藏 webdriver
page.add_init_script("""
    Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
    Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
    window.chrome = { runtime: {} };
""")

# 2. 启动参数禁用自动化标志
launch_args = [
    "--disable-blink-features=AutomationControlled",
    "--disable-web-security",
    "--disable-features=IsolateOrigins,site-per-process",
]

# 3. 使用 stealth 插件（社区方案）
# pip install playwright-stealth
from playwright_stealth import stealth_sync
stealth_sync(page)  # 一键应用所有 stealth 技巧
```

### 1.3 效果

| 检测项 | 原始 Playwright | Stealth 后 |
|--------|----------------|-----------|
| navigator.webdriver | true | undefined |
| plugins.length | 0 | 5 |
| chrome.runtime | undefined | {} |
| webdriver | 可检测 | 不可检测 |

---

## 2. 随机延迟 + 鼠标移动

### 2.1 为什么需要模拟真人？

反爬系统通过行为分析检测：
- 页面加载后瞬间点击 → 机器特征
- 鼠标轨迹直线 → 机器特征
- 滚动速度恒定 → 机器特征

### 2.2 实现

```python
def simulate_human_behavior(page: Page):
    # 随机鼠标移动（贝塞尔曲线模拟）
    for _ in range(random.randint(2, 5)):
        x = random.randint(100, 1800)
        y = random.randint(100, 900)
        page.mouse.move(x, y)
        time.sleep(random.uniform(0.1, 0.3))
    
    # 随机滚动（带加速/减速）
    scroll_amount = random.randint(200, 600)
    page.mouse.wheel(0, scroll_amount)
    time.sleep(random.uniform(0.2, 0.5))
    
    # 随机点击（可选）
    if random.random() > 0.7:
        page.click("body", position={"x": random.randint(100, 800), "y": random.randint(100, 600)})
```

### 2.3 高级：鼠标轨迹模拟

```python
from typing import List, Tuple

def bezier_curve(points: List[Tuple[int, int]], steps: int = 50) -> List[Tuple[int, int]]:
    """生成贝塞尔曲线轨迹点"""
    def interpolate(t: float, p0, p1, p2, p3):
        return (1-t)**3 * p0 + 3*(1-t)**2*t * p1 + 3*(1-t)*t**2 * p2 + t**3 * p3
    
    trajectory = []
    for i in range(steps):
        t = i / steps
        x = interpolate(t, points[0][0], points[1][0], points[2][0], points[3][0])
        y = interpolate(t, points[0][1], points[1][1], points[2][1], points[3][1])
        trajectory.append((int(x), int(y)))
    return trajectory

# 使用
start = (100, 100)
end = (500, 300)
control1 = (200, 400)  # 控制点1
control2 = (400, 100)  # 控制点2

for x, y in bezier_curve([start, control1, control2, end]):
    page.mouse.move(x, y)
    time.sleep(0.01)  # 每步10ms
```

---

## 3. 请求拦截

### 3.1 为什么拦截？

- 加速页面加载（不加载图片/字体）
- 节省带宽
- 避免不必要的资源消耗

### 3.2 实现

```python
# 拦截特定资源类型
BLOCKED_TYPES = ["image", "font", "media", "stylesheet"]
BLOCKED_PATTERNS = [r"\.(jpg|png|gif)$", r"google-analytics", r"googletagmanager"]

def handle_route(route: Route):
    if route.request.resource_type in BLOCKED_TYPES:
        route.abort()
        return
    
    for pattern in BLOCKED_PATTERNS:
        if re.search(pattern, route.request.url):
            route.abort()
            return
    
    route.continue_()

page.route("**/*", handle_route)
```

### 3.3 拦截效果

| 资源类型 | 拦截前加载时间 | 拦截后 | 节省 |
|---------|--------------|--------|------|
| 图片 | 2-5s | 0s | 100% |
| 字体 | 1-2s | 0s | 100% |
| CSS | 0.5-1s | 0s | 100% |
| JS/JSON | 0.5-2s | 0.5-2s | 0% |
| 总计 | 4-10s | 0.5-2s | 80-90% |

---

## 4. 多标签页 / Context

### 4.1 为什么用 Context？

- 隔离 cookies / storage（不同网站不串号）
- 并发抓取（多个标签页同时工作）
- 更快切换（无需重启浏览器）

### 4.2 实现

```python
# 创建多个 Context（隔离）
context1 = browser.new_context(user_agent="UA1")
context2 = browser.new_context(user_agent="UA2")

# 每个 Context 多个标签页
page1 = context1.new_page()
page2 = context1.new_page()

# 并发抓取（注意：500.com 可能需要串行）
from concurrent.futures import ThreadPoolExecutor

def fetch_match(match_id: str, context: BrowserContext) -> dict:
    page = context.new_page()
    try:
        page.goto(f"https://odds.500.com/fenxi/ouzhi-{match_id}.shtml")
        # 提取数据...
        return data
    finally:
        page.close()

# 使用线程池并发（同网站建议串行，不同网站可并发）
with ThreadPoolExecutor(max_workers=3) as executor:
    futures = [executor.submit(fetch_match, mid, context) for mid in match_ids]
    results = [f.result() for f in futures]
```

### 4.3 最佳实践

| 场景 | 推荐方式 | 原因 |
|------|----------|------|
| 同网站多比赛 | 串行 + 延迟 | 避免被封 |
| 不同网站 | 并行 + 不同 Context | 隔离 cookies |
| 大量数据 | 浏览器池 | 避免内存泄漏 |

---

## 5. 截图 + PDF

### 5.1 调试截图

```python
# 页面截图
page.screenshot(path="page.png", full_page=True)

# 元素截图
element = page.locator("table#datatb")
element.screenshot(path="odds_table.png")

# 错误时自动截图
try:
    page.goto(url)
except Exception:
    page.screenshot(path=f"error_{match_id}.png")
    raise
```

### 5.2 PDF 保存

```python
# 保存页面为 PDF
page.pdf(path="report.pdf", format="A4", margin={"top": "20mm", "bottom": "20mm"})
```

### 5.3 对项目的价值

| 功能 | 场景 | 价值 |
|------|------|------|
| 错误截图 | 反爬失败时查看页面状态 | 高 |
| 数据验证 | 对比提取数据与页面显示 | 高 |
| 报告生成 | 保存预测报告为 PDF | 中 |

---

## 6. 存储状态（cookies / localStorage）

### 6.1 为什么保存状态？

- 保持登录状态（无需每次登录）
- 保存验证码通过后的 session
- 避免重复人机验证

### 6.2 实现

```python
# 保存状态
context = browser.new_context()
page = context.new_page()
page.goto("https://odds.500.com")
# ... 登录或验证 ...

# 保存状态到文件
context.storage_state(path="auth_state.json")

# 后续使用保存的状态
context2 = browser.new_context(storage_state="auth_state.json")
page2 = context2.new_page()
# 已登录，无需再次验证
```

### 6.3 状态文件内容

```json
{
  "cookies": [
    {"name": "session_id", "value": "abc123", "domain": "odds.500.com"}
  ],
  "origins": [
    {
      "origin": "https://odds.500.com",
      "localStorage": [{"name": "user_pref", "value": "dark"}]
    }
  ]
}
```

---

## 7. 生产级最佳实践

### 7.1 错误处理金字塔

```
Level 1: 页面级重试（自动刷新）
Level 2: 请求级重试（指数退避）
Level 3: 浏览器级重试（重启浏览器）
Level 4: 代理级重试（切换 IP）
```

### 7.2 配置模板

```python
# 生产环境配置
PROD_CONFIG = FetcherConfig(
    headless=True,
    stealth=True,
    max_retries=5,
    retry_delay_base=3.0,
    intercept_resources=True,
    random_delay=True,
    mouse_movement=True,
    save_screenshot_on_error=True,
)

# 调试环境配置
DEBUG_CONFIG = FetcherConfig(
    headless=False,  # 有头模式，看浏览器操作
    stealth=True,
    max_retries=1,   # 不重试，快速失败
    intercept_resources=False,  # 全量加载，看页面效果
    save_screenshot_on_error=True,
)

# 轻量配置（快速测试）
LIGHT_CONFIG = FetcherConfig(
    headless=True,
    stealth=False,   # 不 stealth，更快
    max_retries=1,
    intercept_resources=True,
    random_delay=False,
    mouse_movement=False,
)
```

### 7.3 监控与日志

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/playwright.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('OddsFetcher')

# 在代码中使用
logger.info(f"Fetching match {match_id}, attempt {attempt}")
logger.warning(f"Rate limit detected, backing off for {delay}s")
logger.error(f"Failed to fetch match {match_id}: {error}")
```

---

## 8. 对 Football Quant OS 的价值

| 技巧 | 应用场景 | 优先级 |
|------|----------|--------|
| **Stealth** | 500.com 反爬 | 🔴 高 |
| **请求拦截** | 加速赔率加载 | 🔴 高 |
| **重试机制** | 网络不稳定时 | 🟡 中 |
| **鼠标模拟** | 复杂反爬网站 | 🟡 中 |
| **状态保存** | 需要登录的平台 | 🟢 低 |
| **并发抓取** | 多场比赛同时 | 🟢 低 |

---

## 9. 下一步建议

1. **测试 Stealth 效果** → 用检测网站验证特征是否隐藏
2. **基准测试** → 对比拦截前后的加载速度
3. **压力测试** → 连续抓取100场比赛，监控稳定性
4. **集成到 OddsPricingAgent** → 替换现有 requests 抓取

---

*文档版本: v1.0*
*生成时间: 2026-06-14*
*作者: Naga Playwright Team*
