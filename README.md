# Helios Testnet Full Automations Bot

### Description
This bot is dedicated to automation enthusiasts, as it can now interact with the Helios Network Testnet — such as claiming faucets, sending tokens, delegating/staking, bridging tokens to tokens, and much more.

### Setup Instructions:
-  Python `3.7 or higher` (recommended 3.9 or 3.10 due to asyncio usage).
-  pip (Python package installer)

### Features
-  **Proxy Support**: Supports both mobile and regular proxies.
-  **Multithread support**: Run your bot faster.
-  **User Agent**: Support saving session for `UserAgent`.
-  **Faucet**: Support auto claiming `official faucet`.
-  **Captcha Solver**: Completing `captcha` for faucet.
-  **Auto Referral**: Support to Register a new account with Referral.
-  **Generate Wallet**: This bot can generate a new wallet for you.
-  **Wallet Handling**: `Shuffle` wallets and `configure` pauses between operations.
-  **Send Token**: This bot can sending HLS token to another wallet.
-  **Bridge Token**: This bot can Bridge token to token eg `HELIOS to FUJI` or `HELIOS to SEPOLIA`.
-  **Delegate Token**: This bot can Delegate a HLS token to available validators.
-  **Deploy Contract**: This bot can Deploying a contract for you.
-  **Auto Register**: This bot can register new accounts that have never been registered with your referral code.
-  **Configurable**: All the features in this bot can be configured according to your preferences.


### Usage
#### Installation and startup

1. Clone this repository:
   ```bash
   git clone https://github.com/successor-ai/helios-testnet-network.git
   cd helios-testnet-network
   ```
2. Create virtual environment (optional but recomended)
   ```bash
   python -m venv venv
   ```

   Once created, you need to activate the virtual environment. The method for activating it varies depending on your operating system:
   
    #### On Windows
    ```bash
    venv\Scripts\activate
    ```
    #### On macOS/Linux
    ```bash
    source venv/bin/activate
    ```
3. Install the dependencies:
   The requirements.txt ensure your requirements.txt looks like this before installing:
   ```yaml
    python-dotenv
    web3==6.15.1
    eth-account
    aiohttp
    aiohttp-socks
    colorama
    fake-useragent
   ```
   Then install:
   ```bash
   pip install -r requirements.txt
   ```    

### Configuration
All settings are in `.env`. Key options include:

#### Feature Settings
```yaml
RUN_BRIDGE=false
RUN_DELEGATE=false
RUN_DEPLOYMENT=false
RUN_SEND_NATIVE=false

BRIDGE_COUNT=[1, 2]
BRIDGE_AMOUNT=[0.0001, 0.0005]

DELEGATE_COUNT=[1, 2]
DELEGATE_AMOUNT=[0.0001, 0.0002]

DEPLOYMENT_COUNT=[1, 2]
DEPLOY_CONSTRUCTOR_ARGS='["Hello from Helios!"]'

SEND_COUNT=[1, 2]
SEND_AMOUNT=[0.0001, 0.0005]
```

- `RUN_BRIDGE, DELEGATE, DEPLOYMENT, SEND_NATIVE, FAUCET` : Set it to `true` or `false`
- `DELEGATE_COUNT, DELEGATE_COUNT [value, value]`: These values are the min and max values that will be randomised.

#### Add your Private Key on `private_key.txt`
   ```txt
   your_private_key
   your_private_key
   ```
#### Add your Proxies on `proxies.txt`
   ```yaml
   http://login:pass@ip:port
   http://login:pass@ip:port
   ```
#### Add referral & wallet
   - Change `example.env` to `.env` and fill your referral code on `INVITE_CODE`
   - Fill the `wallets.txt` with your receiver token address

### Run (first module, then second module):
   ```bash
    python main.py
   ```

### For argument help
   ```bash
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
   ```
     
### Contributing

Submit pull requests or report issues. Ensure your code follows best practices.

### License

This project is open-source—modify and distribute as needed.
