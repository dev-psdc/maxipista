# -*- coding: utf-8 -*-

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import ValidationError, UserError


class LisRequest(models.Model):
    _name = 'lis.request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Request Laboratory'
    _order = 'name desc'

    name = fields.Char('Request Reference', required=True, index=True, copy=False, default='New')
    state = fields.Selection([
        ('draft', 'New'),
        ('confirmed', 'Confirmed'),
        ('taken', 'Taken'),
        ('in_analysis', 'In Analysis'),
        ('sent', 'Sent'),
        ('cancel', 'Cancelled'),
        ], string='Status', readonly=True, copy=False, index=True, tracking=3, default='draft')
    partner_id = fields.Many2one(
        'res.partner', string='Patient', readonly=True,
        states={'draft': [('readonly', False)]},
        required=True, change_default=True, index=True, tracking=1,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id), ('is_patient', '=', True)]",)
    date_planned = fields.Datetime(string='Planned Date', default=lambda s: fields.Datetime.now(), index=True)
    date_execution = fields.Datetime(string='Execution Date', default=lambda s: fields.Datetime.now(), index=True)
    date_request = fields.Datetime(string='Request Date', default=lambda s: fields.Datetime.now(), index=True)
    date_of_previous_test = fields.Date(string='Date of_ Previous Test', default=fields.Date.context_today)
    note = fields.Text('Note')
    sale_line_id = fields.Many2one('sale.order.line', string='Sales Order Lines', readonly=True, states={'draft': [('readonly', False)]}, required=True, index=True, tracking=1)
    order_id = fields.Many2one(related='sale_line_id.order_id', string='Sale Order', store=True, readonly=True, index=True)
    company_id = fields.Many2one(related='order_id.company_id', string='Company', store=True, readonly=True, index=True)
    product_id = fields.Many2one(related='sale_line_id.product_id', string='Product', store=True, readonly=True, index=True)
    booking_slot_id = fields.Many2one("booking.slot", string="Booking Slot", tracking=1)
    booking_date = fields.Date(string="Booking Date", default=fields.Date.context_today, tracking=1)
    processing_date = fields.Date(string="Processing Date", tracking=1)
    booked_slot_id = fields.Many2one(related="booking_slot_id.time_slot_id", string="Booked Slot", store=True, readonly=True)
    plan_id = fields.Many2one(related='booking_slot_id.plan_id', string='Plan', store=True, readonly=True, index=True)
    sale_order_id = fields.Many2one('sale.order', related='sale_line_id.order_id', string='Order Reference', readonly=False, store=True)
    quantity = fields.Integer(string="Quantity", related='sale_line_id.lis_quantity')
    covid_test = fields.Selection([('yes', 'Si'), ('no', 'No')], string='Covid-19 Test')
    previous_test_result = fields.Selection([('positive', 'Positive'), ('negative', 'Negative')], string='Result of the previous test')
    test_result = fields.Selection([('positive', 'Positive'), ('negative', 'Negative')], string='Test Result')
    traveled = fields.Selection([('yes', 'Si'), ('no', 'No')], string='Traveled', default='no')
    other_symptom = fields.Text('Note')
    symptom_ids = fields.Many2many('lis.symptom', string='Symptom')
    is_fatigue = fields.Boolean(string='Cansancio')
    is_coloration = fields.Boolean(string='Coloración azulada en los labios o el rostro')
    is_confusion = fields.Boolean(string='Confusión o dificultad para estar alerta')
    is_diarrhea = fields.Boolean(string='Diarrea')
    is_abdominal_pain = fields.Boolean(string='Dolor Abdominal')
    is_headache = fields.Boolean(string='Dolor de Cabeza')
    is_chest_pain = fields.Boolean(string='Dolor o Presión constante en el pecho')
    is_muscle_pains = fields.Boolean(string='Dolores Musculares')
    is_shaking_chills = fields.Boolean(string='Escalofrios')
    is_shortness_of_breath = fields.Boolean(string='Falta de aire')
    is_fever = fields.Boolean(string='Fiebre')
    is_irritated_throat = fields.Boolean(string='Garganta Irritada')
    is_lost_of_smell = fields.Boolean(string='Perdida de Olfato')
    is_loss_of_taste = fields.Boolean(string='Perdida del Gusto')
    is_cough = fields.Boolean(string='Tos')
    is_printed = fields.Boolean(string='Has json')
    is_threw_up = fields.Boolean(string='Vomitos')
    lis_max = fields.Integer(related='product_id.lis_max')

    def button_draft(self):
        self.write({'state': 'draft'})
        return {}

    def button_confirmed(self):
        self.write({'state': 'confirmed'})
        return {}

    def button_taken(self):
        self.write({'state': 'taken'})
        return {}

    def button_in_analysis(self):
        self.write({'state': "in_analysis"})
        return {}

    def button_sent(self):
        self.write({'state': 'sent', 'date_execution': fields.Datetime.now()})
        return {}

    def button_cancel(self):
        self.write({'state': 'cancel', 'date_execution': fields.Datetime.now()})
        return {}

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            seq_date = None
            if 'date_planned' in vals:
                seq_date = fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(vals['date_planned']))
            vals['name'] = self.env['ir.sequence'].next_by_code('lis.request', sequence_date=seq_date) or '/'
        return super(LisRequest, self).create(vals)

    @api.constrains('booking_date', 'state')
    def _check_available(self):
        for fy in self:
            booking_date = fy.booking_date
            today = fields.Date.today()
            if fy.state == 'confirmed' and booking_date < today:
                raise ValidationError(_('The booking date must not be prior to the today date.'))

            domain = [
                ('product_id', '=', fy.product_id.id),
                ('booking_date', '=', fy.booking_date),
                ('state', '=', 'confirmed'),
            ]

            requests = self.search_count(domain)
            if requests >= fy.lis_max and self.state == 'confirmed':
                raise ValidationError(_('No more available request for this product, for Date Reserved.') + '\n\n%s' % (requests))



