from .online import _register_online
from valor import Valor

async def register_all(valor: Valor):
    """
    Registers all the commands"
    """
    await _register_online(valor)
    
