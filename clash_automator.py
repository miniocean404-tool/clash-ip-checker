import asyncio
import os

import yaml

from core.clash_api import ClashController
from core.ip_checker import IPChecker
from utils.config_loader import load_config

# --- 配置区 ---
# 从 config.yaml 加载配置（如果存在）
cfg = load_config("config.yaml") or {}

# 用户提供的 Clash 配置文件路径
CLASH_CONFIG_PATH = cfg.get("yaml_path", r"YOUR_CLASH_CONFIG_PATH_HERE")
# Clash 外部控制器地址（Clash 默认值）
CLASH_API_URL = cfg.get("clash_api_url", "http://127.0.0.1:9097")
CLASH_API_SECRET = cfg.get("clash_api_secret", "")

# 要切换的选择器名称，通常是 "GLOBAL" 或 "Proxy"
SELECTOR_NAME = cfg.get("selector_name", "GLOBAL")
OUTPUT_SUFFIX = cfg.get("output_suffix", "检测")


async def process_proxies():
    """
    处理 Clash 配置文件中的所有代理节点。

    主要流程：
    1. 加载 Clash 配置文件
    2. 过滤掉状态通知类节点
    3. 强制设置为全局模式
    4. 动态检测 Clash 监听端口
    5. 逐个测试每个代理节点
    6. 获取 IP 质量信息并添加到节点名称
    7. 更新配置文件中的节点名称和代理组
    8. 保存到当前目录下的新文件

    支持中途中断（Ctrl+C），会保存已完成的进度。
    """
    print(f"正在加载配置文件: {CLASH_CONFIG_PATH}")
    if not os.path.exists(CLASH_CONFIG_PATH):
        print(f"错误：配置文件未找到于 {CLASH_CONFIG_PATH}")
        return

    try:
        with open(CLASH_CONFIG_PATH, "r", encoding="utf-8") as f:
            config_data = yaml.full_load(f)  # full_load 对复杂本地 yaml 比 safe_load 更安全
    except Exception as e:
        print(f"错误: YAML 解析失败: {e}")
        return

    proxies = config_data.get("proxies", [])
    if not proxies:
        print("配置文件中未找到 'proxies' 字段。")
        return

    # 过滤关键词（部分匹配）
    # 移除了 "流量"，因为它会匹配有效节点中的 "流量倍率"
    SKIP_KEYWORDS = ["剩余", "重置", "到期", "有效期", "官网", "网址", "更新", "公告"]

    print(f"找到 {len(proxies)} 个代理节点待测试。")

    controller = ClashController(CLASH_API_URL, CLASH_API_SECRET)

    # 强制设置全局模式
    await controller.set_mode("global")

    # 从 API 动态检测端口
    # 配置文件通常不包含运行端口（由 GUI 管理）
    # 我们从运行实例获取实际监听端口
    mixed_port = await controller.get_running_port()
    print(f"从 API 检测到运行端口: {mixed_port}")

    local_proxy_url = f"http://127.0.0.1:{mixed_port}"
    print(f"使用本地代理: {local_proxy_url}")

    selector_to_use = SELECTOR_NAME

    # 调试：检查选择器并自动检测
    all_proxies = await controller.get_proxies()
    if all_proxies:
        print("\n--- 可用的选择器 ---")
        found_global = False
        found_proxy = False

        for k, v in all_proxies.items():
            if v.get("type") in ["Selector", "URLTest", "FallBack"]:
                print(f"{k}: {v.get('type')} | 当前: {v.get('now')}")
                if k == "GLOBAL":
                    found_global = True
                if k == "Proxy":
                    found_proxy = True
        print("---------------------------\n")

        if not found_global and found_proxy:
            print("注意：未找到 'GLOBAL' 选择器，切换到 'Proxy'。")
            selector_to_use = "Proxy"
        elif not found_global and not found_proxy:
            # 回退到第一个选择器？
            pass
    else:
        print("获取代理列表失败或为空。")

    checker = IPChecker(headless=True)
    await checker.start()

    results_map = {}  # 节点名 -> 结果后缀

    try:
        for i, proxy in enumerate(proxies):
            name = proxy["name"]

            # 0. 检查跳过关键词
            should_skip = False
            for kw in SKIP_KEYWORDS:
                if kw in name:
                    should_skip = True
                    break

            if should_skip:
                print(f"\n [{i + 1}/{len(proxies)}] 跳过（状态节点）: {name}")
                continue

            print(f"\n [{i + 1}/{len(proxies)}] 正在测试: {name}")

            # 1. 切换节点
            print(f"-> 正在切换 {selector_to_use} ...")
            switched = await controller.switch_proxy(selector_to_use, name)
            if not switched:
                print("-> 切换失败，跳过 IP 检测。")
                continue

            # 2. 等待切换生效 / 连接重置
            await asyncio.sleep(2)

            # 3. 带重试的 IP 检测
            print("-> 正在执行 IP 检测...")
            res = None
            for attempt in range(2):
                try:
                    # 显式传递本地代理以确保 Playwright 使用它
                    res = await checker.check(proxy=local_proxy_url)
                    if res.get("error") is None and res.get("pure_score") != "❓":
                        break  # 成功
                    if attempt == 0:
                        print("正在重试 IP 检测...")
                        await asyncio.sleep(2)
                except Exception as e:
                    print(f"检测错误: {e}")

            if not res:
                res = {"full_string": "【❌ 错误】", "ip": "错误", "pure_score": "?", "bot_score": "?"}

            full_str = res["full_string"]

            # 提取详情用于日志
            ip_addr = res.get("ip", "未知")
            p_score = res.get("pure_score", "N/A")
            b_score = res.get("bot_score", "N/A")

            print(f"-> 结果: {full_str}")
            print(f"-> 详情: IP: {ip_addr} | 分数: {p_score} | Bot: {b_score}")

            results_map[name] = full_str

    except KeyboardInterrupt:
        print("\n 进程被用户中断。正在保存当前进度...")
    finally:
        await checker.stop()

    # 应用重命名到配置数据
    print("\n 正在更新配置名称...")
    new_proxies = []

    name_mapping = {}  # 旧名 -> 新名

    for proxy in proxies:
        old_name = proxy["name"]
        if old_name in results_map:
            new_name = f"{old_name} {results_map[old_name]}"
            proxy["name"] = new_name
            name_mapping[old_name] = new_name
        new_proxies.append(proxy)

    config_data["proxies"] = new_proxies

    # 更新代理组
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

    # 保存到当前目录
    base = os.path.basename(CLASH_CONFIG_PATH)  # 仅获取文件名
    filename, ext = os.path.splitext(base)
    output_filename = f"{filename}{OUTPUT_SUFFIX}{ext}"
    output_path = os.path.join(os.getcwd(), output_filename)

    try:
        with open(output_path, "w", encoding="utf-8") as f:
            yaml.dump(config_data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
        print(f"\n 成功！已保存更新后的配置到: {output_path}")
    except Exception as e:
        print(f"保存配置时发生错误: {e}")


if __name__ == "__main__":
    # asyncio.set_event_loop_policy (asyncio.WindowsSelectorEventLoopPolicy ()) # 已移除: Playwright 在 Windows 上需要 Proactor
    asyncio.run(process_proxies())
