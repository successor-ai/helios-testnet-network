import json, os, random
from colorama import Fore, Style
from eth_account import Account
from eth_account.messages import encode_defunct

from eth_utils import to_hex
from src.utils import logger

def _banner():
    banner = r"""
                                     ▏▋▋▋▋▋▋▋▋▋▋▋▋▋▋▋▋▋▋▋▋▋▋▋▋▌▏                                    
                                    ▁▃▋▍▍▍▍▍▍▍▍▍▍▍▍▍▍▍▍▍▍▍▍▍▍▂█▆▋                                   
                                   ▎▄▆▍▏▏▊▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▄███▉▎                                  
                                 ▋▃▅█▆▊▅▆▂████████████████▇▂█████▇▂▎                                
                                ▃▊▏▇█▆▊██▇█████████████████▇███████▇▋                               
                               ▊▁▎ ▆█▆▊██████████████████████████████                               
                               ▊▁▎ ▇█▆▊██████████████████████████████                               
                               ▊▁▏ ▇█▆▊███▇▆█▇█████████▆█▇███████████                               
                               ▊▁  ▇█▆▊███▋  ▃████████▄ ▏▌███████████                               
                               ▊▁  ▇█▆▊███▋  ▂████████▄  ▍▇██████████                               
                               ▊▁  ▇█▆▊███▋  ▊████████▄  ▍▂██████████                               
                               ▊▁  ▇█▆▊███▋  ▏████████▄  ▏▂██████████                               
                               ▊▁▌▊▇█▆▊███▋  ▏████████▄  ▏▂██████████                               
                               ▊▁▃███▆▊███▋  ▉████████▅▏ ▎▆██████████                               
                               ▊▁▄███▆▊███▆▂▇██████████▆▇▅███████████                               
                               ▊▁▄███▆▊█████▇▇▇▇▇▇▇▇▇▇▇▇▇▇███████████                               
                               ▊▁▄███▆▊███▆▃▄▃▃▃▃▃▃▃▄▄▄▄▄▁▇██████████                               
                               ▊▃▅███▆▉████▂▌▅▁▋▅▉▌▆▁▋▇▉▄████████████                               
                             ▌▉▄█████▆▁████▄▃▇▅▃▇▅▃▇▅▃▇▅▇████████████▆▉▍                            
                           ▎▃▄▅██████▆▁████▌▏▃▋▏▂▋ ▄▌▏▄▍▉█████████████▆█▊▏                          
                           ▊█▇▆▃▊▇███▆▂█████▄▇▅▄▇▅▄▇▅▄▇▅▅██████████▄▊▆▆██▎                          
                           ▎▍▏▏ ▏▎▋▃▇███████████████████████████▄▂▍▏  ▏▍▍▏                          
                                    ▉██████████████████████████▇▍                                   
                                   ▎▊▇█████████████████████████▇▊                                   
                                   ▍▅▂▄▅██████▂▏     ▍▅█████████▅                                   
                          ▎▂▂▂▂▂▂▂▁▂▄▅████████▃▂▂▂▂▂▂▂▅██████████▅▂▂▂▂▂▂▂▂                          
                          ▍██▅████▃▆██████████████████████████████████████                          
                          ▏▍▍▍▍▍▍▍▍▍▍▍▍▍▍▍▍▍▍▍▍▍▍▍▍▍▍▍▍▍▍▍▍▍▍▍▍▍▍▍▍▍▍▍▍▍▍▍                                     
"""
    print(Fore.LIGHTGREEN_EX + Style.BRIGHT + banner + Style.RESET_ALL)
    print(f"{Fore.GREEN}==================[ {Style.BRIGHT}Successor-ai{Style.NORMAL} ]=================={Style.RESET_ALL}")
    print(f"{Fore.WHITE}>> Helios Network :: Testnet Automation <<{Style.RESET_ALL}")
    print(f"{Fore.WHITE}>> Status: Online | Target: Testnet <<{Style.RESET_ALL}\n")
    print(Fore.GREEN + "------------------------------------------------------------" + Style.RESET_ALL)

def _parse_range(value: str) -> list | None:
    if value and value.startswith('[') and value.endswith(']'):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return None
    return None

def load_from_file(filename: str) -> list[str]:
    if not os.path.exists(filename):
        return []
    try:
        with open(filename, 'r') as f:
            return [line.strip() for line in f if line.strip()]
    except Exception as e:
        logger.error(f"Failed to read file {filename}: {e}")
        return []

def get_address_from_pk(private_key: str) -> str | None:
    try:
        return Account.from_key(private_key).address
    except Exception:
        return None
    
def get_random_value(value_range: list[float]) -> float:
    if isinstance(value_range[0], int):
        return random.randint(value_range[0], value_range[1])
    else:
        return random.uniform(value_range[0], value_range[1])
        
def generate_wallet_details(private_key: str) -> tuple[str, str] | None:
    try:
        account = Account.from_key(private_key)
        return account, account.address
    except Exception:
        return None

def generate_signature_payload(account: Account, address: str) -> dict:
    message = f"Welcome to Helios! Please sign this message to verify your wallet ownership.\n\nWallet: {address}"
    encoded_message = encode_defunct(text=message)
    signed_message = account.sign_message(encoded_message)
    signature = to_hex(signed_message.signature)
    return {"wallet": address, "signature": signature}

def mask_string(s: str, start=6, end=6) -> str:
    if len(s) < start + end:
        return s
    return f"{s[:start]}...{s[-end:]}"

def format_seconds(seconds: int) -> str:
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"

def pad_hex(value, length=64):
    return hex(value)[2:].zfill(length)

def encode_hex_as_string(string, length=32):
    return string.lower()[2:].rjust(length * 2, '0')

def encode_string_as_bytes(string, length=64):
    hex_str = string.encode('utf-8').hex()
    return hex_str.ljust(length * 2, '0')

def print_help_message():
    help_text = """
    Helios Bot - Command-Line Argument Help
    ================================================
    Usage: python main.py [argument]

    Available Arguments:
      --generate        Creates new wallets and saves them to unregistered.txt.
      --register        Registers all accounts from unregistered.txt.
      --deploy          Runs ONLY the contract DEPLOYMENT task.
      --bridge          Runs ONLY the BRIDGE task.
      --delegate        Runs ONLY the DELEGATE task.
      --faucet          Runs ONLY the FAUCET task.
      --send            Runs ONLY the SEND NATIVE TOKEN task.      
      --help            Displays this help message.

    Without Arguments:
      If no argument is provided, the bot will run in normal loop mode,
      executing all tasks enabled in the .env file.
    """
    print(help_text)