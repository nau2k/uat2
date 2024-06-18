# -*- coding: utf-8 -*-
# module template
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'partner_vn_localization',
    "summary": "Việt Nam Ward, District, Province in Partner",
    "description": "Dữ liệu tỉnh, quận, huyện của VN và thêm các trường tương ứng trong partner",
    "version": "12.0.1.0.1",
    "category": "stock",
    "website": "https://itc-group.vn/",
    "author": "ITC Group",
    "license": "AGPL-3",
    'depends': ['contacts'],
    'images': ['images/main_screenshot.png'],
    'data': [
            'data/province.xml',
            'data/district.xml',
            'data/ward.xml',
            'security/ir.model.access.csv',
            'views/res_partner_view.xml',
            'views/ward.xml',
            'views/district.xml',
            'views/province.xml',
            'views/menu.xml',
    ],
    'installable': True,
    'application': True,
}
