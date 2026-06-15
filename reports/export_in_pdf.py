import asyncio
from playwright.async_api import async_playwright

async def export_pdf():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto('http://localhost:8002/iran_nz_report_cn.html', wait_until='networkidle')
        await page.pdf(
            path=r'D:\openclaw-workspace\football_quant_os\reports\iran_nz_report_cn.pdf',
            format='A4',
            print_background=True,
            margin={'top': '20px', 'bottom': '20px', 'left': '20px', 'right': '20px'}
        )
        await browser.close()
        print('PDF exported successfully')

asyncio.run(export_pdf())
