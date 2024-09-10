import aiohttp

class HTTPHandler:
    async def get_json(self, *args, **kwargs):
        async with aiohttp.ClientSession() as session:
            async with session.get(*args, **kwargs) as resp:
                return await resp.json()
    
    async def get_text(self, *args, **kwargs):
        async with aiohttp.ClientSession() as session:
            async with session.get(*args, **kwargs) as resp:
                return await resp.text()