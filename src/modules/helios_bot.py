import random, os
import asyncio
from aiohttp import ClientSession
from aiohttp_socks import ProxyConnector

from src.utils.logger import log
import src.utils.utils as utils
from src.services.helios_api_client import HeliosApiClient
from src.services.web3_client import Web3Client
from src.services.captcha_client import CaptchaSolver
from config import config as _conf
from config.config import settings as _sett

def get_recipient_address(sender_address: str):
    file_path = _conf.WALLET_ADDRESS_LIST
    if not os.path.exists(file_path):
        log.warning(f"The file “{file_path}” was not found.")
        return None

    with open(file_path, 'r') as f:
        addresses = [line.strip() for line in f if line.strip()]

    if not addresses:
        log.warning(f"The file '{file_path}' is empty.")
        return None
        
    valid_recipients = [addr for addr in addresses if addr.lower() != sender_address.lower()]

    if not valid_recipients:
        log.warning("There is no valid recipient address (other than the sender's address).")
        return None
        
    return random.choice(valid_recipients)

class HeliosBot:
    def __init__(self, private_key: str, proxy: str = None, index: int = 0):
        self.private_key = private_key
        self.proxy = proxy
        self.index = index
        self.account, self.address = utils.generate_wallet_details(private_key)

    async def _register_and_onboard(self, session: ClientSession, signature_payload: dict) -> str | None:
        log.info("Trying to register a new account...", index=self.index)
        api = HeliosApiClient(session, self.private_key, self.address, index=self.index)
        
        confirm_data, status_code = await api.confirm_account(signature_payload)
        
        if confirm_data and confirm_data.get("success"):
            log.success("Account successfully created. Starting initial onboarding...", index=self.index)
            access_token = confirm_data.get("token")
            api_with_auth = HeliosApiClient(session, self.private_key, self.address, access_token, self.index)
            
            await api_with_auth.start_onboarding_step("add_helios_network")
            await asyncio.sleep(1)
            complete_data, _ = await api_with_auth.complete_onboarding_step("add_helios_network", "network_added")
            
            if complete_data and complete_data.get("success"):
                xp = complete_data.get("xpAwarded", 0)
                log.success(f"Initial onboarding complete! Earned {xp} XP.", index=self.index)
            
            return access_token

        if status_code == 429:
            log.error(f"Registration failed (429): Invite code '{_sett['INVITE_CODE']}' limit reached.", index=self.index)
        elif confirm_data and "IP address" in confirm_data.get("message", ""):
            log.error("Registration failed: This IP already has an account. Change proxy.", index=self.index)
        else:
            log.error(f"Account registration failed (status: {status_code}).", index=self.index)
        
        return None

    async def _complete_final_onboarding(self, api_with_auth: HeliosApiClient):
        log.info("Begin final onboarding completion...", index=self.index)
        
        await asyncio.sleep(2)
        await api_with_auth.start_onboarding_step("claim_from_faucet")
        await asyncio.sleep(1)
        res, _ = await api_with_auth.complete_onboarding_step("claim_from_faucet", "tokens_claimed")
        if res and res.get("success"):
            log.success(f"Onboarding Faucet completed, Earned {res.get('xpAwarded', 0)} XP.", index=self.index)

        await asyncio.sleep(2)
        await api_with_auth.start_onboarding_step("mint_early_bird_nft")
        await asyncio.sleep(1)
        res, _ = await api_with_auth.complete_onboarding_step("mint_early_bird_nft", "nft_minted")
        if res and res.get("success"):
            log.success(f"NFT onboarding complete, Earned {res.get('xpAwarded', 0)} XP.", index=self.index)

        await asyncio.sleep(2)
        res, _ = await api_with_auth.claim_onboarding_reward()
        if res and res.get("success"):
            log.success(f"SUCCESS! Final onboarding reward claimed, Earned {res.get('xpAwarded', 0)} XP.", index=self.index)

    async def _registration_logic(self, session: ClientSession) -> bool:
        signature_payload = utils.generate_signature_payload(self.account, self.address)
        access_token = await self._register_and_onboard(session, signature_payload)
        
        if not access_token:
            return False

        log.info("Continue to Faucet claim for new accounts...", index=self.index)
        api_with_auth = HeliosApiClient(session, self.private_key, self.address, access_token, self.index)
        
        solver = CaptchaSolver(session, index=self.index)
        turnstile_token = await solver.solve_captcha()
        if not turnstile_token:
            log.error("Failed to complete captcha, registration process stopped.", index=self.index)
            return False

        faucet_result, _ = await api_with_auth.request_faucet(turnstile_token)
        if faucet_result and faucet_result.get("success"):
            log.success("Successfully claimed 1 HLS from the faucet.", index=self.index)
            await self._complete_final_onboarding(api_with_auth)
            return True
        else:
            log.error("Faucet claim failed. Registration process not fully completed.", index=self.index)
            return False

    async def register_account(self, session: ClientSession):
        return await self._registration_logic(session)

    async def run_faucet(self, session: ClientSession):
        signature_payload = utils.generate_signature_payload(self.account, self.address)
        api = HeliosApiClient(session, self.private_key, self.address, index=self.index)
        
        login_data, status_code = await api.login(signature_payload)

        if not (login_data and login_data.get("success")):
            log.error(f"Login failed (status: {status_code}). The account may not be registered yet. Use the --register mode.", index=self.index)
            return

        access_token = login_data.get("token")
        api_with_auth = HeliosApiClient(session, self.private_key, self.address, access_token, index=self.index)
        
        eligibility_data, _ = await api_with_auth.check_eligibility()
        if not eligibility_data or not eligibility_data.get("isEligible"):
            log.warning("Not eligible for faucet (possibly cooldown).", index=self.index)
            return
            
        log.info("Account is eligible for faucet. Processing captcha...", index=self.index)
        solver = CaptchaSolver(session, index=self.index)
        turnstile_token = await solver.solve_captcha()
        if not turnstile_token:
            log.error("Failed to complete captcha.", index=self.index)
            return

        faucet_result, _ = await api_with_auth.request_faucet(turnstile_token)
        if faucet_result and faucet_result.get("success"):
            log.success("Successfully claimed 1 HLS from the faucet.", index=self.index)
        else:
            log.error("Claim failed from the faucet.", index=self.index)

    async def run_bridge(self, web3_client: Web3Client, amount: float):
        try:
            balance = await web3_client.get_hls_balance()
            log.info(f"Current HLS balance: {balance:.4f}", index=self.index)
            if balance < amount:
                log.error(f"Insufficient balance. {amount:.4f} is required, {balance:.4f} is available.", index=self.index)
                return
            await web3_client.bridge(amount)
        except Exception as e:
            log.error(f"Bridge operation error: {e}", index=self.index)

    async def run_delegate(self, web3_client: Web3Client, amount: float, validator_list: list):
        try:
            balance = await web3_client.get_hls_balance()
            log.info(f"Current HLS balance: {balance:.4f}", index=self.index)
            if balance < amount:
                log.error(f"Insufficient balance. {amount:.4f} is required, {balance:.4f} is available.", index=self.index)
                return
            await web3_client.delegate(amount, validator_list)
        except Exception as e:
            log.error(f"Delegate operation error: {e}", index=self.index)

    async def run_deployment(self, web3_client: Web3Client):
        try:
            if not _conf.CONTRACT_ABI or not _conf.CONTRACT_BYTECODE:
                log.error("ABI/Bytecode not loaded. Check 'abi/deploy_abi.json'.", index=self.index)
                return

            constructor_args = _sett['DEPLOY_CONSTRUCTOR_ARGS']
            balance = await web3_client.get_hls_balance()
            log.info(f"Current HLS balance: {balance:.4f}", index=self.index)
            
            min_balance_for_gas = 0.01
            if balance < min_balance_for_gas:
                log.warning(f"Insufficient balance for gas fee. Requires > {min_balance_for_gas}, available {balance:.4f}", index=self.index)
                return 

            await web3_client.deploy_contract(
                abi=_conf.CONTRACT_ABI,
                bytecode=_conf.CONTRACT_BYTECODE,
                constructor_args=constructor_args
            )
        except Exception as e:
            log.error(f"Deployment process error: {e}", index=self.index)

    async def run_send_native(self, web3_client: Web3Client, amount: float):
        try:
            recipient = get_recipient_address(self.address)

            if not recipient:
                log.error("Failed to get recipient. Make sure 'wallets.txt' exists and contains other address.", index=self.index)
                return

            balance = await web3_client.get_hls_balance()
            log.info(f"Current HLS balance: {balance:.4f}", index=self.index)

            if balance < amount:
                log.error(f"Insufficient balance. Need > {amount:.4f}, available {balance:.4f}", index=self.index)
                return

            await web3_client.send_native_token(recipient, amount)

        except Exception as e:
            log.error(f"Native delivery operation error: {e}", index=self.index)
