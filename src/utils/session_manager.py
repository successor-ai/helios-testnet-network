import json
import os
from fake_useragent import UserAgent

SESSION_FILE = "session_ua.json"

def _load_sessions() -> dict:
    if not os.path.exists(SESSION_FILE):
        return {}
    try:
        with open(SESSION_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {}

def _save_sessions(sessions: dict):
    with open(SESSION_FILE, 'w') as f:
        json.dump(sessions, f, indent=4)

def get_user_agent(private_key: str, account_address: str) -> str:
    sessions = _load_sessions()
    if account_address in sessions:
        return sessions[account_address]
    else:
        try:
            ua = UserAgent()
            new_ua = ua.random
        except Exception:
            new_ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
        
        sessions[account_address] = new_ua
        _save_sessions(sessions)
        return new_ua
