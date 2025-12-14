import urllib.parse

import aiohttp


class ClashController:
    """
    Clash API 控制器类，用于管理 Clash 代理客户端的各种操作。文档: https://clash.gitbook.io/doc/restful-api

    主要功能包括：切换代理节点、设置运行模式、获取端口信息和代理列表。
    """

    def __init__(self, api_url, secret=""):
        """
        初始化 Clash 控制器。

        参数:
            api_url: Clash API 地址，如 "http://127.0.0.1:9097"
            secret: API 密钥，用于身份验证
        """
        self.api_url = api_url.rstrip("/")
        self.headers = {"Authorization": f"Bearer {secret}", "Content-Type": "application/json"}

    async def switch_proxy(self, selector, proxy_name):
        """
        将指定的选择器切换到特定的代理节点。

        参数:
            selector: 选择器名称，如 "GLOBAL" 或 "Proxy"
            proxy_name: 代理节点名称

        返回:
            bool: 切换成功返回 True，失败返回 False
        """
        url = f"{self.api_url}/proxies/{urllib.parse.quote(selector)}"
        payload = {"name": proxy_name}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.put(url, json=payload, headers=self.headers, timeout=5) as resp:
                    if resp.status == 204:
                        return True
                    else:
                        print(f"切换到 {proxy_name} 失败。状态码: {resp.status}")
                        return False
        except Exception as e:
            print(f"切换到 {proxy_name} 时发生 API 错误: {e}")
            return False

    async def set_mode(self, mode):
        """
        设置 Clash 运行模式。

        参数:
            mode: 运行模式，可选值: "global"(全局)、"rule"(规则)、"direct"(直连)

        返回:
            bool: 设置成功返回 True，失败返回 False
        """
        url = f"{self.api_url}/configs"
        payload = {"mode": mode}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.patch(url, json=payload, headers=self.headers, timeout=5) as resp:
                    if resp.status == 204:
                        print(f"成功设置模式为: {mode}")
                        return True
                    else:
                        print(f"设置模式失败。状态码: {resp.status}")
                        return False
        except Exception as e:
            print(f"设置模式时发生 API 错误: {e}")
            return False

    async def get_running_port(self):
        """
        从运行中的 Clash 实例获取监听端口。

        优先级: mixed-port > port (HTTP) > socks-port

        返回:
            int: 端口号，如果获取失败则返回默认值 7890
        """
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
        return 7890  # 默认回退端口

    async def get_proxies(self):
        """
        获取所有可用的代理节点列表。

        返回:
            dict: 成功时返回代理字典，失败返回 None
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.api_url}/proxies", headers=self.headers) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data.get("proxies", {})
        except Exception as e:
            print(f"获取代理列表时发生错误: {e}")
            return None
