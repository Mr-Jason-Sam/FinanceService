"""
@Description : 报告
@Author      : Jason_Sam
@Time        : 2021/3/1 11:09

"""
import datetime
import textwrap
from decimal import Decimal, ROUND_UP, ROUND_FLOOR

import matplotlib.patheffects as path_effects
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
from matplotlib import ticker

from constants import time_constants
from constants.enum.index_enum import IndexEnum
from constants.object.index_wind_code_constants import IndexWindCodeConstants
from datasource.apiclient.fund_client import FundClient
from datasource.apiclient.index_client import IndexClient
from datasource.apiclient.portfolio_client import PortfolioClient
from src.constants import io_constants
from src.constants.object import portfolio_constants
from src.constants.object.Index_constants import IndexConstants
from src.constants.object.a_share_index_constants import AShareIndexConstants
from src.constants.object.assets_constants import AssetsConstants
from src.constants.object.comb_constants import PortfolioConstants
from src.constants.object.fund_constants import FundConstants
from src.constants.object.indicator_constants import IndicatorConstants
from src.constants.object.newspaper_constants import NewspaperConstants
from src.constants.object.portfolio_constants import PFL_DICT
from src.constants.object.sw_constants import SwConstants
from src.constants.time_constants import TradeDatePeriodConstants
from src.datasource.excel.pfl_provider import PflExcelProvider
from src.pojo.business.newspaper_info import NewspaperInfo
from src.pojo.dto.com_dto import CombDto
from src.service.module.indicator import Indicator
from src.tools import number_tools, time_tools
from src.tools.style_tools import render_mpl_table


def scale(img, width=None, height=None):
    if not width and not height:
        width, height = img.size  # 原图片宽高
    if not width or not height:
        _width, _height = img.size
        height = width * _height / _width if width else height
        width = height * _width / _height if height else width
    return int(width), int(height)


"""
:@deprecated: 组合报告通用信息
:@param: 
:@return: 
"""


def assemble_newspaper_info(v_comb_dto: CombDto):
    newspaper_info = NewspaperInfo()
    newspaper_info.code = v_comb_dto.code
    newspaper_info.name = PFL_DICT.get(v_comb_dto.dict_id).get(NewspaperConstants.name)
    newspaper_info.title = PFL_DICT.get(v_comb_dto.dict_id).get(NewspaperConstants.name) + '周报'
    newspaper_info.title_label = '——' + PFL_DICT.get(v_comb_dto.dict_id).get(NewspaperConstants.title_label)
    return newspaper_info


