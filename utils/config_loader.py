import os

import yaml


def load_config(config_path="config.yaml"):
    """
    从YAML文件加载配置信息。
    """
    if not os.path.exists(config_path):
        return None

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"配置文件加载错误: {e}")
        return None


def validate_config(config):
    """
    验证配置文件中的必要字段 clash_api_url、yaml_path。
    """
    required = ["clash_api_url", "yaml_path"]
    missing = [k for k in required if k not in config or not config[k]]

    if missing:
        print(f"缺少必需的配置字段: {', '.join(missing)}")
        return False

    if not os.path.exists(config["yaml_path"]):
        print(f"配置错误: 目标YAML文件未找到于 {config['yaml_path']}")
        return False

    return True
