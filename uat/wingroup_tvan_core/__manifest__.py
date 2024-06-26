# -*- coding: utf-8 -*-
{
    "name": "Tvan core",
    "summary": "Tvan core",
    "version": "15.0.1.0.1",
    "category": "account",
    "website": "https://latido.vn",
    "author": "LATIDO JSC, Trình Gia Lạc",
    "license": "OPL-1",
    "depends": [
        "partner_vn_localization", "wingroup_lib", "sale", "sequence_reset_period"
    ],
    "data": [
        'security/ir.model.access.csv',
        # "data/xml_template_01_data.xml",
        # "data/xml_template_inv_data.xml",
        "data/ir_config_parameter.xml",
        "data/tvan_info_data.xml",
        "data/tvan_sign_display_data.xml",
        "data/tvan_report_server_data.xml",
        "wizards/export_summary_inv_view.xml",
        "wizards/export_misa_inv_view.xml",
        "wizards/create_partner_view.xml",
        "wizards/tvan_inv_adjust_wiz_view.xml",
        "views/xml_template_view.xml",
        "views/product_view.xml",
        "views/company_view.xml",
        "views/partner_view.xml",
        "views/tvan_registry_view.xml",
        "views/tvan_cks_info_view.xml",
        "views/tvan_inv_error_view.xml",
        "views/tvan_inv_template_view.xml",
        "views/tvan_contract_view.xml",
        "views/tvan_inv_sample_data_view.xml",
        "views/tvan_inv_serial_view.xml",
        "views/tvan_inv_sequence_view.xml",
        "views/cqt_view.xml",
        "views/tvan_view.xml",
        "views/sale_view.xml",
        # "views/account_move_view.xml",
        "views/invoice_view.xml",
        "reports/report_view.xml",
        "views/menu_view.xml",
    ],
    "external_dependencies" : {
        "python" : ["json2xml"],
    },
    "application": True,
    "installable": True,
}
