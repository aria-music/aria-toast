import asyncio
import glob
from logging import getLogger
from os import remove

import aiofiles
import aiohttp
from win10toast import ToastNotifier

from aria.Config import Config
from PIL import Image

log = getLogger('__name__')

class Aria():
    def __init__(self, config):
        self.config = config
        self.endpoint = self.config.aria_endpoint
        self.headers =  {'Authorization': f'Bearer {config.aria_token}'}
        self.loop = asyncio.get_event_loop()
        self.session = None
        self.client = None
        self.toaster = ToastNotifier()
        
        self.loop.run_until_complete(self.setup())

    async def setup(self):
        self.session = aiohttp.ClientSession()

    def close(self):
        if self.client:
            self.loop.run_until_complete(self.client.close())
        if not self.session.closed:
            self.session.close()
        self.loop.run_until_complete(self.loop.shutdown_asyncgens())
        self.loop.close()

    def run(self):
        self.loop.create_task(self.receive_message())
        self.loop.run_forever()

    async def receive_message(self):
        self.client = await self.session.ws_connect(self.endpoint, headers=self.headers)
        async for msg in self.client:
            try:
                res = msg.json()
                log.debug(f'{res=}')
            except:
                log.error(f'Failed to parse: {msg.data}')
                continue

            await self.parse_message(res)

    async def parse_message(self, res):
        if res['type'].startswith('event_player_state_change'):
            await self.create_toast(res['data'])

    async def create_toast(self, data):
        log.info(f'{data=}')

        if data['state'].startswith('stopped'):
            return

        title = '▶️ ' if data['state'].startswith('playing') else '⏸️ '
        data = data['entry']
        
        if data.get('entry'):
            title += data['entry']['title']
            message = f'{data["entry"]["artist"]}\t{data["entry"]["album"]}'
        else:
            title += data['title']
            message = data['source']
        
        log.info(f'{title=}')
        log.info(f'{message=}')

        song_uri = data['uri'].replace(':', '-').replace('/', '-').replace('?', '-')
        icon_url = data['thumbnail_small']
        icon_path = fr'data\{song_uri}.img.ico' if icon_url else r'data\aria.ico'

        if not glob.glob(fr'{song_uri}.img.ico') and icon_url:
            if await self.get_thumbnail(song_uri, icon_url):
                self.gen_icon(fr'data\{song_uri}.img')
                remove(fr'data/{song_uri}.img')
            else:
                icon_path = r'data\aria.ico' # default icon

        self.toaster.show_toast(title=title, msg=message, icon_path=icon_path, threaded=True)

    async def get_thumbnail(self, song_uri, image_url):
        async with self.session.get(image_url) as resp:
            if resp.status == 200:
                f = await aiofiles.open(fr'data\{song_uri}.img', mode='wb')
                await f.write(await resp.read())
                await f.close()
                return True
            else:
                return False

    def gen_icon(self, icon_file):
        img = Image.open(icon_file)
        img = self.crop_center(img)
        img.save(fr'{icon_file}.ico')

    def crop_center(self, img):
        img_width, img_height = img.size
        crop_width = crop_height = min(img_width, img_height)
        return img.crop(((img_width - crop_width) // 2,
                            (img_height - crop_height) // 2,
                            (img_width + crop_width) // 2,
                            (img_height + crop_height) // 2))
