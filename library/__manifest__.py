{
    # ------ Identity ------
    'name': 'Library',
    'version': '1.0',
    'license': 'LGPL-3',
    'category': '',
    'summary': 'Library Module',
    'author': 'Simone',

    # ------ Dependencies ------
    'depends': ['base',],

    # ----- Application ------
    'application': True,
    'installable': True,
    'sequence': 1,
    'web_app_name': 'Real Estate',

    # ----- Data ------
    'data': [
        'security/ir.model.access.csv',
    ],

    # ----- Assets -----
    'assets': {},

}