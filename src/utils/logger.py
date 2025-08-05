import sys
import random
from datetime import datetime
from colorama import Fore, Style, init

init(autoreset=True)

class ManualLogger:
    _index_colors = [
        Fore.GREEN, Fore.YELLOW, Fore.BLUE, Fore.MAGENTA, Fore.CYAN,
        Fore.LIGHTGREEN_EX, Fore.LIGHTYELLOW_EX, Fore.LIGHTBLUE_EX,
        Fore.LIGHTMAGENTA_EX, Fore.LIGHTCYAN_EX
    ]

    def __init__(self):
        self._assigned_index_colors = {}

    def _log(self, level_name: str, color: str, message: str, index: int = None):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        formatted_level = f"{color}{level_name:^9}{Style.RESET_ALL}"
        
        index_str = ""
        if index is not None:
            if index not in self._assigned_index_colors:
                self._assigned_index_colors[index] = random.choice(self._index_colors)
            
            persistent_color = self._assigned_index_colors[index]
            
            colored_index = f"{persistent_color}{index:<4}{Style.RESET_ALL}"
            index_str = f"| {colored_index} "
        
        print(f"{Fore.LIGHTBLACK_EX}{timestamp}{Style.RESET_ALL} | {formatted_level} {index_str}| {message}", file=sys.stdout, flush=True)

    def debug(self, message: str, index: int = None):
        self._log("DEBUG", Fore.CYAN, message, index)

    def info(self, message: str, index: int = None):
        self._log("INFO", Fore.LIGHTBLUE_EX, message, index)

    def success(self, message: str, index: int = None):
        self._log("SUCCESS", Fore.LIGHTGREEN_EX, message, index)

    def warning(self, message: str, index: int = None):
        self._log("WARNING", Fore.LIGHTYELLOW_EX, message, index)

    def error(self, message: str, index: int = None):
        self._log("ERROR", Fore.LIGHTRED_EX, message, index)
    
    def critical(self, message: str, index: int = None):
        self._log("CRITICAL", Fore.RED + Style.BRIGHT, message, index)

log = ManualLogger()