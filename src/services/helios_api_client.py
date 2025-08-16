import asyncio
from aiohttp import ClientSession, ClientResponseError
from src.utils.logger import log
from config.config import settings as _sett
from src.utils.session_manager import get_user_agent

class HeliosApiClient:
    def __init__(self, session: ClientSession, private_key: str, account_address: str, access_token: str = None, index: int = None):
        self.session = session
        self.private_key = private_key
        self.RPC_URL = _sett['RPC_URL']
        self.base_url = _sett['BASE_URL']
        self.index = index
        user_agent = get_user_agent(private_key, account_address)
        
        self.headers = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
            "Content-Type": "application/json",
            "Origin": "https://testnet.helioschain.network",
            "Referer": "https://testnet.helioschain.network/",
            "User-Agent": user_agent
        }
        
        if access_token:
            self.headers["Authorization"] = f"Bearer {access_token}"

    @staticmethod
    async def fetch_initial_data(session: ClientSession) -> tuple[list[dict], str | None]:
        rpc_url = _sett['RPC_URL']
        if not rpc_url:
            log.error("RPC_URL not configured in settings.")
            return [], None

        payload = {"jsonrpc": "2.0", "method": "eth_getValidatorsByPageAndSize", "params": ["0x1", "0x64"], "id": 1}
        headers = {'Content-Type': 'application/json'}

        try:
            async with session.post(rpc_url, headers=headers, json=payload, timeout=10) as response:
                response.raise_for_status()
                data = await response.json()
                active_validators = [
                    {"Moniker": v.get('moniker'), "Contract Address": v.get('validatorAddress')}
                    for v in data.get('result', []) if v.get('status') == 3
                ]
                if active_validators:
                    log.success(f"Successfully obtained {len(active_validators)} active validators.")
                else:
                    log.warning("No active validators found.")
                return active_validators, rpc_url
        except Exception as e:
            log.error(f"Failed to retrieve validator list using RPC {rpc_url}: {e}")
            return [], rpc_url
            
    async def _request(self, method: str, endpoint: str, data: dict = None, retries=5) -> tuple[dict | None, int]:
        url = f"{self.base_url}/{endpoint}"
        for attempt in range(retries):
            try:
                async with self.session.request(method, url, headers=self.headers, json=data) as response:
                    status = response.status
                    if response.ok:
                        return await response.json(), status
                    response.raise_for_status()
            except ClientResponseError as e:
                log.error(f"API Error on {endpoint}: {e.status} {e.message}", index=self.index)
                return None, e.status
            except Exception as e:
                log.error(f"Request failed on {endpoint}: {e}", index=self.index)
                return None, -1
            if attempt < retries - 1: await asyncio.sleep(5)
        return None, 0

    async def login(self, signature_payload: dict) -> tuple[dict | None, int]:
        return await self._request("POST", "users/login", data=signature_payload)

    async def confirm_account(self, signature_payload: dict) -> tuple[dict | None, int]:
        payload = {**signature_payload, "inviteCode": _sett['INVITE_CODE']}
        return await self._request("POST", "users/confirm-account", data=payload)

    async def start_onboarding_step(self, step_key: str) -> tuple[dict | None, int]:
        payload = {"stepKey": step_key}
        return await self._request("POST", "users/onboarding/start", data=payload)
    
    async def complete_onboarding_step(self, step_key: str, evidence: str) -> tuple[dict | None, int]:
        payload = {"stepKey": step_key, "evidence": evidence}
        return await self._request("POST", "users/onboarding/complete", data=payload)

    async def check_eligibility(self) -> tuple[dict | None, int]:
        payload = {"token": "HLS", "chain": "helios-testnet"}
        return await self._request("POST", "faucet/check-eligibility", data=payload)

    async def request_faucet(self, turnstile_token: str) -> tuple[dict | None, int]:
        payload = {"token": "HLS", "chain": "helios-testnet", "amount": 1, "turnstileToken": turnstile_token}
        return await self._request("POST", "faucet/request", data=payload)
        
    async def claim_onboarding_reward(self) -> tuple[dict | None, int]:
        payload = {"rewardType": "xp"}
        return await self._request("POST", "users/onboarding/claim-reward", data=payload)
