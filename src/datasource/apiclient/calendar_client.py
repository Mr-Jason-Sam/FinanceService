# -*- coding: UTF-8 -*-
"""
@Description : 
@Author      : Jason_Sam
@Time        : 2021/11/10 14:32

"""
import json
import pandas as pd

from constants.dto.calendar_dto_const import CalendarDtoConst
from constants.enum.sort_enum import SortEnum
from datasource.apiclient.base_client import BaseClient
from tools import requests_tools


class CalendarClient(BaseClient):

    """
    :@deprecated: 获取交易日历列表数据
    :@param:
    :@return:
    """
    def fetch_calendar_range_date(self, v_begin_date=None, v_end_date=None, v_asc=True):
        url = self.address + '/calendar/queryCalendarRangeDate'

        """
        开始日期为空时 入参为 0 
        结束日期为空时 入参为 99999999
        排序类型为 ASC 或者 DESC
        """
        if v_begin_date is None:
            v_begin_date = '0'
        if v_end_date is None:
            v_end_date = '99999999'
        if v_asc:
            sort_type = SortEnum.ASC
        else:
            sort_type = SortEnum.DESC

        body = \
            {
                "beginDate": v_begin_date,
                "endDate": v_end_date,
                "sort": sort_type
            }

        js = requests_tools.fetch_net_data_with_body_to_js(url=url, body=json.dumps(body))

        origin_df = pd.DataFrame(data=js['body']['calendarInfoList'])

        if origin_df is None:
            return origin_df

        return list(origin_df[CalendarDtoConst.trade_date])


