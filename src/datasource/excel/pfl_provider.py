# -*- coding: UTF-8 -*-
"""
@Description : 组合提供者
@Author      : Jason_Sam
@Time        : 2021/6/23 9:33

"""

import numpy as np
import pandas as pd

from constants import io_constants, time_constants
from constants.enum.index_enum import IndexEnum
from constants.object.assets_constants import AssetsConstants
from constants.object.comb_constants import PortfolioConstants
from constants.object.fund_constants import FundConstants
from datasource.apiclient.fund_client import FundClient
from datasource.apiclient.index_client import IndexClient

"""
:@deprecated: 
:@param: 
:@return: 
"""


def read_pfl_data(read_path: str):
    # read_data_df = pd.read_excel('C:\\Users\\shenxiaojian\\Desktop\\运营\\组合\\创金小确幸.xlsx', engine=constants.EXCEL_ENGINE)
    read_data_df = pd.read_excel(read_path, engine=io_constants.EXCEL_ENGINE)
    read_data_df[PortfolioConstants.pfl_fund_adj_time] = read_data_df[PortfolioConstants.pfl_fund_adj_time].map(
        lambda x: x.strftime(time_constants.DATE_FORMAT_TRADE_DATE))
    read_data_df[PortfolioConstants.pfl_fund_code] = read_data_df[PortfolioConstants.pfl_fund_code].map(
        lambda x: '{:0>6d}'.format(x))
    read_data_df.sort_values(by=[PortfolioConstants.pfl_fund_code], inplace=True)
    return read_data_df


"""
:@deprecated: 组合净值根据日净值变化、日收益率
:@param: 
:@return: 
"""


def assemble_pfl_assets(period_with_nav_dict):
    pfl_nav_df = pd.DataFrame()

    init_assets = 1
    setup_date = list(period_with_nav_dict.keys())[0]
    for adj_date, adj_df in period_with_nav_dict.items():
        adj_df[PortfolioConstants.assets] = adj_df[PortfolioConstants.pfl_position] * init_assets
        pfl_df = pd.DataFrame(adj_df.groupby([FundConstants.date])[PortfolioConstants.assets].sum())
        if adj_date == setup_date:
            pfl_nav_df = pfl_nav_df.append(pfl_df)
        else:
            pfl_nav_df = pfl_nav_df.append(pfl_df.iloc[1:])
        init_assets = np.array(pfl_df[PortfolioConstants.assets])[-1]

    pfl_nav_df[PortfolioConstants.day_return] = pfl_nav_df[PortfolioConstants.assets] / pfl_nav_df[
        PortfolioConstants.assets].shift(axis=0,
                                         periods=1) - 1

    pfl_nav_df.fillna({PortfolioConstants.day_return: 0}, inplace=True)

    pfl_nav_df[AssetsConstants.trade_date] = pfl_nav_df.index

    pfl_nav_df.reset_index(inplace=True)

    pfl_nav_df.rename(columns={PortfolioConstants.assets: AssetsConstants.assets,
                               PortfolioConstants.day_return: AssetsConstants.day_return}, inplace=True)

    return pfl_nav_df


