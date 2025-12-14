import asyncio
import os
import urllib.parse

import aiohttp
import yaml

from core.ip_checker import IPChecker
from utils.config_loader import load_config

# --- CONFIGURATION ---
# Load from config.yaml if exists
cfg = load_config("config.yaml") or {}

# User provided path
CLASH_CONFIG_PATH = cfg.get("yaml_path", r"YOUR_CLASH_CONFIG_PATH_HERE")
# API URL (Default for Clash)
CLASH_API_URL = cfg.get("clash_api_url", "http://127.0.0.1:9097")
CLASH_API_SECRET = cfg.get("clash_api_secret", "")
# The selector to switch. Usually "GLOBAL" or "Proxy"
SELECTOR_NAME = cfg.get("selector_name", "GLOBAL")
# Output suffix
OUTPUT_SUFFIX = cfg.get("output_suffix", "_checked")


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
                        # print(await resp.text()) # Reduce noise
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


async def process_proxies():
    print(f"Loading config from: {CLASH_CONFIG_PATH}")
    if not os.path.exists(CLASH_CONFIG_PATH):
        print(f"Error: Config file not found at {CLASH_CONFIG_PATH}")
        return

    try:
        with open(CLASH_CONFIG_PATH, "r", encoding="utf-8") as f:
            config_data = yaml.full_load(f)  # full_load is safer for complex local yamls than safe_load
    except Exception as e:
        print(f"Error parsing YAML: {e}")
        return

    proxies = config_data.get("proxies", [])
    if not proxies:
        print("No 'proxies' found in config.")
        return

    # Filter keywords (partial match)
    # Removed "流量" because it matches "流量倍率" in valid nodes
    SKIP_KEYWORDS = ["剩余", "重置", "到期", "有效期", "官网", "网址", "更新", "公告"]

    print(f"Found {len(proxies)} proxies to test.")

    controller = ClashController(CLASH_API_URL, CLASH_API_SECRET)

    # FORCE GLOBAL MODE
    await controller.set_mode("global")

    # DYNAMICALLY DETECT PORT FROM API
    # Profiles often don't contain the running port (managed by GUI)
    # We fetch the actual listening port from the running instance.
    mixed_port = 7890  # fallback
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{CLASH_API_URL}/configs", headers=controller.headers) as resp:
                if resp.status == 200:
                    conf = await resp.json()
                    # Priority: mixed-port > port (http) > socks-port
                    if conf.get("mixed-port", 0) != 0:
                        mixed_port = conf["mixed-port"]
                    elif conf.get("port", 0) != 0:
                        mixed_port = conf["port"]
                    elif conf.get("socks-port", 0) != 0:
                        mixed_port = conf["socks-port"]
                    print(f"Detected Running Port from API: {mixed_port}")
    except Exception as e:
        print(f"Failed to fetch config from API: {e}")

    local_proxy_url = f"http://127.0.0.1:{mixed_port}"
    print(f"Using Local Proxy: {local_proxy_url}")

    selector_to_use = SELECTOR_NAME

    # DEBUG: Check Selectors and Auto-Detect
    try:
        async with aiohttp.ClientSession() as session:
            url = f"{CLASH_API_URL}/proxies"
            headers = {"Authorization": f"Bearer {CLASH_API_SECRET}"}
            async with session.get(url, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    all_proxies = data.get("proxies", {})
                    print("\n--- Available Selectors ---")
                    found_global = False
                    found_proxy = False

                    for k, v in all_proxies.items():
                        if v.get("type") in ["Selector", "URLTest", "FallBack"]:
                            print(f"  {k}: {v.get('type')} | Currently: {v.get('now')}")
                            if k == "GLOBAL":
                                found_global = True
                            if k == "Proxy":
                                found_proxy = True
                    print("---------------------------\n")

                    if not found_global and found_proxy:
                        print("NOTE: 'GLOBAL' selector not found, switching to 'Proxy'.")
                        selector_to_use = "Proxy"
                    elif not found_global and not found_proxy:
                        # Fallback to first selector?
                        pass
                else:
                    print(f"Failed to list proxies. Status: {resp.status}")
    except Exception as e:
        print(f"Debug API Error: {e}")

    checker = IPChecker(headless=True)
    await checker.start()

    results_map = {}  # name -> result_suffix

    try:
        for i, proxy in enumerate(proxies):
            name = proxy["name"]

            # 0. Check for skip keywords
            should_skip = False
            for kw in SKIP_KEYWORDS:
                if kw in name:
                    should_skip = True
                    break

            if should_skip:
                print(f"\n[{i + 1}/{len(proxies)}] Skipping (Status Node): {name}")
                continue

            print(f"\n[{i + 1}/{len(proxies)}] Testing: {name}")

            # 1. Switch Node
            print(f"  -> Switching {selector_to_use} ...")
            switched = await controller.switch_proxy(selector_to_use, name)
            if not switched:
                print("  -> Switch failed, skipping IP check.")
                continue

            # 2. Wait for switch to take effect / connection reset
            await asyncio.sleep(2)

            # 3. Check IP with Retry
            print("  -> Running IP Check...")
            res = None
            for attempt in range(2):
                try:
                    # Pass the local proxy explicitly to ensure Playwright uses it
                    res = await checker.check(proxy=local_proxy_url)
                    if res.get("error") is None and res.get("pure_score") != "❓":
                        break  # Success
                    if attempt == 0:
                        print("     Retrying IP check...")
                        await asyncio.sleep(2)
                except Exception as e:
                    print(f"     Check error: {e}")

            if not res:
                res = {"full_string": "【❌ Error】", "ip": "Error", "pure_score": "?", "bot_score": "?"}

            full_str = res["full_string"]

            # Extract details for logging
            ip_addr = res.get("ip", "Unknown")
            p_score = res.get("pure_score", "N/A")
            b_score = res.get("bot_score", "N/A")

            print(f"  -> Result: {full_str}")
            print(f"  -> Details: IP: {ip_addr} | Score: {p_score} | Bot: {b_score}")

            results_map[name] = full_str

    except KeyboardInterrupt:
        print("\nProcess interrupted by user. Saving current progress...")
    finally:
        await checker.stop()

    # Apply renames to config data
    print("\nUpdating config names...")
    new_proxies = []

    name_mapping = {}  # Old -> New

    for proxy in proxies:
        old_name = proxy["name"]
        if old_name in results_map:
            new_name = f"{old_name} {results_map[old_name]}"
            proxy["name"] = new_name
            name_mapping[old_name] = new_name
        new_proxies.append(proxy)

    config_data["proxies"] = new_proxies

    # Update groups
    if "proxy-groups" in config_data:
        for group in config_data["proxy-groups"]:
            if "proxies" in group:
                new_group_proxies = []
                for p_name in group["proxies"]:
                    if p_name in name_mapping:
                        new_group_proxies.append(name_mapping[p_name])
                    else:
                        new_group_proxies.append(p_name)
                group["proxies"] = new_group_proxies

    # Save to CURRENT DIRECTORY
    base = os.path.basename(CLASH_CONFIG_PATH)  # Get filename only
    filename, ext = os.path.splitext(base)
    output_filename = f"{filename}{OUTPUT_SUFFIX}{ext}"
    output_path = os.path.join(os.getcwd(), output_filename)

    try:
        with open(output_path, "w", encoding="utf-8") as f:
            yaml.dump(config_data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
        print(f"\nSuccess! Saved updated config to: {output_path}")
    except Exception as e:
        print(f"Error saving config: {e}")


if __name__ == "__main__":
    # asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy()) # REMOVED: Playwright requires Proactor on Windows
    asyncio.run(process_proxies())
