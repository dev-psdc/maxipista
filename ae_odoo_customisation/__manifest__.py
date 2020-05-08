# -*- coding: utf-8 -*-
{
    'name': 'Customisation for odoo',
    'version': '12.0.1.0.0',
    'author': 'Ascents Entrepreneurs',
    'license': 'OPL-1',
    'category': 'Tools',
    'summary': 'Customisation for odoo',
    'description': """
Customisation for odoo
----------------------
1. Add fields in signup form
2. Country-State-District Validations
""",
    'depends': ['auth_signup', 'website_sale', 'neonety', 'website_booking_system'],
    'data': [
        'views/templates.xml',
        'views/auth_signup_templates.xml',
    ],
    'installable': True,
    'auto_install': False,
}
