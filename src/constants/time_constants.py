# -*- coding: UTF-8 -*-
"""
@Description : 
@Author      : Jason_Sam
@Time        : 2021/6/29 13:31

"""
from src.service.config.apollo_client import ApolloClient

apollo_client = ApolloClient()

DATE_FORMAT_TRADE_DATE = "%Y%m%d"

ONE_DAY_SECONDS = 60*60*24

NATURE_YEAR_DAYS = 365

class NaturalPeriodConstants(object):
    WEEK = 'NATURAL_WEEK'
    MONTH = 'NATURAL_MONTH'

class TradeDatePeriodConstants(object):
    WEEK = 5
    MONTH = 20
    QUARTER = MONTH * 3
    HALF_YEAR = MONTH * 6
    YEAR = 252

class WindPeriodPerformance:
    WEEK = 'F_AVGRETURN_WEEK'