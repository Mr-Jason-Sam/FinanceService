"""
@Description : 指标Pro（基于dataframe）
@Author      : Jason_Sam
@Time        : 2021/1/26 15:26

"""

import matplotlib.pyplot as plt
import numpy as np

from constants.object.assets_constants import AssetsConstants
from constants.object.date_section_constants import DateSectionConstants
from constants.object.max_drawdown_constants import MaxDrawDownConstants
from constants.time_constants import TradeDatePeriodConstants
from tools import math_tools

"""
:@deprecated: 检查资产DataFrame是否符合规则
:@param: assets_df 资产DataFrame
:@return: 
"""


def check_assets_df(assets_df):
    if AssetsConstants.assets not in list(assets_df.columns) and not assets_df[AssetsConstants.assets]:
        raise RuntimeError("不存在ASSETS数据")
    if not np.issubdtype(assets_df[AssetsConstants.assets], np.number):
        raise RuntimeError("ASSETS数据并非所有都是数字")


"""
:@deprecated: 检查资产DataFrame的bench_mark是否符合规则
:@param: assets_df 资产DataFrame
:@return: 
"""


def check_bench_mark_df(assets_df):
    if AssetsConstants.bench_mark_assets not in list(assets_df.columns) and not assets_df[AssetsConstants.bench_mark_assets]:
        raise RuntimeError("不存在BENCH_MARK_ASSETS数据")
    if not np.issubdtype(assets_df[AssetsConstants.bench_mark_assets], np.number):
        raise RuntimeError("BENCH_MARK_ASSETS数据并非所有都是数字")


"""
:@deprecated: 处理NAN数据
:@param: assets_df 资产DataFrame
:@return: 
"""


def assets_nan_delete(assets_df, col_name_list):
    return assets_df.dropna(axis=0, subset=col_name_list)


"""
:@deprecated: 资产按照日期排序
:@param: assets_df 资产DataFrame
:@param: is_asc 是否按升序排序
:@return: 
"""


def assets_order_by(assets_df, is_asc=True):
    return assets_df.sort_index(ascending=is_asc)


"""
:@deprecated: 组装assets_df
:@param: assets_df 资产DataFrame
:@param: is_date_asc 是否按升序排序
:@return: 
"""


def assemble_assets(assets_df, is_date_asc):
    return assemble_assets_template(assets_df=assets_df,
                                    is_date_asc=is_date_asc,
                                    assets_name=AssetsConstants.assets,
                                    day_return_name=AssetsConstants.day_return)


"""
:@deprecated: 组装assemble_bench_mark_assets
:@param: assets_df 资产DataFrame
:@param: is_date_asc 是否按升序排序
:@return: 
"""


def assemble_bench_mark_assets(assets_df, is_date_asc):
    return assemble_assets_template(assets_df=assets_df,
                                    is_date_asc=is_date_asc,
                                    assets_name=AssetsConstants.bench_mark_assets,
                                    day_return_name=AssetsConstants.bench_mark_day_return)


"""
:@deprecated: 组装资产的模板
:@param: assets_df 资产DataFrame
:@param: is_date_asc 是否按升序排序
:@return: 
"""


def assemble_assets_template(assets_df, is_date_asc, assets_name, day_return_name):
    cols_name_list = [assets_name]
    values = {day_return_name: 0}
    # absolute return init
    tmp = assets_df.copy()

    if assets_name == AssetsConstants.assets:
        check_assets_df(tmp)
    elif assets_name == AssetsConstants.bench_mark_assets:
        check_bench_mark_df(tmp)

    tmp = assets_nan_delete(tmp, cols_name_list)
    tmp[day_return_name] = tmp[assets_name] / tmp[assets_name].shift(axis=0, periods=1) - 1
    tmp = assets_order_by(tmp, is_date_asc)
    tmp = tmp.fillna(value=values)
    return tmp


