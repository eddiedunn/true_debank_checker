"""
This module defines various cell format dictionaries used for styling
Excel cells in the application. These formats include header formats,
wallets column formats, and total cell formats.
"""

from app.config import BLACK_COLOR

header_format_dict = {
    'font_color': '#000000' if BLACK_COLOR else '#ffffff',
    'font_size': 14,
    'bg_color': '#339c5d',
    'bold': True,
    'align': 'center',
    'valign': 'vcenter',
    'text_wrap': True,
    'border': 1
}

wallets_column_format_dict = {
    'font_size': 12,
    'bg_color': '#e0f2f1',
    'bold': True,
    'align': 'center',
    'valign': 'vcenter',
    'text_wrap': True,
    'border': 1
}

total_cell_format_dict = {
    'font_size': 12,
    'bg_color': '#b2dfdb',
    'bold': True,
    'align': 'center',
    'valign': 'vcenter',
    'text_wrap': True,
    'border': 1
}

common_ceil_format_dict = {
    'align': 'center',
    'valign': 'vcenter',
    'text_wrap': True,
}

usd_ceil_format_dict = {
    'bg_color': '#e0f2f1',
    'align': 'center',
    'valign': 'vcenter',
    'text_wrap': True,
    'bold': True,
    'border': 1
}

donate_cell_format_dict = {
    'font_size': 11,
    'bold': True,
    'align': 'center',
    'valign': 'vcenter',
    'text_wrap': True,
    'border': 1
}
