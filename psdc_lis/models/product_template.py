# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_product_lab = fields.Boolean("Laboratory Product")
    lab_req_qty = fields.Integer(string="Laboratory Request Quantity per Day")

    request_ids = fields.One2many('lis.request', 'product_id', string='Requests')
    lis_availability = fields.Selection([('limited', 'Limited'), ('unlimited', 'Unlimited')], string='Available Request', required=True, store=True, compute='_compute_lis', default="limited")
    lis_max = fields.Integer(string='Maximum Available Requests')

    @api.depends('lis_max', 'request_ids.state')
    def _compute_lis(self):
        # initialize fields to 0 + compute lis availability
        for request in self:
            request.lis_availability = 'unlimited' if request.lis_max == 0 else 'limited'

