from .terr_track import _register_terr_track
from valor import Valor

async def register_all(valor: Valor):
    await _register_terr_track(valor)