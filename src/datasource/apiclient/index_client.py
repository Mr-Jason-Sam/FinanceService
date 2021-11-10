# -*- coding: UTF-8 -*-
"""
@Description : 
@Author      : Jason_Sam
@Time        : 2021/11/2 14:18

"""
import decimal
import json

import pandas as pd

from constants.dto.Index_assets_dto_const import IndexAssetsDtoConst
from constants.dto.Index_stk_bond_assets_dto_const import IndexStkBondAssetsDtoConst
from constants.dto.sw_industry_info_dto_const import SwIndustryInfoDtoConst
from constants.object.Index_constants import IndexConstants
from constants.object.a_share_index_constants import AShareIndexConstants
from constants.object.assets_constants import AssetsConstants
from constants.object.sw_constants import SwConstants
from tools import requests_tools

from datasource.apiclient.base_client import BaseClient


class IndexClient(BaseClient):
    """
    :@deprecated: 查询组合资产数据
    :@param:
    :@return:
    """

    def fetchSwIndustryInfo(self, level: str = '3'):
        url = self.address + '/portfolio/querySwIndustryInfo'

        body = \
            {
                "level": level
            }

        js = requests_tools.fetch_net_data_with_body_to_js(url=url, body=json.dumps(body))

        origin_df = pd.DataFrame(data=js['body']['swIndustryInfoList'])

        if origin_df is None:
            return origin_df

        origin_df.rename(
            columns={
                SwIndustryInfoDtoConst.code: SwConstants.code,
                SwIndustryInfoDtoConst.name: SwConstants.name
            },
            inplace=True
        )

        return origin_df

    """
    :@deprecated: 查询指数最近一个资产数据
    :@param:
    :@return:
    """

    def fetchIndexLatestOneAssetsInfo(self, v_index_code: str, v_type: str, v_end_date: str):
        url = self.address + '/index/queryIndexLatestOneAssetsInfo'

        body = \
            {
                "indexCode": v_index_code,
                "type": v_type,
                "endDate": v_end_date
            }

        js = requests_tools.fetch_net_data_with_body_to_js(url=url, body=json.dumps(body))

        origin_df = pd.DataFrame(data=js['body']['indexDataList'])

        if origin_df is None:
            return origin_df

        origin_df.rename(
            columns={
                IndexAssetsDtoConst.code: AShareIndexConstants.code,
                IndexAssetsDtoConst.date: AShareIndexConstants.trade_date,
                IndexAssetsDtoConst.close: AShareIndexConstants.assets
            },
            inplace=True
        )

        origin_df[AssetsConstants.assets] = origin_df[AssetsConstants.assets].map(lambda x: float(x))

        return origin_df

    """
    :@deprecated: 查询指数最近一个资产数据
    :@param:
    :@return:
    """

    def fetchIndexRangeAssetsInfo(self, v_index_code: str, v_type: str, v_begin_date: str, v_end_date: str):
        url = self.address + '/index/queryIndexRangeAssetsInfo'

        body = \
            {
                "indexCode": v_index_code,
                "type": v_type,
                "beginDate": v_begin_date,
                "endDate": v_end_date
            }

        js = requests_tools.fetch_net_data_with_body_to_js(url=url, body=json.dumps(body))

        origin_df = pd.DataFrame(data=js['body']['indexDataList'])

        if origin_df is None:
            return origin_df

        origin_df.rename(
            columns={
                IndexAssetsDtoConst.code: AssetsConstants.code,
                IndexAssetsDtoConst.date: AssetsConstants.trade_date,
                IndexAssetsDtoConst.close: AssetsConstants.assets
            },
            inplace=True
        )

        origin_df[AssetsConstants.assets] = origin_df[AssetsConstants.assets].map(lambda x: float(x))

        return origin_df

    """
    :@deprecated: 获取股债指数数据
    :@param:
    :@return:
    """

    def fetchStkBondIndexAssetsInfo(self, v_stk_code: str, v_bond_code: str, v_begin_date: str, v_end_date: str):
        url = self.address + '/index/queryStkBondIndexAssetsInfo'

        body = \
            {
                "stkCode": v_stk_code,
                "bondCode": v_bond_code,
                "beginDate": v_begin_date,
                "endDate": v_end_date
            }

        js = requests_tools.fetch_net_data_with_body_to_js(url=url, body=json.dumps(body))

        origin_df = pd.DataFrame(data=js['body']['indexDataList'])

        if origin_df is None:
            return origin_df

        origin_df.rename(
            columns={
                IndexStkBondAssetsDtoConst.stk_close: IndexConstants.equity_nav,
                IndexStkBondAssetsDtoConst.bond_close: IndexConstants.bond_nav,
                IndexStkBondAssetsDtoConst.date: IndexConstants.trade_date
            },
            inplace=True
        )

        origin_df[IndexConstants.equity_nav] = origin_df[IndexConstants.equity_nav].map(lambda x: float(x))
        origin_df[IndexConstants.bond_nav] = origin_df[IndexConstants.bond_nav].map(lambda x: float(x))

        return origin_df
