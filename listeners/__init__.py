from .msg_listener import _register_msg_listiner
from valor import Valor

async def register_all(valor: Valor):
    await _register_msg_listiner(valor)