from .msg_listener import _register_msg_listiner
from .react_listener import _register_react_listener
from valor import Valor

async def register_all(valor: Valor):
    await _register_msg_listiner(valor)
    await _register_react_listener(valor)
    return