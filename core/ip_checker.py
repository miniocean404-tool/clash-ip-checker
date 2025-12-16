import asyncio
import re
import aiohttp
from curl_cffi.requests import AsyncSession
from playwright.async_api import async_playwright

class IPChecker:
    def __init__(self, headless=True):
        self.headless = headless
        self.browser = None
        self.playwright = None
        self.cache = {} # Map IP -> Result Dict

    async def start(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=["--no-sandbox", "--disable-setuid-sandbox"]
        )

    async def stop(self):
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    def get_emoji(self, percentage_str):
        try:
            val = float(percentage_str.replace('%', ''))
            # Logic from ipcheck.py with user approved thresholds
            if val <= 10: return "⚪"
            if val <= 30: return "🟢"
            if val <= 50: return "🟡"
            if val <= 70: return "🟠"
            if val <= 90: return "🔴"
            return "⚫"
        except:
            return "❓"

    async def get_simple_ip(self, proxy=None):
        """Fast IPv4 check for caching."""
        urls = ["http://api.ipify.org", "http://v4.ident.me"]
        for url in urls:
            try:
                # User modified timeout to 3s
                timeout = aiohttp.ClientTimeout(total=3)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.get(url, proxy=proxy) as resp:
                        if resp.status == 200:
                            ip = (await resp.text()).strip()
                            if re.match(r"^\d{1,3}(\.\d{1,3}){3}\d{1,3}$", ip):
                                return ip
            except Exception:
                continue 
        return None

    async def check(self, url="https://ippure.com/", proxy=None, timeout=20000):
        if not self.browser:
            await self.start()
        
        # 1. Cleaner Fast IP & Cache Logic
        current_ip = await self.get_simple_ip(proxy)
        if current_ip and current_ip in self.cache:
            print(f"     [Cache Hit] {current_ip}")
            return self.cache[current_ip]
        
        if current_ip:
            print(f"     [New IP] {current_ip}")
        else:
            print("     [Warning] Fast IP check failed. Scanning with browser...")

        # 2. Browser Check (Logic from ipcheck.py)
        context_args = {
             "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        if proxy:
            context_args["proxy"] = {"server": proxy}
            
        context = await self.browser.new_context(**context_args)
        
        # Resource blocking (Optimization)
        await context.route("**/*", lambda route: route.abort() 
            if route.request.resource_type in ["image", "media", "font"] 
            else route.continue_())

        page = await context.new_page()
        
        # Default Result Structure
        result = {
            "pure_emoji": "❓", "bot_emoji": "❓", "ip_attr": "❓", "ip_src": "❓",
            "pure_score": "❓", "bot_score": "❓", "full_string": "", "ip": current_ip if current_ip else "❓", "error": None
        }

        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=timeout)
            
            # Logic from ipcheck.py - Optimized wait
            try:
                await page.wait_for_selector("text=人机流量比", timeout=10000)
            except:
                pass 

            await page.wait_for_timeout(2000)
            text = await page.inner_text("body")

            # 1. IPPure Score
            score_match = re.search(r"IPPure系数.*?(\d+%)", text, re.DOTALL)
            if score_match:
                result["pure_score"] = score_match.group(1)
                result["pure_emoji"] = self.get_emoji(result["pure_score"])

            # 2. Bot Ratio
            bot_match = re.search(r"bot\s*(\d+(\.\d+)?)%", text, re.IGNORECASE)
            if bot_match:
                val = bot_match.group(0).replace('bot', '').strip()
                if not val.endswith('%'): val += "%"
                result["bot_score"] = val
                result["bot_emoji"] = self.get_emoji(val)

            # 3. Attributes
            attr_match = re.search(r"IP属性\s*\n\s*(.+)", text)
            if not attr_match: attr_match = re.search(r"IP属性\s*(.+)", text)
            if attr_match:
                raw = attr_match.group(1).strip()
                result["ip_attr"] = re.sub(r"IP$", "", raw)

            # 4. Source
            src_match = re.search(r"IP来源\s*\n\s*(.+)", text)
            if not src_match: src_match = re.search(r"IP来源\s*(.+)", text)
            if src_match:
                raw = src_match.group(1).strip()
                result["ip_src"] = re.sub(r"IP$", "", raw)

            # 5. Fallback IP if fast check failed
            if result["ip"] == "❓":
                ip_match = re.search(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", text)
                if ip_match: result["ip"] = ip_match.group(0)

            # Construct String with user requested '|' separator
            attr = result["ip_attr"] if result["ip_attr"] != "❓" else ""
            src = result["ip_src"] if result["ip_src"] != "❓" else ""
            info = f"{attr}|{src}".strip()
            if info == "|": info = "未知" # Handle empty case gracefully
            if not info: info = "未知"
            
            result["full_string"] = f"【{result['pure_emoji']}{result['bot_emoji']} {info}】"

            # Cache Update
            if result["ip"] != "❓" and result["pure_score"] != "❓":
                self.cache[result["ip"]] = result.copy()

        except Exception as e:
            result["error"] = str(e)
            result["full_string"] = "【❌ Error】"
        finally:
            if not self.headless:
                print("     [Debug] Waiting 5s before closing browser window...")
                await asyncio.sleep(5)
            await page.close()
            await context.close()
            
        return result

    async def check_fast(self, proxy=None):
        """
        Fast mode using https://my.123169.xyz/v1/info API.
        Skips browser challenge/rendering.
        """
        url = "https://my.123169.xyz/v1/info"
        result = {
            "pure_emoji": "❓", "bot_emoji": "❓", "ip_attr": "❓", "ip_src": "❓",
            "pure_score": "❓", "bot_score": "N/A", "full_string": "", "ip": "❓", "error": None
        }

        try:
            # Short timeout for fast mode (5s)
            # Use curl_cffi AsyncSession
            proxies = None
            if proxy:
                # curl_cffi expects proxies dict: {"http": "...", "https": "..."}
                # Check if proxy string has scheme, usually "http://127.0.0.1:..."
                proxies = {"http": proxy, "https": proxy}

            async with AsyncSession(proxies=proxies, impersonate="chrome110", timeout=5) as session:
                resp = await session.get(url)
                if resp.status_code == 200:
                    data = resp.json()
                    
                    # 1. IP
                    result["ip"] = data.get("ip", "❓")
                    
                    # 2. Pure Score (fraudScore)
                    f_score = data.get("fraudScore")
                    if f_score is not None:
                        # fraudScore is likely 0-100 int. Convert to str% for emoji compatibility
                        result["pure_score"] = f"{f_score}%"
                        result["pure_emoji"] = self.get_emoji(result["pure_score"])
                    
                    # 3. Attributes (Residential vs DataCenter)
                    is_resi = data.get("isResidential", False)
                    # Default to False (机房) if key missing, but API returns boolean
                    result["ip_attr"] = "住宅" if is_resi else "机房"

                    # 4. Source (Broadcast vs Native)
                    is_broad = data.get("isBroadcast", False)
                    result["ip_src"] = "广播" if is_broad else "原生"

                    # 5. Full String
                    # Bot emoji is skipped or N/A. The user said: "Although no bot ratio... finally display without bot ratio"
                    # Original: 【⚪🟢 IPAttr|IPSource】
                    # Fast Mode: 【⚪ IPAttr|IPSource】 (Removed bot emoji slot)
                    
                    attr = result["ip_attr"] if result["ip_attr"] != "❓" else ""
                    src = result["ip_src"] if result["ip_src"] != "❓" else ""
                    info = f"{attr}|{src}".strip()
                    if info == "|": info = "未知"
                    if not info: info = "未知"

                    result["full_string"] = f"【{result['pure_emoji']} {info}】"
                    
                    # Cache Update (Optional, maybe not needed for fast mode as it is already fast)
                    if result["ip"] != "❓":
                        self.cache[result["ip"]] = result.copy()
                        
                else:
                    result["error"] = f"API Error {resp.status_code}"
                    result["full_string"] = "【❌ API Error】"

        except Exception as e:
            print(f"     [Debug] curl_cffi error: {e}")
            result["error"] = str(e)
            result["full_string"] = "【❌ Error】"

        return result

