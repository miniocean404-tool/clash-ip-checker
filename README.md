# 🚀 Clash Node IP CHECKER

[中文](README.md) | [English](README_EN.md) | [官网](https://tombcato.github.io/clash-ip-checker/)

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)
[![Twitter](https://img.shields.io/badge/Twitter-%40hibearss-1DA1F2?style=flat&logo=twitter&logoColor=white)](https://x.com/hibearss)
[![zread](https://img.shields.io/badge/Ask_Zread-_.svg?style=flat&color=00b0aa&labelColor=000000&logo=data%3Aimage%2Fsvg%2Bxml%3Bbase64%2CPHN2ZyB3aWR0aD0iMTYiIGhlaWdodD0iMTYiIHZpZXdCb3g9IjAgMCAxNiAxNiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTQuOTYxNTYgMS42MDAxSDIuMjQxNTZDMS44ODgxIDEuNjAwMSAxLjYwMTU2IDEuODg2NjQgMS42MDE1NiAyLjI0MDFWNC45NjAxQzEuNjAxNTYgNS4zMTM1NiAxLjg4ODEgNS42MDAxIDIuMjQxNTYgNS42MDAxSDQuOTYxNTZDNS4zMTUwMiA1LjYwMDEgNS42MDE1NiA1LjMxMzU2IDUuNjAxNTYgNC45NjAxVjIuMjQwMUM1LjYwMTU2IDEuODg2NjQgNS4zMTUwMiAxLjYwMDEgNC45NjE1NiAxLjYwMDFaIiBmaWxsPSIjZmZmIi8%2BCjxwYXRoIGQ9Ik00Ljk2MTU2IDEwLjM5OTlIMi4yNDE1NkMxLjg4ODEgMTAuMzk5OSAxLjYwMTU2IDEwLjY4NjQgMS42MDE1NiAxMS4wMzk5VjEzLjc1OTlDMS42MDE1NiAxNC4xMTM0IDEuODg4MSAxNC4zOTk5IDIuMjQxNTYgMTQuMzk5OUg0Ljk2MTU2QzUuMzE1MDIgMTQuMzk9OSA1LjYwMTU2IDE0LjExMzQgNS42MDE1NiAxMy43NTk5VjExLjAzOTlDNS42MDE1NiAxMC42ODY0IDUuMzE1MDIgMTAuMzk5OSA0Ljk2MTU2IDEwLjM5OTlaIiBmaWxsPSIjZmZmIi8%2BCjxwYXRoIGQ9Ik0xMy43NTg0IDEuNjAwMUgxMS4wMzg0QzEwLjY4NSAxLjYwMDEgMTAuMzk4NCAxLjg4NjY0IDEwLjM5ODQgMi4yNDAxVjQuOTYwMUMxMC4zOTg0IDUuMzEzNTYgMTAuNjg1IDUuNjAwMSAxMS4wMzg0IDUuNjAwMUgxMy43NTg0QzE0LjExMTkgNS42MDAxIDE0LjM5ODQgNS4zMTM1NiAxNC4zOTk4IDQuOTYwMVYyLjI0MDFDMTQuMzk4NCAxLjg4NjY0IDE0LjExMTkgMS42MDAxIDEzLjc1ODQgMS42MDAxWiIgZmlsbD0iI2ZmZiIvPgo8cGF0aCBkPSJNNCAxMkwxMiA0TDQgMTJaIiBmaWxsPSIjZmZmIi8%2BCjxwYXRoIGQ9Ik00IDEyTDEyIDQiIHN0cm9rZT0iI2ZmZiIgc3Ryb2tlLXdpZHRoPSIxLjUiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIvPgo8L3N2Zz4K&logoColor=ffffff)](https://zread.ai/tombcato/clash-ip-checker)



一个针对 **Clash Verge** (及兼容核心) 的智能自动化工具。它会自动遍历你的代理节点，通过 [IPPure](https://ippure.com/) 检测 IP 纯净度和风险值，并重命名节点，添加实用的指标（IP 纯净度、Bot 比例、IP属性/IP来源状态）`【🟢🟡 住宅|原生】`。

![图片描述](assets/clash-node-checked.png)

##  ⚡新增Docker部署 [详情见Docker分支](https://github.com/tombcato/clash-ip-checker/tree/docker)
相对于主分支而言，Docker部署后代理切换不影响本地网络（非本地部署方式），且能直接输入订阅链接输出新订阅链接，没有繁琐的使用步骤，**正真做到一键替换检测！！！**


## ✨ 功能特点

- **⚡ 极速模式 (新!)**: 暂时默认 **关闭**，通过 IPPure API 直接检测，速度比浏览器模式快 10 倍以上！但缺少 Bot 比例分析，输出`【🟢 住宅|原生】`，可在config.yaml中设置`fast_mode = True`开启。
- **自动切换**: 自动遍历并切换你的 Clash 代理节点。
- **深度 IP 分析**: 检测 IP 纯净度分数、Bot 比例、IP 属性 (原生/机房) 以及归属地。
- **高拟真检测 (可选)**: 在浏览器模式下使用 **Playwright** 进行高拟真检测，包含 Bot 比例分析。
- **智能过滤**: 自动跳过无效节点 (如 "到期", "流量重置", "官网" 等)。
- **配置注入**: 生成一个新的 Clash 配置文件 (`_checked.yaml`)，在节点名称后追加 Emoji 和状态信息。
- **强制全局模式**: 临时将 Clash 强制切换为全局模式以确保测试准确性。

## 🛠️ 前置要求

- **Python 3.10+**
- **Clash Verge** (或其他开启了 External Controller 的 Clash 客户端)
- **Playwright** (用于浏览器模式)
- **curl_cffi** (用于极速模式)

## 📦 安装说明

1.  **克隆仓库**
    ```bash
    git clone git@github.com:tombcato/clash-ip-checker.git
    cd clash-ip-checker
    ```

2.  **安装依赖**
    ```bash
    pip install -r requirements.txt
    playwright install chromium
    #如果install chromium运行失败说明playwright没添加环境变量 可以用 python -m playwright install chromium
    ```

3.  **配置文件**
    - 修改 `config.yaml.example` **删除文件名.example 重命名为 `config.yaml`** 重要！！！。
    - 编辑 `config.yaml` 填入你的信息（具体见下面使用方法）：
        - `fast_mode`: ⚡ 是否使用极速模式 (True/False)。
        - `yaml_path`: 你的 Clash 配置文件 (**.yaml**) 的绝对路径。
        - `clash_api_secret`: 你的 API 密钥 (如果有的话)。


## 🚀 使用方法

1.  打开你的 Clash 客户端 (例如 Clash Verge) 将当前clash正在运行的订阅配置文件切换为你想要测试的订阅， 然后获取该配置文件的yaml文件绝对路径, 在config.yaml中配置yaml_path.
    右键配置文件选择打开文件
    ![](assets/clash-open-yaml.png)
    通过vscode获取path
    ![](assets/clash-open-yaml-vscode.png)
    或者通过记事本获取path, 鼠标悬停展示但无法复制，需要在对应的文件夹中找到再复制
    ![](assets/clash-open-yaml-jsb.png)

1.  确保 **External Controller** (外部控制) 已在设置中开启，并在config.yaml中配置clash_api_url与clash_api_secret与之对应。密码随便设置
    ![alt text](assets/clash-controller.png)
2.  运行脚本:
    ```bash
    python clash_automator.py
    ```
    *默认使用浏览器模式 (包含 Bot 检测)。如需开启 **极速模式** (速度快 10 倍，无 Bot 检测)，请在 `config.yaml` 中设置 `fast_mode = True`。*

3.  脚本将会:
    - 连接到 Clash API。
    - 切换到 "Global" (全局) 模式。
    - 逐个测试代理节点, 访问IPPure获取ip信息。
    - 生成一个名为 `your_config_checked.yaml` 的新文件。
4.  在项目当前文件夹下将生成的 `_checked.yaml` 文件导入 Clash 即可切换该配置查看结果！
    导入_checked.yaml配置
    ![](assets/clash-import.png)

## 📝 输出示例

你的代理节点将会被重命名，直观展示其质量：

### 🔍 结果解读

格式： `【🟢🟡 机房|广播】` (默认浏览器模式) 或 `【⚪ 机房|广播】` (极速模式)

*   **第 1 个 Emoji (⚪)**: **IP 纯净度** (值越低越好，越低越像真实用户)
*   **第 2 个 Emoji (🟡)**: **Bot 比例** (浏览器模式独有，值越高来自机器人的流量更大更容易弹验证)
*   **属性**: 住宅 / 机房 
*   **来源**: 原生 / 广播

#### 📊 评分对照表

| 范围 | Emoji | 含义 |
| :--- | :---: | :--- |
| **0 - 10%** | ⚪ | **极佳** |
| **11 - 30%** | 🟢 | **优秀** |
| **31 - 50%** | 🟡 | **良好** |
| **51 - 70%** | 🟠 | **中等** |
| **71 - 90%** | 🔴 | **差** |
| **> 90%** | ⚫ | **极差** |

#### 🏷️ 常见标签说明

*   **住宅 (Residential)**: 家庭宽带 IP，隐蔽性高，被封锁概率低。
*   **机房 (Datacenter)**: 数据中心 IP，速度快但容易被识别。
*   **原生 (Native)**: 指该 IP 归属于当地运营商，通常解锁流媒体 (Netflix, Disney+) 效果最好。
*   **广播 (Broadcast)**: IP 地理位置与注册地不符。

## ⚙️ 配置项

查看 `config.yaml.example` 获取所有可用配置项的说明。

## 🤝 贡献参与

欢迎提交 Pull Request 来改进这个项目！

## ⚠️ 免责声明

本工具仅供教育和测试使用。请遵守当地法律法规，并合理使用代理服务。

## 🌟 Star 记录

[![Star History Chart](https://api.star-history.com/svg?repos=tombcato/clash-ip-checker&type=Date)](https://star-history.com/#tombcato/clash-ip-checker&Date)