class Newspaper(object):

    def __init__(self, v_comb_dto: CombDto):
        self.__comb_dto = v_comb_dto
        self.__fund_client = FundClient()
        self.__index_client = IndexClient()
        self.__portfolio_client = PortfolioClient()
        if v_comb_dto.excel_db[v_comb_dto.USE_EXCEL]:
            self.__comb_excel_provider = PflExcelProvider(excel_path=v_comb_dto.excel_db[v_comb_dto.EXCEL_PATH],
                                                          begin_date=v_comb_dto.begin_date,
                                                          end_date=v_comb_dto.end_date)
        self.__comb_info = assemble_newspaper_info(v_comb_dto=v_comb_dto)
        self.__assets_df = self.__fetchCombData(v_comb_dto=v_comb_dto)
        self.__indicator_dict = {}
        self.__position_df = self.fetchCombPosition(v_comb_dto=v_comb_dto)
        self.__evaluate = ''

    def assets_to_excel(self):
        self.__assets_df.to_excel('E:\\output\\assets_' + self.__comb_info.code + io_constants.XLSX)

    """
    生成周报
    1、获取组合净值数据（日期、组合净值、业绩比较基准净值）
    2、计算组合指标（区间收益率【一周、三个月、成立以来】、最大回撤【成立以来】、夏普比率【成立以来】、超额收益率、滚动三个月收益率）
    3、组合持仓（基金代码、简称、类型、权重）
    4、画图（趋势图、饼状图）
    5、评价
    6、优化项（上服务器）
    """

    """
    :@deprecated: 获取组合净值数据（日期、组合净值、业绩比较基准净值）
    :@param: 
    :@return: 
    """

    def __fetchCombData(self, v_comb_dto: CombDto):

        if v_comb_dto.excel_db[v_comb_dto.USE_EXCEL]:
            comb_with_bm_df = self.__comb_excel_provider.gen_nav_with_bm(
                index_code=v_comb_dto.excel_db[v_comb_dto.INDEX_CODE],
                bond_index_code=v_comb_dto.excel_db[v_comb_dto.BOND_INDEX_CODE])

            comb_with_bm_df.to_excel(io_constants.newspaper_output_path + self.__comb_info.name + '资产数据' + io_constants.XLSX)

            return comb_with_bm_df

        comb_assets_df = self.__portfolio_client.fetchPortfolioAssetsInfo(v_code=v_comb_dto.code,
                                                                          v_begin_date=v_comb_dto.begin_date,
                                                                          v_end_date=v_comb_dto.end_date)
        bench_assets_df = self.__index_client.fetchStkBondIndexAssetsInfo(v_stk_code=v_comb_dto.stk_bench_mark_code,
                                                                          v_bond_code=v_comb_dto.bond_bench_mark_code,
                                                                          v_begin_date=v_comb_dto.begin_date,
                                                                          v_end_date=v_comb_dto.end_date)
        # 假设投资资金为1
        assets_init = 1
        comb_assets_df[PortfolioConstants.assets] = assets_init
        if comb_assets_df is None or comb_assets_df.empty:
            raise Exception('无组合数据')
        comb_assets_indexes = comb_assets_df.iloc[1:].index
        before_date = comb_assets_df.index[0]
        for date in comb_assets_indexes:
            comb_assets_df.loc[date, PortfolioConstants.assets] =\
                comb_assets_df.loc[before_date, PortfolioConstants.assets] * (1 + comb_assets_df.loc[date, PortfolioConstants.day_return])
            before_date = date

        # 补充日收益率数据
        bench_assets_df[PortfolioConstants.bench_day_return] = \
            v_comb_dto.bench_equity_position * (bench_assets_df[IndexConstants.equity_nav] / bench_assets_df[IndexConstants.equity_nav].shift(axis=0,
                                                                                                                                              periods=1) - 1) + \
            v_comb_dto.bench_bond_position * (bench_assets_df[IndexConstants.bond_nav] / bench_assets_df[IndexConstants.bond_nav].shift(axis=0,
                                                                                                                                        periods=1) - 1)

        bench_assets_df = bench_assets_df.fillna(value={PortfolioConstants.bench_day_return: 0})

        # 使两个df的index一致
        bench_assets_df.index = comb_assets_df.index

        comb_assets_df[PortfolioConstants.bench_day_return] = bench_assets_df[PortfolioConstants.bench_day_return]

        comb_assets_df[PortfolioConstants.bench_assets] = assets_init
        if comb_assets_df is None or comb_assets_df.empty:
            raise Exception('无基准数据')
        bench_assets_indexes = comb_assets_df.iloc[1:].index
        before_date = comb_assets_df.index[0]
        for date in bench_assets_indexes:
            comb_assets_df.loc[date, PortfolioConstants.bench_assets] = comb_assets_df.loc[
                                                                            before_date, PortfolioConstants.bench_assets] * (
                                                                                1 + comb_assets_df.loc[
                                                                            date, PortfolioConstants.bench_day_return])
            before_date = date

        comb_assets_df.to_excel(io_constants.newspaper_output_path + self.__comb_info.name + '资产数据' + io_constants.XLSX)

        return comb_assets_df

    """
       :@deprecated: 计算组合指标（区间收益率【一周、三个月、成立以来】、最大回撤【成立以来】、夏普比率【成立以来】、超额收益率、滚动三个月收益率）
       :@param: 
       :@return: 
       """

    def indicator_factory(self):
        assets_indicator_dict = self.fetchAssetsIndicator(self.__assets_df)
        # 计算基准的收益率相关数据，只复制NAV和DAY_RETURN数据，所以跟基准相关的指标不可用
        bm_assets_df = self.__assets_df.copy()
        bm_assets_df[AssetsConstants.assets] = bm_assets_df[PortfolioConstants.bench_assets]
        bm_assets_df[AssetsConstants.day_return] = bm_assets_df[AssetsConstants.bench_mark_day_return]
        bm_assets_indicator_dict = self.fetchAssetsIndicator(bm_assets_df)

        indicator_list = [assets_indicator_dict, bm_assets_indicator_dict]

        indicator_df = pd.DataFrame(indicator_list, index=['组合', '基准'])
        indicator_df.to_excel(io_constants.newspaper_output_path + self.__comb_info.name + '指标数据' + io_constants.XLSX)

        self.__indicator_dict = {
            '最近一周': number_tools.format_percentage(number_tools.keep_decimal(assets_indicator_dict['return_1w'], 4),
                                                   show_symbol=True),
            '最近三月': number_tools.format_percentage(number_tools.keep_decimal(assets_indicator_dict['return_3m'], 4),
                                                   show_symbol=True),
            '最近半年': number_tools.format_percentage(number_tools.keep_decimal(assets_indicator_dict['return_6m'], 4),
                                                   show_symbol=True),
            '最近一年': number_tools.format_percentage(number_tools.keep_decimal(assets_indicator_dict['return_1y'], 4),
                                                   show_symbol=True),
            '成立以来': number_tools.format_percentage(number_tools.keep_decimal(assets_indicator_dict['return_since'], 4),
                                                   show_symbol=True),
            '最大回撤': number_tools.format_percentage(number_tools.keep_decimal(assets_indicator_dict['max_dd'], 4)),
            '夏普比率': number_tools.keep_decimal(assets_indicator_dict['sharpe_ratio'], 2)
        }

        # 每日超额收益
        self.__assets_df[AssetsConstants.day_return] = self.__assets_df[AssetsConstants.assets] / self.__assets_df[
            AssetsConstants.assets].shift(axis=0, periods=1) - 1
        self.__assets_df[AssetsConstants.bench_mark_day_return] = self.__assets_df[AssetsConstants.bench_mark_assets] / \
                                                                  self.__assets_df[
                                                                      AssetsConstants.bench_mark_assets].shift(
                                                                      axis=0,
                                                                      periods=1) - 1
        self.__assets_df[IndicatorConstants.alpha] = self.__assets_df[AssetsConstants.assets] - self.__assets_df[
            AssetsConstants.bench_mark_assets]
        self.__assets_df = self.__assets_df.fillna(value={IndicatorConstants.alpha: 0})
        # 滚动收益
        self.__assets_df[IndicatorConstants.return_range] = self.__assets_df[AssetsConstants.assets] / self.__assets_df[
            AssetsConstants.assets].shift(axis=0, periods=self.__comb_dto.roll_trade_day) - 1

        # 组装周观点
        self.__evaluate = self.__assemble_evaluate(self.__comb_dto)

        # 输出周观点
        with open(io_constants.newspaper_output_path + self.__comb_info.name + '周观点' + io_constants.TXT, "w") as f:
            f.write(self.__evaluate)

    """
    :@deprecated: 获取资产指标数据
    :@param: 
    :@return: 
    """

    def fetchAssetsIndicator(self, assets_df):
        indicator = Indicator(assets_df=assets_df, has_bench_info=True)

        # trade_date_idx = self.__assets_df.index[-1].get_loc(self.__trade_date)
        # 区间收益率
        return_1w = Indicator(assets_df=assets_df
                              .iloc[-1 * TradeDatePeriodConstants.WEEK:],
                              ann=False).range_return()
        return_3m = Indicator(assets_df=assets_df
                              .iloc[-1 * TradeDatePeriodConstants.QUARTER:],
                              ann=False).range_return()
        # 区间收益率
        return_6m = Indicator(assets_df=assets_df
                              .iloc[-1 * TradeDatePeriodConstants.HALF_YEAR:],
                              ann=False).range_return()
        # 区间收益率
        return_1y = Indicator(assets_df=assets_df
                              .iloc[-1 * TradeDatePeriodConstants.YEAR:],
                              ann=False).range_return()
        return_since = Indicator(assets_df=assets_df, ann=False).range_return()
        # 最大回撤
        max_dd = indicator.max_dd()
        # 夏普比率
        sharpe_ratio = indicator.sharpe_ratio()

        # 年化收益
        return_since_ann = indicator.range_return()
        roll_vol = indicator.roll_vol()
        ewma_vol = indicator.ewma_vol()
        strling = indicator.strling()
        sortino_ratio = indicator.sortino_ratio()
        calmar_ratio = indicator.calmar_ratio()
        info_ratio = indicator.info_ratio()

        indicator_dict = {
            'return_1w': return_1w,
            'return_3m': return_3m,
            'return_6m': return_6m,
            'return_1y': return_1y,
            'return_since': return_since,
            'return_since_ann': return_since_ann,
            'max_dd': max_dd,
            'sharpe_ratio': sharpe_ratio,
            'roll_vol': roll_vol,
            'ewma_vol': ewma_vol,
            'strling': strling,
            'sortino_ratio': sortino_ratio,
            'calmar_ratio': calmar_ratio,
            'info_ratio': info_ratio
        }

        return indicator_dict

    """
       :@deprecated: 组合持仓（基金代码、简称、类型、权重）
       :@param: 
       :@return: 
       """

    def fetchCombPosition(self, v_comb_dto: CombDto):
        if v_comb_dto.excel_db[v_comb_dto.USE_EXCEL]:
            his_position_df = self.__comb_excel_provider.gen_adj_position_info()
            position_df = his_position_df[
                his_position_df[PortfolioConstants.pfl_fund_adj_time] == his_position_df[
                    PortfolioConstants.pfl_fund_adj_time].max()]
        else:
            his_position_df = self.__portfolio_client.fetchPortfolioPositionInfo(v_code=self.__comb_info.code,
                                                                                 v_end_date=self.__comb_dto.end_date)
            # 删除持仓为0%的基金
            his_position_df = his_position_df[~his_position_df[PortfolioConstants.pfl_position].isin([0])]
            position_df = his_position_df[his_position_df[PortfolioConstants.pfl_fund_adj_time] == his_position_df[
                PortfolioConstants.pfl_fund_adj_time].max()]
        position_df[PortfolioConstants.pfl_fund_name] = position_df[PortfolioConstants.pfl_fund_name].map(
            lambda x: x[:-1] if x[-1] in ['A', 'C'] else x)
        # 输出历史调仓
        his_position_df.to_excel(
            io_constants.newspaper_output_path + self.__comb_info.name + '历史持仓' + io_constants.XLSX)
        position_df.to_excel(io_constants.newspaper_output_path + self.__comb_info.name + '最新持仓' + io_constants.XLSX)
        return position_df

    """
    :@deprecated: 组装评论数据
    例：
    【{name}】上周收益为【{return}】，符合预期。成分基金中，周收益居前的是【{top_1_name}】基金收益为【{top_1_return}】与【{top_2_name}】基金收益为【top_2_return】。
    上周A股指数数据，【{sh_index}】{sh_index_desc}、【{sz_index}】{sz_index_desc}、【{business_index}】{business_index_desc}。
    行业层面，【{industry_1}】{industry_1_desc}、【{industry_2}】{industry_2_desc}、【{industry_3}】{industry_3_desc}。
    + 观点
    1、组合名称及其收益率
    :@param: 
    :@return: 
    """

    def __assemble_evaluate(self, v_comb_dto: CombDto):

        if not v_comb_dto.quote_evaluate:
            return v_comb_dto.evaluate

        tmp_end_date = v_comb_dto.end_date if v_comb_dto.end_date is not None else str(
            datetime.datetime.now().strftime(time_constants.DATE_FORMAT_TRADE_DATE))
        comb_name = PFL_DICT.get(v_comb_dto.dict_id).get(NewspaperConstants.name)
        before_week_date = time_tools.find_trade_date(date=tmp_end_date, days=-1 * TradeDatePeriodConstants.WEEK)

        portfolio_evaluate = self.__assemble_portfolio_info(comb_name, tmp_end_date)
        a_share_index_evaluate = self.__assemble_a_share_index(tmp_end_date, before_week_date)
        industry_evaluate = self.__assemble_industry(tmp_end_date, before_week_date)

        quote_evaluate = portfolio_evaluate + a_share_index_evaluate + industry_evaluate

        return quote_evaluate + v_comb_dto.evaluate

    """
    :@deprecated: 组合数据
    :@param: 
    :@return: 
    """

    def __assemble_portfolio_info(self, v_comb_name, v_end_date: str):
        range_return = self.__indicator_dict['最近一周']
        begin_date = time_tools.find_trade_date(date=v_end_date, days=-1 * TradeDatePeriodConstants.WEEK)

        return_df = pd.DataFrame()
        for code in self.__position_df[PortfolioConstants.pfl_fund_code]:
            wind_code = code + '.OF'
            begin_nav_df = self.__fund_client.fetch_fund_nav(v_code_list=[wind_code], v_end_date=begin_date)
            if begin_nav_df is None or begin_nav_df.empty:
                continue
            end_nav_df = self.__fund_client.fetch_fund_nav(v_code_list=[wind_code], v_end_date=v_end_date)
            if end_nav_df is None or end_nav_df.empty:
                continue
            week_return = end_nav_df[FundConstants.adj_nav][0] / begin_nav_df[FundConstants.adj_nav][0] - 1
            return_df = return_df.append(pd.DataFrame(data=[{
                FundConstants.date: v_end_date,
                FundConstants.fund_windcode: wind_code,
                FundConstants.fund_code: code,
                FundConstants.week_return: week_return
            }]))

        return_df.rename(columns={FundConstants.fund_code: PortfolioConstants.pfl_fund_code}, inplace=True)

        return_df = pd.merge(left=return_df,
                             right=self.__position_df,
                             how='left',
                             on=[PortfolioConstants.pfl_fund_code])

        # 取收益率前2数据
        return_df.sort_values(by=[FundConstants.week_return], ascending=False, inplace=True)
        return_df.reset_index(inplace=True)

        # 保留两位小数，添加百分号
        return_df[FundConstants.week_return] = return_df[FundConstants.week_return].map(lambda x: '%.2f%%' % (x * 100))

        portfolio_evaluate = portfolio_constants.PFL_EXAMPLE.format(name=v_comb_name,
                                                                    range_return=range_return,
                                                                    top_1_name=return_df.loc[
                                                                        0, PortfolioConstants.pfl_fund_name],
                                                                    top_1_return=return_df.loc[
                                                                        0, FundConstants.week_return],
                                                                    top_2_name=return_df.loc[
                                                                        1, PortfolioConstants.pfl_fund_name],
                                                                    top_2_return=return_df.loc[
                                                                        1, FundConstants.week_return])
        return portfolio_evaluate

    """
    :@deprecated: A股指数数据
    :@param: 
    :@return: 
    """

    def __assemble_a_share_index(self, v_end_date: str, before_week_date: str):

        a_share_index_df = pd.DataFrame()

        DESC = 'desc'

        for code in portfolio_constants.INDEX_DICT.keys():
            end_date_df = self.__index_client.fetchIndexLatestOneAssetsInfo(v_index_code=code,
                                                                            v_type=IndexEnum.CE_INDEX,
                                                                            v_end_date=v_end_date)
            before_week_df = self.__index_client.fetchIndexLatestOneAssetsInfo(v_index_code=code,
                                                                               v_type=IndexEnum.CE_INDEX,
                                                                               v_end_date=before_week_date)
            end_date_df[AShareIndexConstants.week_return] = end_date_df[AShareIndexConstants.assets] / before_week_df[
                AShareIndexConstants.assets] - 1
            end_date_df[AShareIndexConstants.name] = end_date_df[AShareIndexConstants.code].map(
                portfolio_constants.INDEX_DICT)
            a_share_index_df = a_share_index_df.append(end_date_df)

        a_share_index_df[DESC] = '涨跌幅为' + a_share_index_df[AShareIndexConstants.week_return].map(
            lambda x: '【' + ('%.2f%%' % (x * 100)) + '】')

        a_share_index_df.reset_index(inplace=True)

        a_share_index_evaluate = portfolio_constants.INDEX_EXAMPLE.format(
            sh_index=a_share_index_df.loc[0, AShareIndexConstants.name],
            sh_index_desc=a_share_index_df.loc[0, DESC],
            sz_index=a_share_index_df.loc[1, AShareIndexConstants.name],
            sz_index_desc=a_share_index_df.loc[1, DESC],
            business_index=a_share_index_df.loc[2, AShareIndexConstants.name],
            business_index_desc=a_share_index_df.loc[2, DESC]
        )

        return a_share_index_evaluate

    """
    :@deprecated: 行业数据
    :@param: 
    :@return: 
    """

    def __assemble_industry(self, v_end_date: str, before_week_date: str):
        sw_info_df = self.__index_client.fetchSwIndustryInfo()

        sw_index_df = pd.DataFrame()

        DESC = 'desc'

        for index in sw_info_df.index:
            code = sw_info_df.loc[index, SwConstants.code]
            end_date_df = self.__index_client.fetchIndexLatestOneAssetsInfo(v_index_code=code,
                                                                            v_type=IndexEnum.SW_INDEX,
                                                                            v_end_date=v_end_date)
            before_week_date_df = self.__index_client.fetchIndexLatestOneAssetsInfo(v_index_code=code,
                                                                                    v_type=IndexEnum.SW_INDEX,
                                                                                    v_end_date=before_week_date)
            end_date_df[SwConstants.week_return] = end_date_df[SwConstants.assets] / before_week_date_df[
                SwConstants.assets] - 1
            sw_index_df = sw_index_df.append(end_date_df)

        sw_index_df[DESC] = '涨跌幅为' + sw_index_df[SwConstants.week_return].map(
            lambda x: '【' + ('%.2f%%' % (x * 100)) + '】')

        sw_index_df = pd.merge(left=sw_index_df,
                               right=sw_info_df,
                               how='left',
                               on=[SwConstants.code])
        sw_index_df.sort_values(by=[SwConstants.week_return], ascending=[False], inplace=True)
        sw_index_df.reset_index(inplace=True)

        industry_evaluate = portfolio_constants.INDUSTRY_EXAMPLE.format(
            industry_1=sw_index_df.loc[0, SwConstants.name],
            industry_1_desc=sw_index_df.loc[0, DESC],
            industry_2=sw_index_df.loc[1, SwConstants.name],
            industry_2_desc=sw_index_df.loc[1, DESC],
            industry_3=sw_index_df.loc[2, SwConstants.name],
            industry_3_desc=sw_index_df.loc[2, DESC]
        )

        return industry_evaluate

    """
       :@deprecated: 画图（折线图、饼状图）
       :@param: 
       :@return: 
       """

    def draw(self):
        MAX_FONT_SIZE = 24
        NORMAL_MAX_FONT_SIZE = 20
        TICK_STEP = 7
        plt.rcParams['font.sans-serif'] = 'KaiTi'
        plt.rcParams['axes.unicode_minus'] = False
        # 组合资产与基准比较
        assets_df = self.__assets_df[[AssetsConstants.assets, AssetsConstants.bench_mark_assets]].copy()
        max_assets = max(assets_df[AssetsConstants.assets].max(), assets_df[AssetsConstants.bench_mark_assets].max())
        min_assets = min(assets_df[AssetsConstants.assets].min(), assets_df[AssetsConstants.bench_mark_assets].min())
        assets_df.rename(columns={AssetsConstants.assets: '组合资产'}, inplace=True)
        assets_df.rename(columns={AssetsConstants.bench_mark_assets: '基准资产'}, inplace=True)
        alpha_df = self.__assets_df[[IndicatorConstants.alpha]].copy()
        max_alpha = alpha_df[IndicatorConstants.alpha].max()
        min_alpha = alpha_df[IndicatorConstants.alpha].min()
        alpha_df.rename(columns={IndicatorConstants.alpha: '超额收益'}, inplace=True)
        return_ax = assets_df.plot(kind='line', linewidth=3.0, color=['#FF7F0E', '#1F77B4'])
        alpha_ax = alpha_df.plot(kind='area',
                                 secondary_y=True,
                                 color='#BEBEBE',
                                 ax=return_ax,
                                 stacked=False,
                                 figsize=(14, 8),
                                 legend=False)

        return_ax.set_ylabel('资产', fontsize=MAX_FONT_SIZE)
        return_ax.legend(fontsize=MAX_FONT_SIZE)
        return_ax.tick_params(axis="x", labelsize=MAX_FONT_SIZE)
        return_ax.tick_params(axis="y", labelsize=MAX_FONT_SIZE)
        alpha_ax.set_ylabel('超额收益', fontsize=MAX_FONT_SIZE)
        alpha_ax.tick_params(labelsize=MAX_FONT_SIZE)
        return_step = float(Decimal((max_assets - min_assets) / TICK_STEP).quantize(Decimal('0.00'), rounding=ROUND_UP))
        alpha_step = float(Decimal((max_alpha - min_alpha) / TICK_STEP).quantize(Decimal('0.0000'), rounding=ROUND_UP))
        return_y = []
        alpha_y = []
        return_init_data = 1
        alpha_init_data = 0
        return_min_factor = int(
            Decimal((min_assets - return_init_data) / return_step).quantize(Decimal('0'), rounding=ROUND_FLOOR))
        alpha_min_factor = int(
            Decimal((min_alpha - alpha_init_data) / alpha_step).quantize(Decimal('0'), rounding=ROUND_FLOOR))
        return_max_factor = max(
            int(Decimal((max_assets - return_init_data) / return_step).quantize(Decimal('0'), rounding=ROUND_UP)),
            return_init_data)
        alpha_max_factor = max(
            int(Decimal((max_alpha - alpha_init_data) / alpha_step).quantize(Decimal('0'), rounding=ROUND_UP)),
            alpha_init_data)
        min_factor = min(return_min_factor, alpha_min_factor)
        max_factor = max(return_max_factor, alpha_max_factor)
        for num in range(min_factor, max_factor + 1):
            return_y.append(return_init_data + num * return_step)
            alpha_y.append(alpha_init_data + num * alpha_step)

        return_ax.set_yticks(return_y)
        alpha_ax.set_yticks(alpha_y)
        return_ax.set_ylim(return_y[0] - return_step, return_y[-1] + return_step)
        alpha_ax.set_ylim(alpha_y[0] - alpha_step, alpha_y[-1] + alpha_step)
        alpha_ax.yaxis.set_major_formatter(ticker.PercentFormatter(xmax=1, decimals=1))

        return_ax.set_xlim(xmin=0, xmax=len(assets_df) - 1)
        alpha_ax.set_xlim(xmin=0, xmax=len(assets_df) - 1)

        return_ax.grid(which='both', color='#C8BFE7', linewidth=1.5)
        return_ax.legend(loc=2, fontsize=MAX_FONT_SIZE)
        alpha_ax.legend(loc=9, fontsize=MAX_FONT_SIZE)

        return_plt = plt
        show_date = self.get_date_x(assets_df, 6)
        return_plt.xticks(ticks=list(show_date.keys()), labels=list(show_date.values()))
        return_plt.savefig(io_constants.newspaper_output_path + '收益.png', dpi=180, bbox_inches='tight')
        # return_plt.show()

        # 指标数据
        indicator_df = pd.DataFrame(data=self.__indicator_dict,
                                    index=[0])

        render_mpl_table(data=indicator_df,
                         header_columns=0,
                         row_height=0.8,
                         col_width=2.5,
                         header_color='w',
                         row_colors=['w', 'w'],
                         head_text_color='#4F81BD',
                         font_size=MAX_FONT_SIZE + 5)
        indicator_plt = plt

        indicator_plt.savefig(io_constants.newspaper_output_path + '指标数据.png', dpi=150, bbox_inches='tight')
        # indicator_plt.show()

        # 滚动三个月收益
        return_1q_df = self.__assets_df[IndicatorConstants.return_range].copy()
        return_1q_df.to_excel(
            io_constants.newspaper_output_path + self.__comb_info.name + '滚动' + str(IndicatorConstants.return_range)
            + '交易日收益' + io_constants.XLSX)
        return_1q_df = return_1q_df.dropna()
        plt.figure(figsize=(15.5, 5), dpi=180)
        roll_return_ax = return_1q_df.plot(kind='line', linewidth=3.0)
        roll_return_plt = plt
        roll_return_plt.gca().spines['right'].set_color('none')
        roll_return_plt.gca().spines['top'].set_color('none')
        roll_return_ax.tick_params(axis="x", labelsize=MAX_FONT_SIZE)
        roll_return_ax.tick_params(axis="y", labelsize=MAX_FONT_SIZE)

        roll_return_ax.grid(which='both', color='#C8BFE7', linewidth=1.5)
        roll_return_ax.set_xlim(xmin=0, xmax=len(return_1q_df) - 1)

        roll_return_y = []
        # range_data = return_1q_df.max() - return_1q_df.min()
        # roll_return_ax.yaxis.set_major_locator(MultipleLocator(range_data / TICK_STEP))
        # roll_return_ax.xaxis.set_major_locator(ticker.LinearLocator(numticks=5))
        max_roll_return = return_1q_df.max()
        min_roll_return = return_1q_df.min()
        roll_return_step = float(
            Decimal((return_1q_df.max() - return_1q_df.min()) / TICK_STEP).quantize(Decimal('0.0000'),
                                                                                    rounding=ROUND_UP))
        roll_return_init_data = 0
        roll_return_min_factor = int(
            Decimal((min_roll_return - roll_return_init_data) / roll_return_step).quantize(Decimal('0'),
                                                                                           rounding=ROUND_FLOOR))
        roll_return_max_factor = max(
            int(Decimal((max_roll_return - roll_return_init_data) / roll_return_step).quantize(Decimal('0'),
                                                                                               rounding=ROUND_UP)),
            roll_return_init_data)
        for num in range(roll_return_min_factor, roll_return_max_factor + 1):
            roll_return_y.append(roll_return_init_data + num * roll_return_step)

        # for y in np.linspace(return_1q_df.min(), return_1q_df.max(), num=TICK_STEP):
        #     y_list.append(float(Decimal(y).quantize(Decimal('0.000'), rounding=ROUND_UP)))
        # roll_return_ax.set_yticks(y_list)
        # roll_return_ax.set_ylim(return_1q_df.min() - return_1q_step, return_1q_df.max() + return_1q_step)
        roll_return_ax.set_yticks(roll_return_y)
        roll_return_ax.set_ylim(roll_return_y[0] - roll_return_step, roll_return_y[-1] + roll_return_step)
        roll_return_ax.yaxis.set_major_formatter(ticker.PercentFormatter(xmax=1, decimals=1))
        show_date = self.get_date_x(return_1q_df, 6)
        roll_return_plt.xticks(ticks=list(show_date.keys()), labels=list(show_date.values()))
        roll_return_plt.savefig(io_constants.newspaper_output_path + '滚动三月收益.png', bbox_inches='tight')
        # roll_return_plt.show()

        # 持仓类型占比图
        fund_type_df = self.__position_df.copy().groupby([PortfolioConstants.pfl_fund_type]).sum()
        fund_adj_time = np.array(self.__position_df[PortfolioConstants.pfl_fund_adj_time])[0]
        fund_type_df.columns = ['']

        fund_type_plt = plt
        fund_type_plt.rcParams['font.size'] = NORMAL_MAX_FONT_SIZE
        fund_type_df.plot.pie(subplots=True,
                              legend=False,
                              colors=['#C8BFE7', '#9CBA5B', '#DEA6A5', '#89AAD2'],
                              autopct="%.1f%%",
                              figsize=(6, 5))
        fund_type_plt.xticks(())
        fund_type_plt.yticks(())
        fund_type_plt.title('注：组合成分为最近一次调仓，时间为' + str(fund_adj_time),
                            fontsize=NORMAL_MAX_FONT_SIZE * 0.75,
                            y=0)
        fund_type_plt.savefig(io_constants.newspaper_output_path + '基金类型.png', dpi=170, bbox_inches='tight')
        # fund_type_plt.show()

        # 组合持仓详情
        position_df = self.__position_df[[PortfolioConstants.pfl_fund_code, PortfolioConstants.pfl_fund_name,
                                          PortfolioConstants.pfl_position, PortfolioConstants.pfl_fund_type]].copy()
        # position_df[CombConstants.comb_fund_name] = position_df[CombConstants.comb_fund_name].apply(
        #     lambda x: x[:-1] if x[-1] in ['A', 'C'] else x)
        position_df[PortfolioConstants.pfl_position] = position_df[PortfolioConstants.pfl_position].apply(
            lambda x: number_tools.format_percentage(x))
        position_df = position_df.rename(columns={
            PortfolioConstants.pfl_fund_code: PortfolioConstants.fund_code_ch,
            PortfolioConstants.pfl_fund_name: PortfolioConstants.fund_name_ch,
            PortfolioConstants.pfl_position: PortfolioConstants.fund_pos_ch,
            PortfolioConstants.pfl_fund_type: PortfolioConstants.fund_type_ch
        })
        render_mpl_table(position_df, header_columns=0, col_width=4.25, row_height=0.7,
                         header_color='#F79646',
                         font_size=32,
                         row_colors=['#FDEFE9', '#FFDEAD'], col_widths=[3, 8, 3, 3])
        position_plt = plt
        position_plt.savefig(io_constants.newspaper_output_path + '组合持仓详情.png', dpi=120, bbox_inches='tight')
        # position_plt.show()

        # 标题
        title_plt = plt
        fig = title_plt.figure(figsize=(10, 2))
        text = fig.text(0.5, 0.5, self.__comb_info.title, color='#E28B00', ha='center', va='center', size=30)
        text.set_path_effects([path_effects.SimpleLineShadow(), path_effects.Normal()])
        title_plt.savefig(io_constants.newspaper_output_path + '组合标题.png', dpi=300, bbox_inches='tight')
        # title_plt.show()

        # 标题标注
        title_label_plt = plt
        fig = title_label_plt.figure(figsize=(10, 2))
        text = fig.text(0.5, 0.5, self.__comb_info.title_label, color='black', ha='center', va='center', size=25)
        text.set_path_effects([path_effects.SimpleLineShadow(), path_effects.Normal()])
        title_label_plt.savefig(io_constants.newspaper_output_path + '组合标题标注.png', dpi=150, bbox_inches='tight')
        # title_label_plt.show()

        # 整合图片
        template_img = Image.open(r'' + io_constants.newspaper_input_path + self.__comb_dto.template)
        return_img = Image.open(r'' + io_constants.newspaper_output_path + '收益.png')
        indicator_img = Image.open(r'' + io_constants.newspaper_output_path + '指标数据.png')
        roll_return_img = Image.open(r'' + io_constants.newspaper_output_path + '滚动三月收益.png')
        com_detail_img = Image.open(r'' + io_constants.newspaper_output_path + '组合持仓详情.png')
        fund_type_img = Image.open(r'' + io_constants.newspaper_output_path + '基金类型.png')
        title_img = Image.open(r'' + io_constants.newspaper_output_path + '组合标题.png')
        title_label_img = Image.open(r'' + io_constants.newspaper_output_path + '组合标题标注.png')

        template_img.paste(title_img, (430, 100))
        template_img.paste(title_label_img, (450, 280))
        if self.__comb_dto.display_return_module:
            template_img.paste(return_img, (400, 700))
            template_img.paste(indicator_img, (600, 470))
        template_img.paste(com_detail_img, (390, 2180))
        template_img.paste(roll_return_img, (390, 3000))
        template_img.paste(fund_type_img, (2000, 2160))
        draw = ImageDraw.Draw(template_img)
        font = ImageFont.truetype("simkai.ttf", 80, encoding="unic")
        draw.text((2490, 288), datetime.datetime.now().strftime('%Y/%m/%d'), fill='black', font=font)

        if self.__comb_dto.display_evaluate:

            font = ImageFont.truetype("simkai.ttf", 50, encoding="unic")
            tmp_evaluate = self.__evaluate.format(self.__comb_info.name, self.__indicator_dict['最近一周'])
            # tmp_evaluate = tmp_evaluate.encode('gbk')
            lines = textwrap.wrap(tmp_evaluate, replace_whitespace=False, width=45)
            y_text = 3980
            for line in lines:
                width, height = font.getsize(line)
                draw.text((425, y_text), line, font=font, fill='black', ha='right', wrap=True)
                y_text += height + 15

        template_img.save(io_constants.newspaper_report_output_path + self.__comb_info.name + '周报.png')

    """
    :@deprecated: 获取x轴的时间显示项
    :@param:
    :@return: 
    """

    def get_date_x(self, df: pd.DataFrame, size):
        if size == 1:
            raise Exception('x轴至少有1个以上')
        indexes = df.index
        total_assets = len(indexes)
        dis = int(total_assets / (size - 1))
        show_date = {}
        tmp_index = 0
        for index, date in enumerate(indexes):
            if index % dis == 0:
                tmp_index = index
                show_date[index] = date
            if index == total_assets - 1:
                if len(show_date) == size:
                    show_date.pop(tmp_index)
                show_date[index] = date

        return show_date


