# -*- coding: utf-8 -*-
# from odoo import http


# class PsdcLis(http.Controller):
#     @http.route('/psdc_lis/psdc_lis/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/psdc_lis/psdc_lis/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('psdc_lis.listing', {
#             'root': '/psdc_lis/psdc_lis',
#             'objects': http.request.env['psdc_lis.psdc_lis'].search([]),
#         })

#     @http.route('/psdc_lis/psdc_lis/objects/<model("psdc_lis.psdc_lis"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('psdc_lis.object', {
#             'object': obj
#         })
