from .constants import *
from .agents import Agent, random_agent
from .models import Tile
from .structures import EventRecorder
from .proofs import get_proof
from .curves import gen_mouse_move
from .utils import parse_proxy_string, random_widget_id, latest_version_id
from .exceptions import *
from typing import Iterator, List
from random import randint
from urllib.parse import urlsplit
from http.client import HTTPSConnection
import json
import ssl
import zlib

class Challenge:
    _version_id = latest_version_id()
    _default_ssl_context = ssl.create_default_context()

    id: str
    token: str
    config: dict
    mode: str
    question: dict
    tiles: List[Tile]

    def __init__(
        self,
        site_key: str,
        site_url: str,
        agent: Agent = None,
        http_proxy: str = None,
        timeout: float = 5,
        ssl_context: ssl.SSLContext = _default_ssl_context
    ):
        agent = agent or random_agent()

        self._site_key = site_key
        self._site_url = site_url
        self._site_hostname = urlsplit(site_url).hostname
        self._agent = agent
        self._http_proxy = parse_proxy_string(http_proxy)
        self._timeout = timeout
        self._ssl_context = ssl_context
        self._conn_map = {}

        self._widget_id = random_widget_id()
        self._spec = None
        self._answers = []
        self.id = None
        self.token = None
        self.config = None
        self.mode = None
        self.question = None
        self.tiles = None

        self._agent.epoch_travel(-10)
        self._setup_frames()
        self._validate_config()
        self._get_captcha()
        self._frame.set_data("dct", self._frame._manifest["st"])

    def __iter__(self) -> Iterator[Tile]:
        if not self.tiles: return
        yield from self.tiles

    def close(self) -> None:
        for conn in self._conn_map.values():
            conn.close()

    def answer(self, tile: Tile) -> None:
        assert isinstance(tile, Tile), "Not a tile object."
        self._answers.append(tile)
    
    def submit(self) -> str:
        if self.token: return self.token
    
        self._simulate_solve()
        self._agent.epoch_wait()
        data = self._request(
            method="POST",
            url=f"https://hcaptcha.com/checkcaptcha/{self.id}"
                f"?s={self._site_key}",
            headers={
                "Accept": "*/*",
                "Content-type": "application/json;charset=UTF-8"
            },
            body=self._agent.json_encode({
                "v": self._version_id,
                "job_mode": self.mode,
                "answers": {
                    tile.id: "true" if tile in self._answers else "false"
                    for tile in self.tiles
                },
                "serverdomain": self._site_hostname,
                "sitekey": self._site_key,
                "motionData": self._agent.json_encode({
                    **self._frame.get_data(),
                    "topLevel": self._top.get_data(),
                    "v": 1
                }),
                "n": self._get_proof(),
                "c": self._agent.json_encode(self._spec)
            }),
            origin_url="https://newassets.hcaptcha.com/",
            sec_site="same-site",
            sec_mode="cors",
            sec_dest="empty"
        )
        self.close()

        if not data.get("pass"):
            raise RequestRejected("Submit request was rejected.")

        self.token = data["generated_pass_UUID"]
        return self.token

    def _setup_frames(self):
        self._top = EventRecorder(agent=self._agent)
        self._top.record()
        self._top.set_data("dr", "") # refferer
        self._top.set_data("inv", False)
        self._top.set_data("sc", self._agent.get_screen_properties())
        self._top.set_data("nv", self._agent.get_navigator_properties())
        self._top.set_data("exec", False)
        self._agent.epoch_travel(randint(200, 400))

        self._frame = EventRecorder(agent=self._agent)
        self._frame.record()

    def _get_proof(self):
        if not self._spec: return
        return get_proof(self._spec["type"], self._spec["req"])

    def _simulate_solve(self):
            total_pages = max(1, int(len(self.tiles)/TILES_PER_PAGE))
            cursor_pos = (
                randint(1, 5),
                randint(300, 350)
            )

            for page in range(total_pages):
                page_tiles = self.tiles[page * TILES_PER_PAGE : (page + 1) * TILES_PER_PAGE]
                for tile in page_tiles:
                    if not tile in self._answers:
                        continue
                    tile_pos = (
                        (TILE_IMAGE_SIZE[0] * int(tile.index % TILES_PER_ROW))
                            + TILE_IMAGE_PADDING[0] * int(tile.index % TILES_PER_ROW)
                            + randint(10, TILE_IMAGE_SIZE[0])
                            + TILE_IMAGE_START_POS[0],
                        (TILE_IMAGE_SIZE[1] * int(tile.index / TILES_PER_ROW))
                            + TILE_IMAGE_PADDING[1] * int(tile.index / TILES_PER_ROW)
                            + randint(10, TILE_IMAGE_SIZE[1])
                            + TILE_IMAGE_START_POS[1],
                    )
                    for event in gen_mouse_move(cursor_pos, tile_pos, self._agent,
                            offsetBoundaryX=0, offsetBoundaryY=0, leftBoundary=0,
                            rightBoundary=FRAME_SIZE[0], upBoundary=FRAME_SIZE[1],
                            downBoundary=0):
                        self._frame.record_event("mm", event)
                    # TODO: add time delay for mouse down and mouse up
                    self._frame.record_event("md", event)
                    self._frame.record_event("mu", event)
                    cursor_pos = tile_pos
                
                # click verify/next/skip btn
                btn_pos = (
                    VERIFY_BTN_POS[0] + randint(5, 50),
                    VERIFY_BTN_POS[1] + randint(5, 15),
                )
                for event in gen_mouse_move(cursor_pos, btn_pos, self._agent,
                        offsetBoundaryX=0, offsetBoundaryY=0, leftBoundary=0,
                        rightBoundary=FRAME_SIZE[0], upBoundary=FRAME_SIZE[1],
                        downBoundary=0):
                    self._frame.record_event("mm", event)
                # TODO: add time delay for mouse down and mouse up
                self._frame.record_event("md", event)
                self._frame.record_event("mu", event)
                cursor_pos = btn_pos

    def _validate_config(self):
        data = self._request(
            method="GET",
            url="https://hcaptcha.com/checksiteconfig"
               f"?host={self._site_hostname}&sitekey={self._site_key}&sc=1&swa=1",
            headers={
                "Cache-Control": "no-cache",
                "Content-type": "application/json; charset=utf-8"
            },
            origin_url="https://newassets.hcaptcha.com/",
            sec_site="same-site",
            sec_mode="cors",
            sec_dest="empty"
        )

        if not data.get("pass"):
            raise RequestRejected(
                "Validation request failed. Are you sure the site key is valid?")

    def _get_captcha(self):
        data = self._request(
            method="POST",
            url="https://hcaptcha.com/getcaptcha"
               f"?s={self._site_key}",
            headers={
                "Accept": "application/json",
                "Content-type": "application/x-www-form-urlencoded"
            },
            body=self._agent.url_encode({
                "v": self._version_id,
                "sitekey": self._site_key,
                "host": self._site_hostname,
                "hl": "en",
                "motionData": self._agent.json_encode({
                    "v": 1,
                    **self._frame.get_data(),
                    "topLevel": self._top.get_data(),
                    "session": {},
                    "widgetList": [self._widget_id],
                    "widgetId": self._widget_id,
                    "href": self._site_url,
                    "prev": {
                        "escaped": False,
                        "passed": False,
                        "expiredChallenge": False,
                        "expiredResponse": False
                    }
                }),
                "n": self._get_proof(),
                "c": self._agent.json_encode(self._spec)
            }),
            origin_url="https://newassets.hcaptcha.com/",
            sec_site="same-site",
            sec_mode="cors",
            sec_dest="empty"
        )
        
        if data.get("pass"):
            self.token = data["generated_pass_UUID"]
            return
        
        self.id = data["key"]
        self.config = data["request_config"]
        self.mode = data["request_type"]
        self.question = data["requester_question"]
        self.tiles = [
            Tile(id=info["task_key"],
                 image_url=info["datapoint_uri"],
                 index=index,
                 challenge=self)
            for index, info in enumerate(data["tasklist"])
        ]

    def _get_tile_image(self, image_url):
        data = self._request(
            method="GET",
            url=image_url,
            headers={"Accept-Encoding": "gzip, deflate, br"}
        )
        return data

    def _request(
        self,
        method: str,
        url: str,
        headers: dict = {},
        body: bytes = None,
        origin_url: str = None,
        sec_site: str = "cross-site",
        sec_mode: str = "cors",
        sec_dest: str = "empty"
    ):
        if isinstance(body, str):
            body = body.encode()
        
        p_url = urlsplit(url)
        addr = (p_url.hostname.lower(), p_url.port or 443)

        conn = self._conn_map.get(addr)
        if not conn:
            if not self._http_proxy:
                conn = HTTPSConnection(
                    *addr,
                    timeout=self._timeout,
                    context=self._ssl_context)
            else:
                conn = HTTPSConnection(
                    *self._http_proxy[1],
                    timeout=self._timeout,
                    context=self._ssl_context)
                conn.set_tunnel(
                    *addr,
                    headers={"Proxy-Authorization": self._http_proxy[0]})
            self._conn_map[addr] = conn
        
        conn.putrequest(
            method=method,
            url=p_url.path + (f"?{p_url.query}" if p_url.query else ""),
            skip_host=True,
            skip_accept_encoding=True)

        headers = self._agent.format_headers(
            url=url,
            body=body,
            headers=headers,
            origin_url=origin_url,
            sec_site=sec_site,
            sec_mode=sec_mode,
            sec_dest=sec_dest)

        for name, value in headers.items():
            conn.putheader(name, value)
        conn.endheaders(body)

        resp = conn.getresponse()
        data = resp.read()

        if (encoding := resp.headers.get("content-encoding")):
            if encoding == "gzip":
                data = zlib.decompress(data, 16 + zlib.MAX_WBITS)

        if resp.status > 403:
            raise RequestRejected(
                f"Unrecognized status code: {resp.status}: {resp.reason}")

        if resp.headers["content-type"].startswith("application/json"):
            data = json.loads(data)
            if "c" in data:
                self._spec = data["c"]
            
        return data