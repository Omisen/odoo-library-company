{
    # ------ Identity ------
    'name': 'Library',
    'version': '1.0',
    'license': 'LGPL-3',
    'category': 'Services/Library',
    'summary': 'Library Module',
    'author': 'Simone',

    # ------ Dependencies ------
    'depends': ['base', 'mail'],

    # ----- Application ------
    'application': True,
    'installable': True,
    'sequence': 1,
    'web_app_name': 'Library',

    # ----- Data ------
    'data': [
        'security/ir.model.access.csv',
        'data/library_category.xml',
        'data/mail_template_data.xml',
        'data/cron_data.xml',
        'views/library_reservation.xml',
        'views/library_category_view.xml',
        'views/library_loan_view.xml',
        'views/library_book_view.xml',
        'views/library_menu_views.xml',
    ],

    # ----- Assets -----
    'assets': {},

}