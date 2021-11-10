import numpy as np


def EWMA_std(data_list, factor, use_avg=True):
    if factor < 0 or factor > 1:
        # TODO Exception
        print('EWMA_std Exception')

    _sum = 0

    data_avg = 0
    if use_avg:
        data_avg = np.mean(data_list)

    for index, data in enumerate(data_list):
        _sum = _sum + factor * np.power(1 - factor, index) * np.power(float(data) - data_avg, 2)

    return np.power(_sum, 0.5)

