# -*- coding: utf-8 -*-
{
    "name": "WL Lib",
    "summary": "WL Lib",
    "version": "15.0.1.0.1",
    "category": "account",
    "website": "https://latido.vn",
    "author": "LATIDO JSC, Trình Gia Lạc",
    "license": "OPL-1",
    "depends": [
        "mail", "web",
    ],
    "data": [
        "views/portal_sign_view.xml",
        "views/sequence_view.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "wingroup_lib/static/src/js/digital_sign.js",
            "wingroup_lib/static/src/js/field_utils.js",
        ],
        "web.assets_qweb": [
            "wingroup_lib/static/src/xml/digital_sign.xml",
        ],
    },
    "external_dependencies": {
        "python": ["xmltodict"]
    },
    "application": False,
    "installable": True,
}
