# -*- coding: UTF-8 -*-
"""
@Description : 
@Author      : Jason_Sam
@Time        : 2021/11/1 15:32

"""

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        pass

    try:
        import unicodedata
        unicodedata.numeric(s)
        return True
    except (TypeError, ValueError):
        pass

    return False


def keep_decimal(num: float, keep: int):
    try:
        return int(num * (10 ** keep)) / (10 ** keep)
    except ValueError:
        return 0

def format_percentage(num: float, show_symbol=False):
    if num > 0 and show_symbol:
        return '+{:3.2f}%'.format(num * 100)
    else:
        return '{:3.2f}%'.format(num * 100)