{
    'name': 'Matrix widget',

    'author': 'Kitworks Systems',
    'website': 'https://kitworks.systems/',

    'category': 'Extra Tools',
    'license': 'OPL-1',
    'version': '15.0.1.0.2',

    'depends': [
        'web',
    ],
    'images': [
        'static/description/cover.png',
        'static/description/icon.png',
    ],
    'assets': {
        'web.assets_backend': [
            'kw_matrix_widget/static/src/js/matrix.js', ],
        'web.assets_qweb': [
            'kw_matrix_widget/static/src/xml/qweb_matrix_template.xml',
        ],
    },
    'installable': True,
}