class Indicator(object):
    """
    Example：
                    assets
        20200101    1.0
        20200102    1.2

    """

    def __init__(self, assets_df, windows=None, ann=True, is_date_asc=True, has_bench_info=False):
        self.__assets_df = assemble_assets(assets_df, is_date_asc)
        self.__assets_with_bm_df = None if not has_bench_info else assemble_bench_mark_assets(self.__assets_df,
                                                                                              is_date_asc)
        self.__ann = ann
        self.__windows = windows if windows else len(self.__assets_df)
        self.__is_date_asc = is_date_asc

    """
    :@deprecated: 最大回撤信息
    :@param: 
    :@return: MaxDrawDownConstants 最大回撤信息
    """

    def max_dd_info(self):
        assets_list = self.__assets_df[AssetsConstants.assets]
        assets_list = assets_list.reset_index(drop=True)
        # roll_max = pd.Series(assets_list.expanding().max())
        end_pos = np.argmax(np.maximum.accumulate(assets_list) / assets_list - 1)
        if end_pos == 0:
            return {
                MaxDrawDownConstants.max_drawdown: 0,
                MaxDrawDownConstants.max_assets: assets_list[len(assets_list) - 1],
                MaxDrawDownConstants.min_assets: assets_list[len(assets_list) - 1],
                MaxDrawDownConstants.max_assets_date: self.__assets_df.index.values[len(assets_list) - 1],
                MaxDrawDownConstants.min_assets_date: self.__assets_df.index.values[len(assets_list) - 1]
            }

        begin_pos = np.argmax(assets_list[:end_pos])

        # if assets_list[begin_pos] == 0:
        #     raise RuntimeError(ExceptionCode.DATA_ERROR)

        max_dd_info = {
            MaxDrawDownConstants.max_drawdown: 1 - assets_list[end_pos] / assets_list[begin_pos],
            MaxDrawDownConstants.max_assets: assets_list[begin_pos],
            MaxDrawDownConstants.min_assets: assets_list[end_pos],
            MaxDrawDownConstants.max_assets_date: self.__assets_df.index.values[begin_pos],
            MaxDrawDownConstants.min_assets_date: self.__assets_df.index.values[end_pos]
        }

        return max_dd_info

    """
    :@deprecated: 获取最大回撤的数值
    :@param: 
    :@return: 
    """

    def max_dd(self):
        return self.max_dd_info().get(MaxDrawDownConstants.max_drawdown)

    """
    :@deprecated: 区间收益率
    :@param: 
    :@return: float64
    """

    def range_return(self):
        return self.range_return_template(self.__assets_df, AssetsConstants.assets)

    # """
    #     :@deprecated: 区间收益率
    #     :@param:
    #     :@return: float64
    #     """
    # def trade_date_return(self, before_trade_dates):
    #     if before_trade_dates > len(self.__assets_df):
    #         # TODO 可以获取更多的数据即可计算
    #         return 0
    #     before_trade_date = self.__assets_df.index[-1 * before_trade_dates]
    #     return self.range_return_template(self.__assets_df, AssetsConstants.assets, before_trade_date)

    """
    :@deprecated: 滚动波动率
    :@param: 
    :@return: float64
    """

    def roll_vol(self):
        day_return_list = self.__assets_df[AssetsConstants.day_return]

        roll_vol_res = np.std(day_return_list, ddof=1)
        if self.__ann:
            roll_vol_res *= np.power(TradeDatePeriodConstants.YEAR, 0.5)
        return roll_vol_res

    """
    :@deprecated: EWMA波动率
    :@param: 
    :@return: float64
    """

    def ewma_vol(self, v_lambda=0.01):
        assets_tmp = self.__assets_df
        if self.__is_date_asc:
            assets_tmp = assets_order_by(self.__assets_df, False)

        day_return_list = assets_tmp[AssetsConstants.day_return]
        ewma_vol_res = math_tools.EWMA_std(day_return_list, v_lambda, False)

        if self.__ann:
            ewma_vol_res *= np.power(TradeDatePeriodConstants.YEAR, 0.5)
        return ewma_vol_res

    """
    :@deprecated: 夏普比率 = 区间收益率 / 波动率
    :@param: 
    :@return: float64 
    """

    def sharpe_ratio(self):
        return_data = self.range_return()
        vol = self.roll_vol()

        if not return_data or not vol:
            return None

        return return_data / vol

    """
    :@deprecated: 索提诺比率 = 区间收益率 / 负收益率集合
    :@param: 
    :@return: float64
    """

    def sortino_ratio(self):
        return_data = self.range_return()

        day_return_list = self.__assets_df[AssetsConstants.day_return]

        negative = 0
        negative_num = 0
        # 负数集合
        for day_return in day_return_list:
            if day_return < 0:
                negative += np.power(day_return, 2)
                negative_num += 1

        if negative_num == 0:
            negative = 1
        else:
            negative = np.power(negative / negative_num, 0.5)

        if self.__ann:
            negative *= np.power(TradeDatePeriodConstants.YEAR, 0.5)

        if negative == 0:
            return None

        if not return_data or not negative:
            return None

        return return_data / negative

    """
    :@deprecated: 卡玛比率 = 区间收益率 / 最大回撤
    :@param: 
    :@return: float64
    """

    def calmar_ratio(self):
        return_data = self.range_return()

        max_dd_data = self.max_dd()

        if max_dd_data == 0:
            return None

        if not return_data or not max_dd_data:
            return None

        return return_data / max_dd_data

    """
    :@deprecated: 斯特林=最大N个回撤的简单平均
    :@param: max_sample 最大回撤样本数量
    :@return: 
    """

    def strling(self, max_sample=5):
        date_section_list = [{DateSectionConstants.begin_date: self.__assets_df.first_valid_index(),
                              DateSectionConstants.end_date: self.__assets_df.last_valid_index()}
                             ]
        max_dd_info_list = []
        self.strling_recursive(date_section_list, max_dd_info_list, max_sample)

        if not max_dd_info_list:
            return None

        max_dd_list = []
        for info in max_dd_info_list:
            max_dd_list.append(info[MaxDrawDownConstants.max_drawdown])

        return np.mean(max_dd_list)

    """
    :@deprecated: 斯特林递归内容
    :@param: date_section_list 最大回撤查找日期区间列表
    :@param: max_dd_info_list 最大回撤列表
    :@param: max_sample 最大回撤样本数量
    :@return: 
    """

    def strling_recursive(self, date_section_list, max_dd_info_list, max_sample):
        max_dd_info_data = {MaxDrawDownConstants.max_drawdown: 0}

        new_date_section = {}

        # 达到样本数
        if len(max_dd_info_list) == max_sample:
            return max_dd_info_list

        for date_section in date_section_list:
            indicator_sub = Indicator(
                self.__assets_df.loc[date_section[DateSectionConstants.begin_date]:date_section[DateSectionConstants.end_date]])
            max_dd_info_data_tmp = indicator_sub.max_dd_info()

            if max_dd_info_data_tmp[MaxDrawDownConstants.max_drawdown] > max_dd_info_data[MaxDrawDownConstants.max_drawdown]:
                max_dd_info_data = max_dd_info_data_tmp

        # 区间内无最大回撤
        if max_dd_info_data[MaxDrawDownConstants.max_drawdown] == 0:
            return max_dd_info_list
        max_dd_info_list.append(max_dd_info_data)

        for date_section in date_section_list:
            if date_section[DateSectionConstants.begin_date] <= max_dd_info_data[MaxDrawDownConstants.max_assets_date] \
                    and date_section[DateSectionConstants.end_date] >= max_dd_info_data[MaxDrawDownConstants.min_assets_date]:
                new_date_section = {
                    DateSectionConstants.begin_date: max_dd_info_data[MaxDrawDownConstants.min_assets_date],
                    DateSectionConstants.end_date: date_section[DateSectionConstants.end_date]
                }
                date_section[DateSectionConstants.end_date] = max_dd_info_data[MaxDrawDownConstants.max_assets_date]
                break

        if new_date_section and new_date_section[DateSectionConstants.begin_date] != new_date_section[DateSectionConstants.end_date]:
            date_section_list.append(new_date_section)

        self.strling_recursive(date_section_list, max_dd_info_list, max_sample)

    """
    :@deprecated: 信息比率 = 超额收益率 / 跟踪误差
    :@param: 
    :@return: float64
    """

    def info_ratio(self):
        alpha = self.alpha()
        tracking_error = self.tracking_error()

        if not alpha or not tracking_error:
            return None

        return alpha / tracking_error

    """
    :@deprecated: 跟踪误差 = std(基金日收益率-基准日收益率)
    :@param: 
    :@return: float64
    """

    def tracking_error(self):
        day_return_minus_list = self.__assets_with_bm_df[AssetsConstants.day_return] - self.__assets_with_bm_df[
            AssetsConstants.bench_mark_day_return]

        tracking_error = np.std(day_return_minus_list, ddof=1)

        if self.__ann:
            return tracking_error * np.power(TradeDatePeriodConstants.YEAR, 0.5)

        return tracking_error

    """
    :@deprecated: 超额收益率 = 区间收益率 - 业绩基准收益率
    :@param: 
    :@return: float64
    """

    def alpha(self):
        assets_return = self.range_return()
        bench_mark_return = self.bench_mark_range_return()

        if not assets_return or not bench_mark_return:
            return None

        return assets_return - bench_mark_return

    """
    :@deprecated: 业绩基准收益率
    :@param: 
    :@return: 
    """

    def bench_mark_range_return(self):
        return self.range_return_template(self.__assets_with_bm_df, AssetsConstants.bench_mark_assets)

    """
    :@deprecated: 最大回撤修复期
    :@param: 
    :@return: int 天数
    """
    def max_drawdown_repair(self):
        max_dd_info = self.max_dd_info()
        if not max_dd_info or max_dd_info.get(MaxDrawDownConstants.max_drawdown) == 0:
            raise RuntimeError("该区间无最大回撤")
        after_min_assets = self.__assets_df[max_dd_info.get(MaxDrawDownConstants.min_assets_date):]

        after_repaired_assets = after_min_assets[after_min_assets[AssetsConstants.assets] >= max_dd_info.get(MaxDrawDownConstants.max_assets)]
        if after_repaired_assets.empty:
            raise RuntimeError("该区间内最大回撤仍未修复")
        else:
            return len(after_min_assets) - len(after_repaired_assets)

    """
    :@deprecated: 最大回撤持续期
    :@param: 
    :@return: int 天数
    """
    def max_drawdown_period(self):
        max_dd_info = self.max_dd_info()
        if not max_dd_info or max_dd_info.get(MaxDrawDownConstants.max_drawdown) == 0:
            raise RuntimeError("该区间无最大回撤")
        period = self.__assets_df.loc[max_dd_info.get(MaxDrawDownConstants.max_assets_date):max_dd_info.get(MaxDrawDownConstants.min_assets_date)]
        return len(period) - 1

    """
    :@deprecated: IRR
    :@param: 
    :@return: 
    """
    def irr(self, cash: float, interval: int):
        # 得到总投资金额和账户累积总资产的dataframe
        data = self.__assets_df.copy()
        data.loc[data.index[0], 'money'] = 0  # 此处money即客户的账户资金,初始化为0
        data.loc[data.index[0], 'investment'] = 0  # 此处investment为客户投资金额，初始化为0
        for day in range(0, len(data), interval):
            start_date = self.__assets_df.index[day]  # 每一个阶段的第一天定投
            data.loc[start_date, 'money'] = data.loc[start_date, 'money'] + cash
            data.loc[start_date, 'investment'] = data.loc[start_date, 'investment'] + cash
            data.loc[day:day + interval + 1, 'money'] = data[day:day + interval + 1][AssetsConstants.assets] * (
                    data.loc[start_date, 'money'] / data.loc[start_date, AssetsConstants.assets])
            data.loc[day:day + interval + 1, 'investment'] = data.loc[start_date, 'investment']

        # 计算IRR
        data['cash_flow'] = 0
        for day in range(0, len(data), interval):
            start_date = self.__assets_df.index[day]  # 每一个阶段的第一天定投
            data.loc[start_date, 'cash_flow'] = -1 * cash
        data.loc[data.index[-1], 'cash_flow'] = data.loc[data.index[-1], 'cash_flow'] + data.loc[
            data.index[-1], 'money']
        irr = np.irr(data['cash_flow'])


        # # 画图
        # data.index = data[AssetsConstants.trade_date]
        # mpl.rcParams['font.sans-serif'] = ['KaiTi', 'SimHei', 'FangSong']  # 汉字字体,优先使用楷体，如果找不到楷体，则使用黑体
        # mpl.rcParams['font.size'] = 24  # 字体大小
        # mpl.rcParams['axes.unicode_minus'] = False  # 正常显示负号
        # plt.figure(dpi=200, figsize=(12, 8))
        # plt.plot(data['money'], label='账户累积总资产')
        # plt.plot(data['investment'], label='总投入额')
        # # plt.xticks(data.index, rotation="vertical")
        # # plt.xticks(rotation=45)
        # plt.gca().xaxis.set_major_locator(ticker.MultipleLocator(TradeDatePeriodConstants.YEAR))
        # plt.title(title)
        # plt.legend()
        # plt.yticks([100000, 200000, 300000, 400000, 500000, 600000],
        #            ['10万元', '20万元', '30万元', '40万元', '50万元', '60万元'])
        # # plt.gca().yaxis
        # # plt.gca().yaxis.set_major_formatter(matplotlib.ticker.FormatStrFormatter('%.1f 万元'))
        # plt.tick_params(labelsize=18)
        # plt.show()
        # # plt.savefig(r"./定投曲线.png")

        if self.__ann:
            irr = (1 + irr) ** TradeDatePeriodConstants.YEAR - 1

        return irr
    
    """
    :@deprecated: 滚动收益率
    :@param: 
    :@return: 
    """
    def rolling_earning(self, interval, title):
        data = self.__assets_df.copy()[[AssetsConstants.assets]]
        data['interval_return'] = data[AssetsConstants.assets]/data[AssetsConstants.assets].shift(axis=0, periods=interval) - 1
        data = data.dropna()

        # draw
        plt.figure(dpi=200, figsize=(12, 8))
        plt.hist(data['interval_return'], bins=150)
        plt.title(title)
        plt.yticks([])
        plt.savefig(r"./" + str(interval) + "交易日收益曲线分布.png")
        plt.show()

    """
    :@deprecated: 收益率模板
    :@param: 
    :@return: 
    """
    def range_return_template(self, assets_df, assets_name, before_trade_date=None):
        first_assets = assets_df.loc[assets_df.first_valid_index(), assets_name] if not before_trade_date else assets_df.loc[before_trade_date, assets_name]
        last_assets = assets_df.loc[assets_df.last_valid_index(), assets_name]
        range_return = last_assets / first_assets - 1

        if self.__ann:
            range_return = np.power(range_return + 1, TradeDatePeriodConstants.YEAR / self.__windows) - 1

        return range_return


