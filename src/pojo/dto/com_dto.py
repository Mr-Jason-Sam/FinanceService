"""
@Description : 组合请求数据
@Author      : Jason_Sam
@Time        : 2021/3/8 16:48

"""
from constants.object.index_wind_code_constants import IndexWindCodeConstants
from constants.time_constants import TradeDatePeriodConstants


class CombDto:
    code: str
    begin_date: str = None
    end_date: str = None
    dict_id: str
    roll_trade_day: int = TradeDatePeriodConstants.QUARTER
    template: str = 'template.png'

    bench_equity_position: float
    bench_bond_position: float

    evaluate: str
    quote_evaluate = True

    USE_EXCEL = 'USE_EXCEL'
    EXCEL_PATH = 'EXCEL_PATH'
    INDEX_CODE = 'INDEX_CODE'
    BOND_INDEX_CODE = 'BOND_INDEX_CODE'
    excel_db: dict = {USE_EXCEL: False,
                      EXCEL_PATH: '',
                      INDEX_CODE: '',
                      BOND_INDEX_CODE: ''}

    display_return_module = True
    display_evaluate = True

    stk_bench_mark_code: str = IndexWindCodeConstants.hs_300
    bond_bench_mark_code: str = IndexWindCodeConstants.cba_bond
