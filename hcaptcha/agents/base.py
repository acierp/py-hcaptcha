from typing import Literal

class Agent:
    user_agent: str
    header_order: dict

    def __init__(self):
        self._epoch_delta = 0

    def get_screen_properties(self) -> dict:
        return
    
    def get_navigator_properties(self) -> dict:
        return

    def epoch(self, ms: bool = True) -> float:
        return

    def epoch_travel(self, delta: float, ms: bool = True):
        return

    def epoch_wait(self):
        return

    def json_encode(self, data: Literal):
        return

    def url_encode(self, data: dict) -> str:
        return
    
    def format_headers(
        self,
        url: str,
        headers: dict = {},
        origin_url: str = None,
        sec_site: str = "cross-site",
        sec_mode: str = "cors",
        sec_dest: str = "empty"
    ) -> dict:
        return