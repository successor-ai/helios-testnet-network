import asyncio
from aiohttp import ClientSession
from src.utils.logger import log
from config.config import settings as _sett

class CaptchaSolver:
    def __init__(self, session: ClientSession, index: int = None):
        self.session = session
        self.index = index
        self.service_name = _sett.get("CAPTCHA_SERVICE", "").lower()
        self.api_key = None
        self.create_task_url = None
        self.get_result_url = None

        if self.service_name == "2captcha":
            self.api_key = _sett.get("API_KEY_2CAPTCHA")
            self.create_task_url = "https://api.2captcha.com/createTask"
            self.get_result_url = "https://api.2captcha.com/getTaskResult"

        elif self.service_name == "anticaptcha":
            self.api_key = _sett.get("API_KEY_ANTI_CAPTCHA")
            self.create_task_url = "https://api.anti-captcha.com/createTask"
            self.get_result_url = "https://api.anti-captcha.com/getTaskResult"
        
        elif self.service_name == "capmonster":
            self.api_key = _sett.get("API_KEY_CAPMONSTER")
            self.create_task_url = "https://api.capmonster.cloud/createTask"
            self.get_result_url = "https://api.capmonster.cloud/getTaskResult"

        else:
            if self.service_name:
                log.warning(f"The Captcha service “{self.service_name}” is invalid.", index=self.index)

        if self.service_name and not self.api_key:
            log.warning(f"API Key for {self.service_name} not found. Captcha verification will be skipped.", index=self.index)

        self.website_url = _sett.get("CAPTCHA_PAGE_URL")
        self.website_key = _sett.get("CAPTCHA_SITE_KEY")

    async def solve_captcha(self) -> str | None:
        if not all([self.api_key, self.create_task_url, self.website_url, self.website_key]):
            log.error("Captcha configuration incomplete. Process cancelled.", index=self.index)
            return None

        log.info(f"Completing the Turnstile captcha using {self.service_name}...", index=self.index)

        task_payload = {
            "clientKey": self.api_key,
            "task": {
                "type": "TurnstileTaskProxyless",
                "websiteURL": self.website_url,
                "websiteKey": self.website_key,
            },
        }
        
        try:
            async with self.session.post(self.create_task_url, json=task_payload) as response:
                if response.status != 200:
                    log.error(f"Failed to create captcha task ({response.status}): {await response.text()}", index=self.index)
                    return None
                
                resp_json = await response.json()
                if resp_json.get("errorId", 0) > 0:
                    log.error(f"Error from API {self.service_name}: {resp_json.get('errorDescription')}", index=self.index)
                    return None
                
                task_id = resp_json.get("taskId")
                if not task_id:
                    log.error("Failed to obtain taskId from response.", index=self.index)
                    return None
        except Exception as e:
            log.error(f"Exception when creating a captcha task: {e}", index=self.index)
            return None

        log.info(f"The captcha task was successfully created with ID: {task_id}", index=self.index)

        result_payload = {"clientKey": self.api_key, "taskId": task_id}
        
        for _ in range(36):
            await asyncio.sleep(5)
            try:
                async with self.session.post(self.get_result_url, json=result_payload) as response:
                    if response.status != 200:
                        log.warning(f"Failed to retrieve captcha results ({response.status}): {await response.text()}", index=self.index)
                        continue

                    result_json = await response.json()
                    status = result_json.get("status")

                    if status == "ready":
                        log.success("Captcha successfully completed!", index=self.index)
                        return result_json.get("solution", {}).get("token")
                    
                    if status == "processing":
                        log.info("Captcha is still processing...", index=self.index)
                        continue
                    
                    if result_json.get("errorId", 0) > 0:
                        log.error(f"Error retrieving results: {result_json.get('errorDescription')}", index=self.index)
                        return None

            except Exception as e:
                log.error(f"Exception when retrieving captcha results: {e}", index=self.index)
                return None
        
        log.error("The captcha completion time has expired (timeout).", index=self.index)
        return None