"""
:@deprecated: 周报输出
:@param: 
:@return: 
"""


def newspaper_factory(v_comb_dto: CombDto):
    newspaper = Newspaper(v_comb_dto=v_comb_dto)
    newspaper.indicator_factory()
    newspaper.assets_to_excel()
    newspaper.draw()


comb_dto_LAIFU = CombDto()
comb_dto_LAIFU_PLUS = CombDto()
comb_dto_FIX_INCOME = CombDto()
comb_dto_XIAOQUEXING = CombDto()
comb_dto_CREATE_MONEY = CombDto()
comb_dto_WANGCAI = CombDto()
comb_dto_XINGFU = CombDto()

# evaluate = '【{name}】上周收益为【{return}】，符合预期。成分基金中，周收益居前的是【{top_1_name}】基金收益为【{top_1_return}】与【{top_2_name}】基金收益为【top_2_return】。上周A股宽幅震荡，上证指数小幅上行0.4%，沪深300上行0.5%，创业板指上行0.7%。行业层面，钢铁（6.2%）、通信（4.2%）和采掘（3.9%）表现较好。下半年经济或边际小幅转弱，近期降准的主要作用在于降低融资成本、对冲MLF到期以及对冲经济下滑，但当前的经济状态意味着并没有所谓的新一轮宽松周期开启。降准并不意味着央行的货币政策转向宽松，未来货币政策更可能是相机决策。从目前已公布的上市公司公报来看间有限，则中游制造板块的盈利修复值得关注。综合此次二季报披露率较高、预告业绩增速靠细分行业，有望下半年在基本面和股价上均超市场预期，此类细分行业值得关注。'

