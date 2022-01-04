from .terr_track import _register_terr_track
from .join_leave import _register_join_leave
from valor import Valor

async def register_all(valor: Valor):
    # await _register_terr_track(valor)
    await _register_join_leave(valor)