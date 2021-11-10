"""
@Description : 样式工具
@Author      : Jason_Sam
@Time        : 2021/3/5 12:18

"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import six


def render_mpl_table(data, col_width=3.0, row_height=0.625, font_size=16,
                     header_color='#40466e', row_colors=None, edge_color='w',
                     head_text_weight='bold', head_text_color='w', col_widths=None,
                     bbox=None, header_columns=0,
                     ax=None, **kwargs):
    if bbox is None:
        bbox = [0, 0, 1, 1]
    if row_colors is None:
        row_colors = ['#f1f1f2', 'w']
    if ax is None:
        size = (np.array(data.shape[::-1]) + np.array([0, 1])) * np.array([col_width, row_height])
        fig, ax = plt.subplots(figsize=size)
        ax.axis('off')

    if col_widths is None:
        mpl_table = ax.table(cellText=data.values, bbox=bbox, colLabels=data.columns, **kwargs)
    else:
        mpl_table = ax.table(cellText=data.values, bbox=bbox, colLabels=data.columns, **kwargs,
                             colWidths=col_widths)

    mpl_table.auto_set_font_size(False)
    mpl_table.set_fontsize(font_size)

    for k, cell in six.iteritems(mpl_table._cells):
        cell.set_edgecolor(edge_color)
        if k[0] == 0 or k[1] < header_columns:
            cell.set_text_props(weight=head_text_weight, color=head_text_color)
            cell.set_facecolor(header_color)
        else:
            cell.set_text_props(ha='center')
            cell.set_facecolor(row_colors[k[0] % len(row_colors)])
    return ax
