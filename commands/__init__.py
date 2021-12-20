from .online import _register_online
from .test import _register_test
from .help import _register_help
from .showbuild import _register_showbuild
from .preferences import _register_preferences
from .gxp import _register_gxp
from .plot import _register_plot
from .activity import _register_activity
from .profile import _register_profile
from .coin import _register_coin
from .ticket import _register_ticket
from .pm import _register_pm
from .join import _register_join
from .plot2 import _register_plot2
from .avg import _register_avg
from .link import _register_link
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
    await _register_gxp(valor)
    await _register_plot(valor)
    await _register_activity(valor)
    await _register_profile(valor)
    await _register_coin(valor)
    await _register_ticket(valor)
    await _register_pm(valor)
    await _register_join(valor)
    await _register_plot2(valor)
    await _register_avg(valor)
    await _register_link(valor)