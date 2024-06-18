# -*- encoding: utf-8 -*-
{
    'name': 'Aeroo Reports',
    'category': 'Tools',
    'author': 'Quanvm00 ',
    'description': '''
    ''',
    'depends': ['base'],
    'external_dependencies': {
        'python': [
            'tempfile',
            'subprocess'
        ],
    },
    'data': [
        "security/ir.model.access.csv",
        
        "data/report_aeroo_data.xml", 
        
        "views/report_view.xml",
        "views/report_print_by_action.xml",
        "views/installer.xml",
        'views/template.xml',
    ],
    'assets':{
      'web.assets_backend':['report_aeroo/static/src/js/action_manager_report.js',],
     },
    'license': 'LGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False,
}
