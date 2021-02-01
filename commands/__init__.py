from .online import _register_online
from .test import _register_test
from .help import _register_help
from .showbuild import _register_showbuild
from .preferences import _register_preferences
from valor import Valor

async def register_all(valor: Valor):
    """
    Registers all the commands"
    """
    await _register_help(valor)
    await _register_online(valor)
    await _register_test(valor)
    await _register_showbuild(valor)
    await _register_preferences(valor)