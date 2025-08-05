import asyncio
import os
import sys
from eth_account import Account
from aiohttp import ClientSession

from src.utils.logger import log
from config import config
from config.config import settings as _sett
import src.utils.utils as utils
from src.modules.helios_bot import HeliosBot
from src.services.helios_api_client import HeliosApiClient
from src.services.web3_client import Web3Client

if sys.platform == "win32":
    try:
        import winloop
        winloop.install()
    except ImportError:
        pass
else:
    try:
        import uvloop
        uvloop.install()
    except ImportError:
        pass

async def process_account_tasks(session: ClientSession, semaphore: asyncio.Semaphore, pk: str, proxy: str, index: int, validator_list: list, rpc_url: str):
    async with semaphore:
        bot = None
        web3_client = None
        try:
            address = utils.get_address_from_pk(pk)
            log.info(f"Starting processing account {utils.mask_string(address)}", index=index)
            if proxy:
                log.info(f"Using proxy: {proxy.split('@')[-1] if '@' in proxy else proxy}", index=index)
            
            bot = HeliosBot(private_key=pk, proxy=proxy, index=index)
            web3_client = Web3Client(private_key=pk, rpc_url=rpc_url, proxy=proxy, index=index)
            api_client = HeliosApiClient(session, pk, address, index=index)
            await api_client._sync()

            if _sett['RUN_FAUCET']:
                await bot.run_faucet(session)
                await asyncio.sleep(utils.get_random_value(_sett['DELAY_BETWEEN_TASKS']))

            if _sett['RUN_BRIDGE']:
                count = utils.get_random_value(_sett['BRIDGE_COUNT'])
                log.info(f"Will perform bridge {count} times.", index=index)
                for _ in range(count):
                    amount = utils.get_random_value(_sett['BRIDGE_AMOUNT'])
                    await bot.run_bridge(web3_client, amount)
                    await asyncio.sleep(utils.get_random_value(_sett['DELAY_BETWEEN_TASKS']))

            if _sett['RUN_DELEGATE']:
                count = utils.get_random_value(_sett['DELEGATE_COUNT'])
                log.info(f"Will perform delegation {count} times.", index=index)
                for _ in range(count):
                    amount = utils.get_random_value(_sett['DELEGATE_AMOUNT'])
                    await bot.run_delegate(web3_client, amount, validator_list)
                    await asyncio.sleep(utils.get_random_value(_sett['DELAY_BETWEEN_TASKS']))

            if _sett['RUN_DEPLOYMENT']:
                count = utils.get_random_value(_sett['DEPLOYMENT_COUNT'])
                log.info(f"Will perform {count} deployments.", index=index)
                for _ in range(count):
                    await bot.run_deployment(web3_client)
                    await asyncio.sleep(utils.get_random_value(_sett['DELAY_BETWEEN_TASKS']))

            if _sett['RUN_SEND_NATIVE']:
                count = utils.get_random_value(_sett['SEND_COUNT'])
                log.info(f"Will perform {count} send native token.", index=index)
                for _ in range(count):
                    amount = utils.get_random_value(_sett['SEND_AMOUNT'])
                    await bot.run_send_native(web3_client, amount)
                    await asyncio.sleep(utils.get_random_value(_sett['DELAY_BETWEEN_TASKS']))

            log.success(f"The account {utils.mask_string(address)} has been processed.", index=index)
        except Exception as e:
            log.error(f"Unexpected error on worker account {index}: {e}", index=index)

async def process_deployment(session: ClientSession, semaphore: asyncio.Semaphore, pk: str, proxy: str, index: int, rpc_url: str):
    async with semaphore:
        address = utils.get_address_from_pk(pk)
        log.info(f"Trying to deploy a contract with an account {utils.mask_string(address)}", index=index)
        
        bot = HeliosBot(private_key=pk, proxy=proxy, index=index)
        web3_client = Web3Client(private_key=pk, rpc_url=rpc_url, proxy=proxy, index=index)
        await bot.run_deployment(web3_client)

async def process_registration(session: ClientSession, semaphore: asyncio.Semaphore, pk: str, proxy: str, index: int) -> tuple[bool, str]:
    async with semaphore:
        try:
            bot = HeliosBot(private_key=pk, proxy=proxy, index=index)
            is_success = await bot.register_account(session)
            return is_success, pk
        except Exception as e:
            log.error(f"Unexpected error during account registration {index}: {e}", index=index)
            return False, pk

def generate_wallets():
    try:
        count = int(input("How many wallets would you like to create? > "))
    except ValueError:
        log.error("Invalid input, must be a number.")
        return

    log.info(f"Creating {count} new wallets...")
    wallets = []
    for i in range(count):
        account = Account.create()
        pk = account.key.hex()
        wallets.append(pk)
        log.info(f"Wallet {i+1}: address={account.address} pk=***")

    with open(config.UNREGISTERED_ACCOUNTS_FILE, 'a') as f:
        for pk in wallets:
            f.write(f"{pk}\n")
    
    log.success(f"{count} The new wallet has been saved to '{config.UNREGISTERED_ACCOUNTS_FILE}'")
    log.success(f"Run 'python main.py --register' to registering a new accounts")

