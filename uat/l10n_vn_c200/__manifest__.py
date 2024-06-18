# -*- coding: utf-8 -*-
{
    "name": "Vietnam - Accounting C200",
    "version": "12.0.1.0.3",
    "author": "LATIDO JSC",
    "website": "https://latido.vn",
    "category": "Localization",
    "description": """
This is the module to manage the accounting chart for Vietnam in Odoo.
=========================================================================

This module applies to companies based in Vietnamese Accounting Standard (VAS)
with Chart of account under Circular No. 200/2014/TT-BTC

""",
    "depends": [
        "account",
        "base_iban",
        "l10n_multilang"
    ],
    "data": [
         'data/l10n_vn_chart_data.xml',
         'data/account.account.template.csv',
         'data/l10n_vn_chart_post_data.xml',
         'data/account_tax_group_data.xml',
         'data/account_tax_report_data.xml',
         'data/account_tax_data.xml',
         'data/account_chart_template_data.xml',
         'views/account_view.xml',
    ],

    'demo': [
        'demo/demo_company.xml',
    ],
    'post_init_hook': '_post_init_hook',
    'license': 'LGPL-3',
}