# evaluate = '本周权益市场整体下行，其中上证综指下跌4.31%，深圳成指下跌3.70%，创业版指下跌0.86%。其中通信（+2.32%）、有色（+1.88%）、电子（+1.32%）表现较好。国内权益市场需警惕疫情反复带来的风险，以及经济加速下行带来的风险，债市需关注财政偏紧局面是否会出现改变，若出现宽信用转向，将对债市有一定冲击。'

evaluate = '国内权益市场需关注能源紧缺对经济的综合影响，债市需关注财政偏紧局面是否会出现改变，若出现宽信用转向，将对债市有一定冲击。'
# TODO 自动获取最新
end_date = '20211105'
# today = time_tools.now_yymmdd()
# end_date = time_tools.find_trade_date(today, -1)
# print(end_date)

# 来福
comb_dto_LAIFU.code = 'ZH032924'
comb_dto_LAIFU.dict_id = comb_dto_LAIFU.code
comb_dto_LAIFU.begin_date = '20200316'
comb_dto_LAIFU.end_date = end_date
comb_dto_LAIFU.bench_equity_position = 0.1
comb_dto_LAIFU.bench_bond_position = 1 - comb_dto_LAIFU.bench_equity_position
comb_dto_LAIFU.evaluate = evaluate
newspaper_factory(comb_dto_LAIFU)

