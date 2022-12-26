# Andrew's Discord color utils https://gist.github.com/classAndrew/2f151a12c49a9e4a105fd1dfa338daba 
# See https://gist.github.com/kkrypt0nn/a02506f3712ff2d1c8ca7c9e0aed7c06 for details

'''
example:
from discord_ansicolor import green bold, bg_light_gray
colored = green(bold(bg_light_gray("hello!")))
'''

from typing import Union, Callable
class ColorText:
    def __init__(self, txt="", fmt=None, color=None, bg=None):
        if isinstance(txt, ColorText):
            self.txt = txt.txt
            self.fmt = fmt if fmt else txt.fmt
            self.color = color if color else txt.color
            self.bg = bg if bg else txt.bg
        else:
            self.fmt = fmt if fmt else 0
            self.color = color if color else 30
            self.bg = bg if bg else None
            self.txt = txt
    def __str__(self):
        return f'\u001b[{self.fmt};{self.color}{";"+str(self.bg) if self.bg else ""}m{self.txt}'
    def __repr__(self):
        return self.__str__()
    
formats = {"normal": 0, "bold": 1, "underline": 4}
colors = {"gray": 30, "red": 31, "green": 32, "yellow": 33, "blue": 34,
    "pink": 35, "cyan": 36, "white": 37}
backgrounds = {"bg_firefly_dark_blue": 40, "bg_orange": 41, "bg_marble_blue": 42, "bg_grayish_turquoise": 43,
    "bg_gray": 44, "bg_indigo": 45, "bg_light_gray": 46, "bg_white": 47}

normal: Callable[[Union[ColorText, str]], ColorText] = lambda text: ColorText(text, fmt=formats["normal"])
bold: Callable[[Union[ColorText, str]], ColorText] = lambda text: ColorText(text, fmt=formats["bold"])
underline: Callable[[Union[ColorText, str]], ColorText] = lambda text: ColorText(text, fmt=formats["underline"])
gray: Callable[[Union[ColorText, str]], ColorText] = lambda text: ColorText(text, color=colors["gray"])
red: Callable[[Union[ColorText, str]], ColorText] = lambda text: ColorText(text, color=colors["red"])
green: Callable[[Union[ColorText, str]], ColorText] = lambda text: ColorText(text, color=colors["green"])
yellow: Callable[[Union[ColorText, str]], ColorText] = lambda text: ColorText(text, color=colors["yellow"])
blue: Callable[[Union[ColorText, str]], ColorText] = lambda text: ColorText(text, color=colors["blue"])
pink: Callable[[Union[ColorText, str]], ColorText] = lambda text: ColorText(text, color=colors["pink"])
cyan: Callable[[Union[ColorText, str]], ColorText] = lambda text: ColorText(text, color=colors["cyan"])
white: Callable[[Union[ColorText, str]], ColorText] = lambda text: ColorText(text, color=colors["white"])
bg_firefly_dark_blue: Callable[[Union[ColorText, str]], ColorText] = lambda text: ColorText(text, bg=backgrounds["bg_firefly_dark_blue"])
bg_orange: Callable[[Union[ColorText, str]], ColorText] = lambda text: ColorText(text, bg=backgrounds["bg_orange"])
bg_marble_blue: Callable[[Union[ColorText, str]], ColorText] = lambda text: ColorText(text, bg=backgrounds["bg_marble_blue"])
bg_grayish_turquoise: Callable[[Union[ColorText, str]], ColorText] = lambda text: ColorText(text, bg=backgrounds["bg_grayish_turquoise"])
bg_gray: Callable[[Union[ColorText, str]], ColorText] = lambda text: ColorText(text, bg=backgrounds["bg_gray"])
bg_indigo: Callable[[Union[ColorText, str]], ColorText] = lambda text: ColorText(text, bg=backgrounds["bg_indigo"])
bg_light_gray: Callable[[Union[ColorText, str]], ColorText] = lambda text: ColorText(text, bg=backgrounds["bg_light_gray"])
bg_white: Callable[[Union[ColorText, str]], ColorText] = lambda text: ColorText(text, bg=backgrounds["bg_white"])