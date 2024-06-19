# -*- coding: utf-8 -*-
{
    "name": "TVAN Systemmmmm",
    "summary": "TVAN System",
    "version": "15.0.1.0.1",
    "category": "account",
    "website": "https://latido.vn",
    "author": "LATIDO JSC, Trình Gia Lạc",
    "license": "OPL-1",
    "depends": [
        "mail", "web", "smile_api_rest",
    ],
    "data": [
        'security/ir.model.access.csv',
        # "data/api_request_data.xml",
        # "data/tct_format_data.xml",
        "data/xml_template_01_data.xml",
        "data/xml_template_inv_data.xml",
        "data/xml_template_tb04_data.xml",
        # "data/api_01_data.xml",
        # "data/api_inv_data.xml",
        # "data/api_tb04_data.xml",
        "views/tvan_config_view.xml",
        "views/users_view.xml",
        "views/tvan_log_view.xml",
        "views/tvan_template_view.xml",
        "views/menu_view.xml",
    ],
    "external_dependencies": {
        "python": ["xmltodict"]
    },
    "post_load": "post_load_hook",
    "application": False,
    "installable": True,
}
