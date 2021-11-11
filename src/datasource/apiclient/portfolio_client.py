# -*- coding: UTF-8 -*-
"""
@Description : 
@Author      : Jason_Sam
@Time        : 2021/11/2 14:17

"""
import decimal
import json
import pandas as pd
from numpy import number

from constants.dto.portfolio_assets_dto_const import PortfolioAssetsDtoConst
from constants.dto.portfolio_position_dto_const import PortfolioPositionDtoConst
from constants.object.comb_constants import PortfolioConstants
from src.datasource.apiclient.base_client import BaseClient
from src.tools import requests_tools


class PortfolioClient(BaseClient):
    """
    :@deprecated: 查询组合资产数据
    :@param:
    :@return:
    """

    def fetchPortfolioAssetsInfo(self, v_code: str, v_begin_date: str, v_end_date: str):
        url = self.address + '/portfolio/queryPortfolioInfo'

        if v_begin_date is None:
            v_begin_date = '0'
        if v_end_date is None:
            v_end_date = '99999999'

        body = \
            {
                "code": v_code,
                "beginDate": v_begin_date,
                "endDate": v_end_date
            }

        js = requests_tools.fetch_net_data_with_body_to_js(url=url, body=json.dumps(body))

        origin_df = pd.DataFrame(data=js['body']['portfolioInfoList'])

        if origin_df is None or origin_df.empty:
            return origin_df

        origin_df.rename(
            columns={
                PortfolioAssetsDtoConst.date: PortfolioConstants.trade_date,
                PortfolioAssetsDtoConst.nav: PortfolioConstants.assets,
                PortfolioAssetsDtoConst.daily_return: PortfolioConstants.day_return
            },
            inplace=True
        )
        origin_df.set_index(PortfolioConstants.trade_date, inplace=True)
        origin_df[PortfolioConstants.assets] = origin_df[PortfolioConstants.assets].map(lambda x: float(x))
        origin_df[PortfolioConstants.day_return] = origin_df[PortfolioConstants.day_return].map(lambda x: float(x))

        return origin_df

    """
    :@deprecated: 获取组合持仓
    :@param: 
    :@return: 
    """

    def fetchPortfolioPositionInfo(self, v_code: str, v_end_date: str):
        url = self.address + '/portfolio/queryPortfolioHistoryPositionInfo'

        if v_end_date is None:
            v_end_date = '99999999'

        body = \
            {
                "code": v_code,
                "endDate": v_end_date
            }

        js = requests_tools.fetch_net_data_with_body_to_js(url=url, body=json.dumps(body))

        origin_df = pd.DataFrame(data=js['body']['positionInfoList'])

        if origin_df is None or origin_df.empty:
            return origin_df

        origin_df.rename(
            columns={
                PortfolioPositionDtoConst.code: PortfolioConstants.pfl_fund_code,
                PortfolioPositionDtoConst.name: PortfolioConstants.pfl_fund_name,
                PortfolioPositionDtoConst.position: PortfolioConstants.pfl_position,
                PortfolioPositionDtoConst.type: PortfolioConstants.pfl_fund_type,
                PortfolioPositionDtoConst.adj_date: PortfolioConstants.pfl_fund_adj_time
            },
            inplace=True
        )

        origin_df[PortfolioConstants.pfl_position] = origin_df[PortfolioConstants.pfl_position].map(lambda x: float(x))

        return origin_df