# 固收加强
comb_dto_FIX_INCOME.code = 'ZH032924'
comb_dto_FIX_INCOME.dict_id = 'ZH032924_TMP'
comb_dto_FIX_INCOME.begin_date = '20200316'
comb_dto_FIX_INCOME.end_date = end_date
comb_dto_FIX_INCOME.bench_equity_position = 0.1
comb_dto_FIX_INCOME.bench_bond_position = 1 - comb_dto_FIX_INCOME.bench_equity_position
comb_dto_FIX_INCOME.template = 'template_tmp.png'
comb_dto_FIX_INCOME.roll_trade_day = TradeDatePeriodConstants.HALF_YEAR
comb_dto_FIX_INCOME.evaluate = evaluate
comb_dto_FIX_INCOME.display_return_module = False
comb_dto_FIX_INCOME.display_evaluate = False
newspaper_factory(comb_dto_FIX_INCOME)

# 来福Plus
comb_dto_LAIFU_PLUS.code = 'ZH045084'
comb_dto_LAIFU_PLUS.dict_id = comb_dto_LAIFU_PLUS.code
comb_dto_LAIFU_PLUS.begin_date = '20200617'
comb_dto_LAIFU_PLUS.end_date = end_date
comb_dto_LAIFU_PLUS.bench_equity_position = 0.2
comb_dto_LAIFU_PLUS.bench_bond_position = 1 - comb_dto_LAIFU_PLUS.bench_equity_position
comb_dto_LAIFU_PLUS.evaluate = evaluate
newspaper_factory(comb_dto_LAIFU_PLUS)

