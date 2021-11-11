# -*- coding: UTF-8 -*-
"""
@Description : 
@Author      : Jason_Sam
@Time        : 2021/11/3 10:41

"""
import decimal
import json

import pandas as pd

from constants.dto.fund_assets_dto_const import FundAssetsDtoConst
from constants.object.fund_constants import FundConstants
from datasource.apiclient.base_client import BaseClient
from tools import requests_tools


class FundClient(BaseClient):
    """
    :@deprecated: 获取基金净值
    :@param:
    :@return:
    """

    def fetch_fund_nav(self, v_code_list: [], v_end_date: str):
        url = self.address + '/fund/queryFundAdjNav'

        if v_end_date is None:
            v_end_date = '99999999'

        body = \
            {
                "fundCodes": v_code_list,
                "endDate": v_end_date
            }

        js = requests_tools.fetch_net_data_with_body_to_js(url=url, body=json.dumps(body))

        origin_df = pd.DataFrame(data=js['body'])

        if origin_df is None or origin_df.empty:
            return origin_df

        origin_df.rename(
            columns={
                FundAssetsDtoConst.code: FundConstants.fund_windcode,
                FundAssetsDtoConst.date: FundConstants.date,
                FundAssetsDtoConst.adj_nav: FundConstants.adj_nav
            },
            inplace=True
        )

        origin_df[FundConstants.adj_nav] = origin_df[FundConstants.adj_nav].map(lambda x: float(x))

        return origin_df

    """
    :@deprecated: 获取基金区间复权净值
    :@param:
    :@return:
    """

    def fetch_fund_range_nav(self, v_fund_code_list: [], v_begin_date: str, v_end_date: str):
        url = self.address + '/fund/queryHistoryFundAdjNav'

        if v_begin_date is None:
            v_begin_date = '0'
        if v_end_date is None:
            v_end_date = '99999999'

        body = \
            {
                "fundCodes": v_fund_code_list,
                "beginDate": v_begin_date,
                "endDate": v_end_date
            }

        js = requests_tools.fetch_net_data_with_body_to_js(url=url, body=json.dumps(body))

        if len(js['body']) == 0:
            print(js)

        origin_df = pd.DataFrame(data=js['body'][0])

        if origin_df is None or origin_df.empty:
            return origin_df

        origin_df.rename(
            columns={
                FundAssetsDtoConst.code: FundConstants.fund_windcode,
                FundAssetsDtoConst.date: FundConstants.date,
                FundAssetsDtoConst.adj_nav: FundConstants.adj_nav
            },
            inplace=True
        )

        origin_df[FundConstants.adj_nav] = origin_df[FundConstants.adj_nav].map(lambda x: float(x))

        return origin_df

#
# client = FundClient()
# data = client.fetch_fund_range_nav(['110011.OF'], '20211029', '20211109')