async def run_mode_runner(process_function, private_keys, proxies, *args):
    semaphore = asyncio.Semaphore(_sett['MAX_CONCURRENT_TASKS'])
    async with ClientSession() as session:
        tasks = []
        for i, pk in enumerate(private_keys):
            proxy = proxies[i % len(proxies)] if proxies else None
            task = process_function(session, semaphore, pk, proxy, i + 1, *args)
            tasks.append(task)
        
        return await asyncio.gather(*tasks)

async def run_register_mode(private_keys, proxies):
    if not private_keys:
        log.warning(f"File '{config.UNREGISTERED_ACCOUNTS_FILE}' empty.")
        return

    log.info(f"Attempting to register {len(private_keys)} accounts.")
    results = await run_mode_runner(process_registration, private_keys, proxies)
    
    successful_pks = {pk for is_success, pk in results if is_success}
    if successful_pks:
        log.success(f"{len(successful_pks)} The account has been successfully registered and transferred.")
        with open(config.REGISTERED_ACCOUNTS_FILE, 'a') as f:
            for pk in successful_pks:
                f.write(f"{pk}\n")
        
        remaining_pks = [pk for pk in private_keys if pk not in successful_pks]
        with open(config.UNREGISTERED_ACCOUNTS_FILE, 'w') as f:
            f.write("\n".join(remaining_pks) + "\n")
    log.info("The registration process is complete.")

async def run_tasks_mode(private_keys, proxies, active_validators, rpc_url):
    if not private_keys:
        log.warning(f"File '{config.REGISTERED_ACCOUNTS_FILE}' empty.")
        return
    
    active_tasks = ", ".join(filter(None, [
        "Faucet" if _sett['RUN_FAUCET'] else None, 
        "Bridge" if _sett['RUN_BRIDGE'] else None, 
        "Delegate" if _sett['RUN_DELEGATE'] else None,
        "Deployment" if _sett['RUN_DEPLOYMENT'] else None,
        "Send token" if _sett['RUN_SEND_NATIVE'] else None
    ]))
    log.info(f"Starting bot for {len(private_keys)} accounts. Active Tasks: {active_tasks}")
    
    await run_mode_runner(process_account_tasks, private_keys, proxies, active_validators, rpc_url)

async def run_forever(private_keys, proxies, active_validators, rpc_url):
    while True:
        await run_tasks_mode(private_keys, proxies, active_validators, rpc_url)
        wait_minutes = _sett['TIME_SLEEP_BETWEEN_CYCLES']
        wait_seconds = wait_minutes * 60
        log.info(f"Cycle complete. Waiting {wait_minutes} minutes ({utils.format_seconds(wait_seconds)}) for the next cycle.")
        await asyncio.sleep(wait_seconds)
        
async def main():
    args = sys.argv

    if '--help' in args:
        utils.print_help_message()
        return

    mode = "run_forever"
    if '--generate' in args: mode = "generate"
    elif '--register' in args: mode = "register"
    elif '--deploy' in args: mode = "deploy"
    elif '--bridge' in args: mode = "bridge"
    elif '--delegate' in args: mode = "delegate"
    elif '--faucet' in args: mode = "faucet"
    elif '--send' in args: mode = "send"

    os.system("cls" if os.name == "nt" else "clear")
    utils._banner()

    if mode == "generate":
        generate_wallets()
        return

    active_validators = []
    rpc_url = None
    async with ClientSession() as session:
        active_validators, rpc_url = await HeliosApiClient.fetch_initial_data(session, chain="heliostestnet")

    if not rpc_url:
        log.error("Could not fetch a valid RPC URL from the server. Aborting all operations.")
        return
    
    private_keys = utils.load_from_file(config.REGISTERED_ACCOUNTS_FILE if mode != "register" else config.UNREGISTERED_ACCOUNTS_FILE)
    proxies = utils.load_from_file(config.PROXY_FILE) if _sett['USE_PROXY'] else []

    if not private_keys:
        log.warning("No private keys found to process.")
        return

    if mode in ["deploy", "bridge", "delegate", "faucet", "send"]:
        log.debug(f"Running the bot in single-task mode: {mode.upper()}")
        task_key_map = {
            "faucet": "RUN_FAUCET", "bridge": "RUN_BRIDGE", "delegate": "RUN_DELEGATE",
            "deploy": "RUN_DEPLOYMENT", "send": "RUN_SEND_NATIVE"
        }
        for key in task_key_map.values(): _sett[key] = False
        selected_key = task_key_map.get(mode)
        if selected_key: _sett[selected_key] = True
        
        await run_tasks_mode(private_keys, proxies, active_validators, rpc_url)
    
    elif mode == "register":
        await run_register_mode(private_keys, proxies)
    else: 
        await run_forever(private_keys, proxies, active_validators, rpc_url)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log.warning("Interruption accepted. Shutting down...")
    except Exception as e:
        log.error(f"A critical error occurred in the main execution block: {e}")
    finally:
        log.success("The bot has stopped.")
