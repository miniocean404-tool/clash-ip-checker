from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    """
    卸载 playwright 所有浏览器的命令: playwright uninstall
    """
    print("Chromium:", p.chromium.executable_path)
    print("Firefox:", p.firefox.executable_path)
    print("WebKit:", p.webkit.executable_path)


sync_playwright()
