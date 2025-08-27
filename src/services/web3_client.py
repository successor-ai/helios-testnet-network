import asyncio
import random
from web3 import Web3
from web3.exceptions import TransactionNotFound
from eth_abi.abi import encode

from src.utils.logger import log
from config import config
from src.utils import constant as _const
import src.utils.utils as utils
from config.config import settings as _sett

class Web3Client:
    def __init__(self, private_key: str, rpc_url: str, proxy: str = None, index: int = None):
        self.account, self.address = utils.generate_wallet_details(private_key)
        self.index = index
        
        request_kwargs = {"timeout": 60}
        if proxy:
            request_kwargs["proxies"] = {"http": proxy, "https": proxy}
            
        self.w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs=request_kwargs))

        if not self.w3.is_connected():
            log.error(f"Failed to connect to RPC: {rpc_url}", index=self.index)
            raise ConnectionError("Failed to connect to RPC")

        self.nonce = self.w3.eth.get_transaction_count(self.address, 'pending')
    
    async def _wait_for_receipt(self, tx_hash: str, retries=5):
        for i in range(retries):
            try:
                receipt = await asyncio.to_thread(self.w3.eth.wait_for_transaction_receipt, tx_hash, timeout=300)
                return receipt
            except (Exception, TransactionNotFound):
                log.warning(f"Receipt not found for {tx_hash}, retrying ({i+1}/{retries})...", index=self.index)
                await asyncio.sleep(10)
        raise Exception(f"Transaction receipt not found for {tx_hash} after maximum retries.", index=self.index)

    async def get_hls_balance(self) -> float:
        balance_wei = self.w3.eth.get_balance(self.address)
        return Web3.from_wei(balance_wei, 'ether')

    async def approve(self, spender: str, amount: float):
        token_contract = self.w3.eth.contract(address=self.w3.to_checksum_address(_const.HLS_CONTRACT_ADDRESS), abi=config.ERC20_ABI)
        amount_wei = Web3.to_wei(amount, 'ether')
        
        allowance = token_contract.functions.allowance(self.address, spender).call()
        if allowance >= amount_wei:
            return True
        
        log.info(f"Approving {amount} HLS", index=self.index)
        tx_data = token_contract.functions.approve(spender, amount_wei)
        
        tx = tx_data.build_transaction({
            "from": self.address,
            "nonce": self.nonce,
            "gas": 150000,
            "gasPrice": self.w3.eth.gas_price 
        })
        
        signed_tx = self.account.sign_transaction(tx)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)

        self.nonce += 1
        
        receipt = await self._wait_for_receipt(tx_hash.hex())
        if receipt and receipt['status'] == 1:
            log.success(f"Approval successful! Block: {receipt.blockNumber}", index=self.index)
            return True
        else:
            log.error("Approval failed!", index=self.index)
            return False

    async def bridge(self, amount: float):
        if not await self.approve(_const.BRIDGE_ROUTER_ADDRESS, amount):
            return None
        
        destination = random.choice(_const.DESTINATION_CHAINS)
        log.info(f"Bridging {amount:.7f} HLS to {destination['Ticker']}...", index=self.index)
        
        bridge_amount_wei = Web3.to_wei(amount, 'ether')
        estimated_fees = int(bridge_amount_wei * 0.01)

        encoded_data = (
            utils.pad_hex(destination['ChainId']) +
            utils.pad_hex(160) +
            utils.encode_hex_as_string(_const.HLS_CONTRACT_ADDRESS) +
            utils.pad_hex(bridge_amount_wei) +
            utils.pad_hex(estimated_fees) +
            utils.pad_hex(42) +
            utils.encode_string_as_bytes(self.address)
        )
        calldata = "0x7ae4a8ff" + encoded_data

        tx = {
            "to": _const.BRIDGE_ROUTER_ADDRESS,
            "from": self.address,
            "data": calldata,
            "value": 0,
            "nonce": self.nonce,
            "chainId": self.w3.eth.chain_id
        }

        gas = self.w3.eth.estimate_gas(tx)
        tx['gas'] = int(gas * 1.2)
        tx['gasPrice'] = self.w3.eth.gas_price

        signed_tx = self.account.sign_transaction(tx)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        
        self.nonce += 1
        
        receipt = await self._wait_for_receipt(tx_hash.hex())
        if receipt and receipt['status'] == 1:
            log.success(f"Bridge {amount:.7f} successful!", index=self.index)
            log.success(f"Tx: {_sett['EXPLORER_URL']}{tx_hash.hex()}", index=self.index)
            return tx_hash.hex()
        return None

    async def delegate(self, amount: float, validator_list: list):
        if not validator_list:
            log.error("The validator list is empty. Delegation is not possible.", index=self.index)
            return None

        validator = random.choice(validator_list)
        log.info(f"Delegation of {amount:.4f} HLS to {validator['Moniker']}...", index=self.index)

        delegate_amount_wei = Web3.to_wei(amount, 'ether')
        
        encoded_data = encode(
            ["address", "address", "uint256", "bytes"],
            [self.address.lower(), validator["Contract Address"].lower(), delegate_amount_wei, "ahelios".encode("utf-8")]
        )
        calldata = "0xf5e56040" + encoded_data.hex()
        
        tx = {
            "to": _const.DELEGATE_ROUTER_ADDRESS,
            "from": self.address,
            "data": calldata,
            "value": 0,
            "nonce": self.nonce,
            "chainId": self.w3.eth.chain_id
        }
        
        gas = self.w3.eth.estimate_gas(tx)
        tx['gas'] = int(gas * 1.2)
        tx['gasPrice'] = self.w3.eth.gas_price

        signed_tx = self.account.sign_transaction(tx)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)

        self.nonce += 1
        
        receipt = await self._wait_for_receipt(tx_hash.hex())
        if receipt and receipt['status'] == 1:
            log.success(f"Delegation successful {amount:.4f} HLS to {validator['Moniker']}!", index=self.index)
            log.success(f"Tx: {_sett['EXPLORER_URL']}{tx_hash.hex()}", index=self.index)
            return tx_hash.hex()
        return None
    
    async def deploy_contract(self, abi: list, bytecode: str, constructor_args: list):
        log.info(f"Deploy the contract with constructor arguments: {constructor_args}", index=self.index)
        
        Contract = self.w3.eth.contract(abi=abi, bytecode=bytecode)
        tx_data = Contract.constructor(*constructor_args).build_transaction({
            'from': self.address,
            'nonce': self.nonce,
            'gasPrice': self.w3.eth.gas_price
        })
        
        gas = self.w3.eth.estimate_gas(tx_data)
        tx_data['gas'] = int(gas * 1.2)
        
        signed_tx = self.account.sign_transaction(tx_data)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        self.nonce += 1
        
        log.info(f"Deployment transaction sent:", index=self.index) 
        log.info(f"tx: {_sett['EXPLORER_URL']}{tx_hash.hex()}", index=self.index)
        receipt = await self._wait_for_receipt(tx_hash.hex())
        if receipt and receipt['status'] == 1:
            contract_address = receipt['contractAddress']
            log.success(f"Contract successfully deployed: {contract_address}", index=self.index)
            return contract_address
        else:
            log.error("Deployment contract failed!", index=self.index)
            return None
        
    async def send_native_token(self, recipient_address: str, amount: float):
        log.info(f"Sending {amount:.5f} HLS to {utils.mask_string(recipient_address)}", index=self.index)
        
        amount_wei = self.w3.to_wei(amount, 'ether')
        
        tx_data = {
            'to': self.w3.to_checksum_address(recipient_address),
            'from': self.address,
            'value': amount_wei,
            'nonce': self.nonce,
            'chainId': self.w3.eth.chain_id
        }
        
        gas = self.w3.eth.estimate_gas(tx_data)
        tx_data['gas'] = int(gas * 1.2)
        tx_data['gasPrice'] = self.w3.eth.gas_price

        signed_tx = self.account.sign_transaction(tx_data)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        self.nonce += 1
        
        receipt = await self._wait_for_receipt(tx_hash.hex())
        if receipt and receipt['status'] == 1:
            log.success(f"Send {amount:.5f} HLS successfully!", index=self.index)
            log.success(f"Tx: {_sett['EXPLORER_URL']}{tx_hash.hex()}", index=self.index)
            return tx_hash.hex()
        else:
            log.error(f"Failed to send HLS to {utils.mask_string(recipient_address)}", index=self.index)
            return None