class PflExcelProvider:

    def __init__(self, excel_path, begin_date, end_date):
        self.__excel_path = excel_path
        self.__begin_date = begin_date
        self.__end_date = end_date

        self.__index_client = IndexClient()
        self.__fund_client = FundClient()
        """
        1、读取数据【基金代码、仓位、日期、类型等】
        2、获取持仓范围内的基金净值、持仓期间净值变化
        3、组合净值根据净值变化生成。
        """
        self.__read_data_df = read_pfl_data(self.__excel_path)
        self.__period_with_nav_dict = self.assemble_adj_trade_data(self.__read_data_df)
        self.__pfl_df = assemble_pfl_assets(self.__period_with_nav_dict)

    """
    :@deprecated: 生成组合净值
    :@param:
    :@return:
    """

    def gen_nav(self):
        if self.__end_date is not None and self.__begin_date is not None:
            return self.__pfl_df[(self.__begin_date <= self.__pfl_df[AssetsConstants.trade_date]) &
                                 (self.__pfl_df[AssetsConstants.trade_date] <= self.__end_date)]
        elif self.__end_date is None and self.__begin_date is not None:
            return self.__pfl_df[(self.__begin_date <= self.__pfl_df[AssetsConstants.trade_date])]
        return self.__pfl_df

    """
    :@deprecated: 生成调仓信息
    :@param: 
    :@return: 
    """

    def gen_adj_position_info(self):
        position_df = self.__read_data_df[[PortfolioConstants.pfl_fund_code,
                                           PortfolioConstants.pfl_fund_name,
                                           PortfolioConstants.pfl_position,
                                           PortfolioConstants.pfl_fund_type,
                                           PortfolioConstants.pfl_fund_adj_time]]

        if self.__end_date is not None and self.__begin_date is not None:
            return position_df[(self.__begin_date <= self.__read_data_df[PortfolioConstants.pfl_fund_adj_time]) &
                               (self.__read_data_df[PortfolioConstants.pfl_fund_adj_time] <= self.__end_date)]
        elif self.__end_date is None and self.__begin_date is not None:
            return position_df[(self.__begin_date <= self.__read_data_df[PortfolioConstants.pfl_fund_adj_time])]

        return position_df

    """
    :@deprecated: 生成业绩基准净值
    :@param: 
    :@return: 
    """

    def gen_bm_nav(self, index_code: str, bond_index_code: str):
        ccy_index_df = self.__index_client.fetchIndexRangeAssetsInfo(v_index_code=index_code,
                                                                     v_type=IndexEnum.FUND_INDEX,
                                                                     v_begin_date=self.__begin_date,
                                                                     v_end_date=self.__end_date)
        bond_index_df = self.__index_client.fetchIndexRangeAssetsInfo(v_index_code=bond_index_code,
                                                                      v_type=IndexEnum.BOND_INDEX,
                                                                      v_begin_date=self.__begin_date,
                                                                      v_end_date=self.__end_date)

        ccy_tag = '_ccy'
        bond_tag = '_bond'

        index_pfl_df = pd.merge(left=ccy_index_df,
                                right=bond_index_df,
                                on=[AssetsConstants.trade_date],
                                sort=True,
                                suffixes=(ccy_tag, bond_tag))

        ccy_ratio = 0.7
        bond_ratio = 1 - ccy_ratio
        index_pfl_df[AssetsConstants.assets] = \
            index_pfl_df[AssetsConstants.assets + ccy_tag] / index_pfl_df.loc[0, AssetsConstants.assets + ccy_tag] * ccy_ratio +\
            index_pfl_df[AssetsConstants.assets + bond_tag] / index_pfl_df.loc[0, AssetsConstants.assets + bond_tag] * bond_ratio

        index_pfl_df[AssetsConstants.day_return] = index_pfl_df[AssetsConstants.assets] / index_pfl_df[
            AssetsConstants.assets].shift(axis=0, periods=1) - 1

        index_pfl_df.fillna({AssetsConstants.day_return: 0}, inplace=True)

        index_pfl_res_df = index_pfl_df[
            [AssetsConstants.trade_date, AssetsConstants.assets, AssetsConstants.day_return]]

        return index_pfl_res_df

    """
    :@deprecated: 生成组合数据带基准
    :@param: 
    :@return: 
    """

    def gen_nav_with_bm(self, index_code: str, bond_index_code: str):
        pfl_df = self.gen_nav()
        bm_df = self.gen_bm_nav(index_code, bond_index_code)

        # print(len(pfl_df))
        # print(len(bm_df))

        bm_df.rename(columns={AssetsConstants.assets: AssetsConstants.bench_mark_assets,
                              AssetsConstants.day_return: AssetsConstants.bench_mark_day_return}, inplace=True)

        pfl_with_bm_df = pd.merge(left=pfl_df,
                                  right=bm_df,
                                  on=[AssetsConstants.trade_date],
                                  sort=True)

        pfl_with_bm_df.index = np.array(pfl_with_bm_df[AssetsConstants.trade_date])
        pfl_with_bm_df = pfl_with_bm_df[[AssetsConstants.assets,
                                         AssetsConstants.day_return,
                                         AssetsConstants.bench_mark_assets,
                                         AssetsConstants.bench_mark_day_return]]

        return pfl_with_bm_df

    """
    :@deprecated: 补充每期调仓后的净值、持仓期间净值变化
    :@param: 
    :@return: 
    """

    def assemble_adj_trade_data(self, origin_data_df: pd.DataFrame):
        period_with_nav_dict = {}
        data_date_group = origin_data_df.groupby([PortfolioConstants.pfl_fund_adj_time])

        adj_date_array = list(data_date_group.groups.keys())
        adj_date_array.sort()

        for date, groups in data_date_group:
            now_date = str(date)
            now_index = adj_date_array.index(now_date)

            if now_index >= len(adj_date_array) - 1:
                next_date = None
            else:
                next_date = adj_date_array[now_index + 1]

            adj_df = pd.DataFrame(data=groups)
            fund_code_list = list(adj_df[PortfolioConstants.pfl_fund_code])

            nav_df = self.__fund_client.fetch_fund_range_nav(v_fund_code_list=fund_code_list,
                                                             v_begin_date=now_date,
                                                             v_end_date=next_date)

            nav_df[FundConstants.fund_code] = nav_df[FundConstants.fund_windcode].map(lambda x: x[:-3])
            nav_df.sort_values(by=[FundConstants.date, FundConstants.fund_windcode], ascending=[1, 1],
                               inplace=True)

            nav_trade_groups = nav_df.groupby(FundConstants.fund_code)
            for fund_code, fund_groups in nav_trade_groups:
                fund_df = pd.DataFrame(data=fund_groups)
                setup_nav = np.array(fund_df[FundConstants.adj_nav])[0]
                fund_df[FundConstants.change] = fund_df[FundConstants.adj_nav] / setup_nav
                nav_df.loc[fund_df.index, FundConstants.change] = fund_df.loc[fund_df.index, FundConstants.change]
                # 仓位变化情况
                init_position = np.array(
                    adj_df.loc[adj_df[PortfolioConstants.pfl_fund_code] == fund_code, PortfolioConstants.pfl_position])[
                    0]
                nav_df.loc[fund_df.index, PortfolioConstants.pfl_position] = nav_df.loc[
                                                                                 fund_df.index, FundConstants.change] * init_position

            period_with_nav_dict[date] = nav_df

        return period_with_nav_dict
