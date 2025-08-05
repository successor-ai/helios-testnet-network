import os, json
from pathlib import Path
from dotenv import load_dotenv
from src.utils.utils import _parse_range

load_dotenv()

REGISTERED_ACCOUNTS_FILE = "private_key.txt"
UNREGISTERED_ACCOUNTS_FILE = "unregistered.txt"
PROXY_FILE = "proxies.txt"
WALLET_ADDRESS_LIST = "wallets.txt"

ABI_DIR = Path(__file__).resolve().parent.parent / "abi"
ERC20_ABI = json.load(open(ABI_DIR / "erc20_abi.json", "r", encoding="utf-8"))
ROOT_DIR = Path(__file__).resolve().parent.parent
CONTRACTS_DIR = ROOT_DIR / "abi"
CONTRACT_ABI = None
CONTRACT_BYTECODE = None

settings = {
    "USE_PROXY": os.getenv("USE_PROXY", "false").lower() == "true",
    "CAPTCHA_API_KEY": os.getenv("CAPTCHA_API_KEY", None),
    "SITE_KEY": os.getenv("SITE_KEY", "0x4AAAAAABhz7Yc1no53_eWA"),

    "CAPTCHA_SERVICE": os.getenv("CAPTCHA_SERVICE", None),
    "API_KEY_CAPMONSTER": os.getenv("API_KEY_CAPMONSTER", None),
    "API_KEY_2CAPTCHA": os.getenv("API_KEY_2CAPTCHA", None),
    "API_KEY_ANTI_CAPTCHA": os.getenv("API_KEY_ANTI_CAPTCHA", None),
    "CAPTCHA_SITE_KEY": os.getenv("CAPTCHA_SITE_KEY", None),
    "CAPTCHA_PAGE_URL": os.getenv("CAPTCHA_PAGE_URL", None),

    "DEPLOY_CONSTRUCTOR_ARGS": json.loads(os.getenv("DEPLOY_CONSTRUCTOR_ARGS", '[]')),
    "CAPTCHA_API_KEY": os.getenv("CAPTCHA_API_KEY"),
    "MAX_CONCURRENT_TASKS": int(os.getenv("MAX_CONCURRENT_TASKS", 5)),
    "INVITE_CODE": os.getenv("INVITE_CODE", None),

    "RUN_FAUCET": os.getenv("RUN_FAUCET", "false").lower() == "true",
    "RUN_BRIDGE": os.getenv("RUN_BRIDGE", "false").lower() == "true",
    "RUN_DELEGATE": os.getenv("RUN_DELEGATE", "false").lower() == "true",
    "RUN_DEPLOYMENT": os.getenv("RUN_DEPLOYMENT", "false").lower() == "true",    

    "BRIDGE_COUNT": _parse_range(os.getenv("BRIDGE_COUNT", "[1, 2]")),
    "BRIDGE_AMOUNT": _parse_range(os.getenv("BRIDGE_AMOUNT", "[0.001, 0.005]")),

    "DELEGATE_COUNT": _parse_range(os.getenv("DELEGATE_COUNT", "[2, 3]")),
    "DELEGATE_AMOUNT": _parse_range(os.getenv("DELEGATE_AMOUNT", "[0.001, 0.002]")),

    "DEPLOYMENT_COUNT": _parse_range(os.getenv("DEPLOYMENT_COUNT", "[1, 2]")),

    "BASE_URL": os.getenv("BASE_URL", "https://testnet-api.helioschain.network/api"),
    "PAGE_URL": os.getenv("PAGE_URL", "https://testnet.helioschain.network"),
    "RPC_URL": os.getenv("RPC_URL", "http://152.42.200.232:8000"),
    "EXPLORER_URL": os.getenv("EXPLORER_URL", "https://explorer.helioschainlabs.org/tx/0x"),

    "TIME_SLEEP_BETWEEN_CYCLES": int(os.getenv("TIME_SLEEP_BETWEEN_CYCLES", 240)),
    "DELAY_BETWEEN_ACCOUNTS": _parse_range(os.getenv("DELAY_BETWEEN_ACCOUNTS", "[60, 120]")),
    "DELAY_BETWEEN_TASKS": _parse_range(os.getenv("DELAY_BETWEEN_TASKS", "[10, 20]")),
    
    "RUN_SEND_NATIVE": os.getenv("RUN_SEND_NATIVE", "false").lower() == "true",
    "SEND_COUNT": _parse_range(os.getenv("SEND_COUNT", "[2, 3]")),
    "SEND_AMOUNT": _parse_range(os.getenv("SEND_AMOUNT", "[0.01, 0.05]")),

}

try:
    with open(CONTRACTS_DIR / "deploy_abi.json", 'r') as f:
        _contract_artifact = json.load(f)
    CONTRACT_ABI = _contract_artifact['abi']
    CONTRACT_BYTECODE = _contract_artifact['bytecode']

except (FileNotFoundError, KeyError) as e:
    print(f"The file “abi/deploy_abi.json” was not found or its format is incorrect. Error: {e}")
