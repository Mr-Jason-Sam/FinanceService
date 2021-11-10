import time

from constants import time_constants
from datasource.apiclient.calendar_client import CalendarClient


def find_trade_date(date, days, asc=False):
    calendar_client = CalendarClient()
    if days < 0:
        trade_date_list = calendar_client.fetch_calendar_range_date(v_end_date=date, v_asc=False)
        days = -days
    elif days > 0:
        trade_date_list = calendar_client.fetch_calendar_range_date(v_begin_date=date)
    else:
        if not asc:
            trade_date_list = calendar_client.fetch_calendar_range_date(v_end_date=date, v_asc=asc)
        else:
            trade_date_list = calendar_client.fetch_calendar_range_date(v_begin_date=date, v_asc=asc)
    if not trade_date_list:
        raise Exception('无法获取到交易日历信息')

    if days >= len(trade_date_list):
        raise Exception('超过交易日历范围')

    return trade_date_list[days]


def now_yymmdd():
    return time.strftime(time_constants.DATE_FORMAT_TRADE_DATE, time.localtime(time.time()))
