# -*- coding: utf-8 -*-
{
    "name": "Report Engine",
    "summary": "Report Engine",
    "version": "15.0.1.0.1",
    "category": "account",
    "website": "https://latido.vn",
    "author": "LATIDO JSC, Trình Gia Lạc",
    "license": "OPL-1",
    "depends": [
        "auth_totp", "report_aeroo",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/res_users_view.xml",
        "views/report_template_odt_view.xml",
        "views/report_pdf_view.xml",
        "views/menu_view.xml",
    ],
    "application": False,
    "installable": True,
}
