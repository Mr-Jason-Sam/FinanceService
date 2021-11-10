"""
@Description : 组合字典
@Author      : Jason_Sam
@Time        : 2021/3/18 16:17

"""
from constants.object.newspaper_constants import NewspaperConstants

PFL_DICT = {
    'ZH032924': {
        NewspaperConstants.name: '创金来福固收+组合',
        NewspaperConstants.title_label: '严控风险，稳健投资，追求稳定收益'
    },
    'ZH032924_TMP': {
        NewspaperConstants.name: '固收加强组合',
        NewspaperConstants.title_label: '严控风险，稳健投资，追求稳定收益'
    },
    # 'ZH037782': {
    #     NewspaperConstants.name: '为你创金纯权益组合',
    #     NewspaperConstants.title_label: '行业轮动，追求更高风险回报'
    # },
    'ZH037782': {
        NewspaperConstants.name: '为你创金景气行业组合',
        NewspaperConstants.title_label: '组合主理人：王妍 创金合信行业投资研究部总监(行业轮动，追求更高风险回报)'
    },
    'ZH045084': {
        NewspaperConstants.name: '创金来福Plus固收+组合',
        NewspaperConstants.title_label: '严控风险，稳健投资，更高风险敞口，更高收益'
    },
    'simulation': {
        NewspaperConstants.name: '创金小确幸组合',
        NewspaperConstants.title_label: '现金管理新进阶，满满"小确幸"'
    },
    'ZH058937': {
        NewspaperConstants.name: '创金旺财组合',
        NewspaperConstants.title_label: '严控风险，稳健投资，追求稳定收益'
    },
    'ZH013136': {
        NewspaperConstants.name: '我要稳稳的幸福组合',
        NewspaperConstants.title_label: '严控风险，稳健投资，追求稳定收益'
    },
}

INDEX_DICT = {
    '000001.SH': '上证指数',
    '399001.SZ': '深证成指',
    '399006.SZ': '创业板指'
}

PFL_EXAMPLE = '【{name}】上周收益为【{range_return}】，符合预期。成分基金中，周收益居前的是【{top_1_name}】基金收益为【{top_1_return}】与【{top_2_name}】基金收益为【{top_2_return}】。'
INDEX_EXAMPLE = '上周A股指数方面，【{sh_index}】{sh_index_desc}、【{sz_index}】{sz_index_desc}、【{business_index}】{business_index_desc}。'
INDUSTRY_EXAMPLE = '行业方面，【{industry_1}】{industry_1_desc}、【{industry_2}】{industry_2_desc}、【{industry_3}】{industry_3_desc}。'
