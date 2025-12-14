import urllib.parse

import aiohttp


class ClashController:
    def __init__(self, api_url, secret=""):
        self.api_url = api_url.rstrip("/")
        self.headers = {"Authorization": f"Bearer {secret}", "Content-Type": "application/json"}

    async def switch_proxy(self, selector, proxy_name):
        """Switches the selector to the specified proxy."""
        url = f"{self.api_url}/proxies/{urllib.parse.quote(selector)}"
        payload = {"name": proxy_name}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.put(url, json=payload, headers=self.headers, timeout=5) as resp:
                    if resp.status == 204:
                        return True
                    else:
                        print(f"Failed to switch to {proxy_name}. Status: {resp.status}")
                        return False
        except Exception as e:
            print(f"API Error switching to {proxy_name}: {e}")
            return False

    async def set_mode(self, mode):
        """Sets the Clash mode (global, rule, direct)."""
        url = f"{self.api_url}/configs"
        payload = {"mode": mode}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.patch(url, json=payload, headers=self.headers, timeout=5) as resp:
                    if resp.status == 204:
                        print(f"Successfully set mode to: {mode}")
                        return True
                    else:
                        print(f"Failed to set mode logic. Status: {resp.status}")
                        return False
        except Exception as e:
            print(f"API Error setting mode: {e}")
            return False

    async def get_running_port(self):
        """Fetches the mixed-port or http-port from running instance."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.api_url}/configs", headers=self.headers) as resp:
                    if resp.status == 200:
                        conf = await resp.json()
                        if conf.get("mixed-port", 0) != 0:
                            return conf["mixed-port"]
                        if conf.get("port", 0) != 0:
                            return conf["port"]
                        if conf.get("socks-port", 0) != 0:
                            return conf["socks-port"]
        except Exception:
            pass
        return 7890  # Default fallback

    async def get_proxies(self):
        """Fetches all proxies."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.api_url}/proxies", headers=self.headers) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data.get("proxies", {})
        except Exception as e:
            print(f"Error fetching proxies: {e}")
            return None
