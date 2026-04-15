{
    # ------ Identity ------
    'name': 'Library',
    'version': '1.0',
    'license': 'LGPL-3',
    'category': 'Services/Library',
    'summary': 'Library Module',
    'author': 'Simone',

    # ------ Dependencies ------
    'depends': ['base',],

    # ----- Application ------
    'application': True,
    'installable': True,
    'sequence': 1,
    'web_app_name': 'Library',

    # ----- Data ------
    'data': [
        'security/ir.model.access.csv',
        'data/library_category.xml',
        'views/library_book_view.xml',
        'views/library_category_view.xml',
        'views/library_menu_views.xml',
    ],

    # ----- Assets -----
    'assets': {},

}