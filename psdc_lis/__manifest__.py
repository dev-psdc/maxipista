# -*- coding: utf-8 -*-
{
    'name': "Laboratory Information System",
    'summary': """Laboratory Information System""",
    'description': """Laboratory Information System""",
    'author': "PSDC, INC",
    'website': "http://www.psdc.com",
    'category': 'Administration',
    'version': '1.0',
    'depends': ['base', 'website_booking_system'],
    'data': [
        'security/psdc_lis.xml',
        'security/ir.model.access.csv',
        'data/lis_sequence.xml',
        'views/res_partner.xml',
        'views/request_views.xml',
        'views/sale_order_views.xml',
        'views/product_template_views.xml',
        'views/lis_views.xml',
    ],
}
