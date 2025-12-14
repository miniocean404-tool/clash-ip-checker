import asyncio
import re

import aiohttp
from playwright.async_api import async_playwright


class IPChecker:
    """
    IP 检测器类，用于检查代理节点的 IP 质量和属性。

    主要功能：
    - 通过多个服务检测当前 IP 地址
    - 获取 IPPure 系数和 Bot 流量比
    - 查询 IP 归属地和属性信息
    - 支持结果缓存以提高效率
    """

    def __init__(self, headless=True):
        """
        初始化 IP 检测器。

        参数:
            headless: 是否使用无头模式运行浏览器，默认 True（后台运行）
        """
        self.headless = headless
        self.browser = None
        self.playwright = None
        self.cache = {}  # IP -> 检测结果字典的映射

    async def start(self):
        """
        启动 Playwright 浏览器实例。

        必须在调用 check () 方法前执行此方法。
        """
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=self.headless, args=["--no-sandbox", "--disable-setuid-sandbox"])

    async def stop(self):
        """
        停止并清理浏览器实例。

        在完成所有检测后应调用此方法释放资源。
        """
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    def get_emoji(self, percentage_str):
        """
        根据百分比值返回对应的 emoji 表情。

        用于直观展示 IP 质量等级：
        - ⚪ 优秀 (≤10%)
        - 🟢 良好 (≤30%)
        - 🟡 一般 (≤50%)
        - 🟠 较差 (≤70%)
        - 🔴 很差 (≤90%)
        - ⚫ 极差 (>90%)

        参数:
            percentage_str: 百分比字符串，如 "25%"

        返回:
            str: 对应的 emoji 字符
        """
        try:
            val = float(percentage_str.replace("%", ""))
            # 用户认可的阈值逻辑
            if val <= 10:
                return "⚪"
            if val <= 30:
                return "🟢"
            if val <= 50:
                return "🟡"
            if val <= 70:
                return "🟠"
            if val <= 90:
                return "🔴"
            return "⚫"
        except (ValueError, AttributeError):
            return "❓"

    async def get_simple_ip(self, proxy=None):
        """
        快速获取 IPv4 地址，用于缓存检查。

        参数:
            proxy: 代理服务器 URL，如 "http://127.0.0.1:7890"

        返回:
            str: IP 地址字符串，获取失败返回 None
        """
        urls = ["http://api.ipify.org", "http://v4.ident.me"]
        for url in urls:
            try:
                # 用户修改超时为 3 秒
                timeout = aiohttp.ClientTimeout(total=3)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.get(url, proxy=proxy) as resp:
                        if resp.status == 200:
                            ip = (await resp.text()).strip()
                            if re.match(r"^\d {1,3}(\.\d {1,3}){3}\d {1,3}$", ip):
                                return ip
            except Exception:
                continue
        return None

    async def check(self, url="https://ippure.com/", proxy=None, timeout=20000):
        """
        执行完整的 IP 质量检测。

        检测流程：
        1. 快速获取 IP 并检查缓存
        2. 使用浏览器访问检测网站
        3. 解析 IPPure 系数、Bot 流量比、IP 属性和来源
        4. 生成格式化的结果字符串
        5. 更新缓存

        参数:
            url: IP 检测网站 URL，默认为 ippure.com
            proxy: 代理服务器 URL
            timeout: 页面加载超时时间（毫秒），默认 20 秒

        返回:
            dict: 包含以下字段的结果字典
                - ip: IP 地址
                - pure_score: IPPure 系数
                - bot_score: Bot 流量比
                - pure_emoji: IPPure 对应的 emoji
                - bot_emoji: Bot 对应的 emoji
                - ip_attr: IP 属性
                - ip_src: IP 来源
                - full_string: 格式化的完整结果字符串
                - error: 错误信息（如有）
        """
        if not self.browser:
            await self.start()

        # 1. 快速 IP 检测与缓存逻辑
        current_ip = await self.get_simple_ip(proxy)
        if current_ip and current_ip in self.cache:
            print(f"[缓存命中] {current_ip}")
            return self.cache[current_ip]

        if current_ip:
            print(f"[新 IP] {current_ip}")
        else:
            print("[警告] 快速 IP 检测失败。使用浏览器扫描...")

        # 2. 浏览器检测
        context_args = {
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        if proxy:
            context_args["proxy"] = {"server": proxy}

        context = await self.browser.new_context(**context_args)

        # 资源拦截（优化）
        await context.route(
            "**/*", lambda route: route.abort() if route.request.resource_type in ["image", "media", "font"] else route.continue_()
        )

        page = await context.new_page()

        # 默认结果结构
        result = {
            "pure_emoji": "❓",
            "bot_emoji": "❓",
            "ip_attr": "❓",
            "ip_src": "❓",
            "pure_score": "❓",
            "bot_score": "❓",
            "full_string": "",
            "ip": current_ip if current_ip else "❓",
            "error": None,
        }

        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=timeout)

            # 优化的等待逻辑
            try:
                await page.wait_for_selector("text = 人机流量比", timeout=10000)
            except:
                pass

            await page.wait_for_timeout(2000)
            text = await page.inner_text("body")

            # 1. 解析 IPPure 系数
            score_match = re.search(r"IPPure 系数.*?(\d+%)", text, re.DOTALL)
            if score_match:
                result["pure_score"] = score_match.group(1)
                result["pure_emoji"] = self.get_emoji(result["pure_score"])

            # 2. 解析 Bot 流量比
            bot_match = re.search(r"bot\s*(\d+(\.\d+)?)%", text, re.IGNORECASE)
            if bot_match:
                val = bot_match.group(0).replace("bot", "").strip()
                if not val.endswith("%"):
                    val += "%"
                result["bot_score"] = val
                result["bot_emoji"] = self.get_emoji(val)

            # 3. 解析 IP 属性
            attr_match = re.search(r"IP 属性 \s*\n\s*(.+)", text)
            if not attr_match:
                attr_match = re.search(r"IP 属性 \s*(.+)", text)
            if attr_match:
                raw = attr_match.group(1).strip()
                result["ip_attr"] = re.sub(r"IP$", "", raw)

            # 4. 解析 IP 来源
            src_match = re.search(r"IP 来源 \s*\n\s*(.+)", text)
            if not src_match:
                src_match = re.search(r"IP 来源 \s*(.+)", text)
            if src_match:
                raw = src_match.group(1).strip()
                result["ip_src"] = re.sub(r"IP$", "", raw)

            # 5. 如果快速检测失败，从页面提取 IP
            if result["ip"] == "❓":
                ip_match = re.search(r"\b (?:\d {1,3}\.){3}\d {1,3}\b", text)
                if ip_match:
                    result["ip"] = ip_match.group(0)

            # 构造用户要求的 '|' 分隔格式字符串
            attr = result["ip_attr"] if result["ip_attr"] != "❓" else ""
            src = result["ip_src"] if result["ip_src"] != "❓" else ""
            info = f"{attr}|{src}".strip()
            if info == "|":
                info = "未知"  # 优雅处理空值情况
            if not info:
                info = "未知"

            result["full_string"] = f"【{result['pure_emoji']}{result['bot_emoji']} {info}】"

            # 更新缓存
            if result["ip"] != "❓" and result["pure_score"] != "❓":
                self.cache[result["ip"]] = result.copy()

        except Exception as e:
            result["error"] = str(e)
            result["full_string"] = "【❌ 错误】"
        finally:
            if not self.headless:
                print("[调试] 等待 5 秒后关闭浏览器窗口...")
                await asyncio.sleep(5)
            await page.close()
            await context.close()

        return result
