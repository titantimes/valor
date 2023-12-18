import aiohttp

class HTTPHandler:
    def __init__(self) -> None:
        self.session = aiohttp.ClientSession()
    
    async def get_json(self, *args, **kwargs):
        async with self.session.get(*args, **kwargs) as resp:
            return await resp.json()