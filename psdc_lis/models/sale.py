# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    lis_count = fields.Integer(string='Request Lab Count', compute='_get_lis_request', readonly=True)
    order_line_count = fields.Integer("Number of generated sale items", compute='_compute_line_count')

    def _compute_line_count(self):
        Line = self.env['sale.order.line']
        for record in self:
            record.order_line_count = Line.search_count([('order_id', '=', record.id)])

    def _get_lis_request(self):
        request = self.env['lis.request']
        for lis in self:
            self.lis_count = request.search_count([('order_id', '=', lis.id)])

    def action_view_request(self):
        return {
            'domain': "[('order_id','in',[" + ','.join(map(str, self.ids)) + "])]",
            'name': _('Lab Request'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'lis.request',
            'type': 'ir.actions.act_window',
            'target': 'current',
        }

    def _action_confirm(self):
        result = super(SaleOrder, self)._action_confirm()
        order_line = self.env['sale.order.line'].search([('order_id', '=', self.id)])
        for order in order_line:
            for line in order:
                if line.product_id.is_product_lab == True:
                    line.sudo().action_create_lis_request()
        return result


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    lis_request_line = fields.One2many('lis.request', 'sale_line_id', string='Lab Request Lines', states={'cancel': [('readonly', True)], 'done': [('readonly', True)]}, copy=True)
    lis_quantity = fields.Integer(string="Quantity", compute='_compute_quantity')
    order_line_count = fields.Integer("Number of generated sale items", related='order_id.order_line_count')

    @api.depends('product_uom_qty')
    def _compute_quantity(self):
        if self.product_uom_qty:
            self.lis_quantity = int(float(self.product_uom_qty))

    # def write(self, values):
    #   self._action_create_lis_request()
    #    return super(SaleOrderLine, self).write(values)

    # def write(self, vals):
    #   res = super(SaleOrderLine, self).write(vals)
    #    res.action_create_lis_request()
    #   return res

    def action_create_lis_request(self):
        for res in self:
            quantity = int(float(self.product_uom_qty))
            if quantity > 0:
                for i in range(quantity):
                    self.env['lis.request'].create({
                        'sale_line_id': res.id,
                        'date_planned': self.create_date,
                        'date_request': self.create_date,
                        'date_execution': self.create_date,
                        'booking_date': self.booking_date,
                        'note': self.name,
                        'booking_slot_id': self.booking_slot_id.id,
                        'other_symptom': self.other_symptom,
                        'covid_test': self.covid_test,
                        'traveled': self.traveled,
                        'state': 'draft',
                        'previous_test_result': self.previous_test_result,
                        'date_of_previous_test': self.date_of_previous_test,
                        'partner_id': self.patient_id.id if self.patient_id.id else self.order_partner_id.id,
                    })