# 为你创金
comb_dto_CREATE_MONEY.code = 'ZH037782'
comb_dto_CREATE_MONEY.dict_id = comb_dto_CREATE_MONEY.code
comb_dto_CREATE_MONEY.begin_date = '20190923'
comb_dto_CREATE_MONEY.end_date = end_date
comb_dto_CREATE_MONEY.stk_bench_mark_code = IndexWindCodeConstants.csi_800
comb_dto_CREATE_MONEY.bench_equity_position = 1
comb_dto_CREATE_MONEY.bench_bond_position = 1 - comb_dto_CREATE_MONEY.bench_equity_position
comb_dto_CREATE_MONEY.evaluate = evaluate
newspaper_factory(comb_dto_CREATE_MONEY)

#  小确幸
comb_dto_XIAOQUEXING.code = 'simulation'
comb_dto_XIAOQUEXING.dict_id = comb_dto_XIAOQUEXING.code
comb_dto_XIAOQUEXING.begin_date = '20190101'
comb_dto_XIAOQUEXING.end_date = end_date
comb_dto_XIAOQUEXING.excel_db = {comb_dto_XIAOQUEXING.USE_EXCEL: True,
                                 comb_dto_XIAOQUEXING.EXCEL_PATH: io_constants.newspaper_input_path + '创金小确幸调仓.xlsx',
                                 comb_dto_XIAOQUEXING.INDEX_CODE: IndexWindCodeConstants.ccy_11025,
                                 comb_dto_XIAOQUEXING.BOND_INDEX_CODE: IndexWindCodeConstants.csi_11015}
comb_dto_XIAOQUEXING.evaluate = evaluate
newspaper_factory(comb_dto_XIAOQUEXING)

# 旺财
comb_dto_WANGCAI.code = 'ZH058937'
comb_dto_WANGCAI.dict_id = comb_dto_WANGCAI.code
comb_dto_WANGCAI.begin_date = '20210105'
comb_dto_WANGCAI.end_date = end_date
comb_dto_WANGCAI.bench_equity_position = 0.6
comb_dto_WANGCAI.bench_bond_position = 1 - comb_dto_WANGCAI.bench_equity_position
comb_dto_WANGCAI.evaluate = evaluate
newspaper_factory(comb_dto_WANGCAI)

# 稳稳的幸福
comb_dto_XINGFU.code = 'ZH013136'
comb_dto_XINGFU.dict_id = comb_dto_XINGFU.code
comb_dto_XINGFU.begin_date = '20200316'
comb_dto_XINGFU.end_date = end_date
comb_dto_XINGFU.bench_equity_position = 0.1
comb_dto_XINGFU.bench_bond_position = 1 - comb_dto_XINGFU.bench_equity_position
comb_dto_XINGFU.evaluate = evaluate
newspaper_factory(comb_dto_XINGFU)
