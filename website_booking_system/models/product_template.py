# -*- coding: utf-8 -*-
##########################################################################
# Author      : Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# Copyright(c): 2016-Present Webkul Software Pvt. Ltd.
# All Rights Reserved.
#
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
# License URL :<https://store.webkul.com/license.html/>
##########################################################################

from odoo import api, fields, models, _
from odoo.exceptions import Warning, UserError
from dateutil.relativedelta import relativedelta
import datetime, pytz

import logging
_logger = logging.getLogger(__name__)

Days = {
    0 : 'mon',
    1 : 'tue',
    2 : 'wed',
    3 : 'thu',
    4 : 'fri',
    5 : 'sat',
    6 : 'sun',
}


class Website(models.Model):
    _inherit = 'website'

    @api.model
    def bk_products_validation(self):
        """"Check any sold out product of booking type is in the cart or not."""
        order = self.sale_get_order()
        if order:
            order_lines = order.website_order_line
            for line in order_lines:
                product_obj = line.product_id.product_tmpl_id
                if product_obj.is_booking_type:
                    av_qty = product_obj.get_bk_slot_available_qty(line.booking_date, line.booking_slot_id.id)
                    if av_qty < 0:
                        break
            else:
                return True
        return False


class SaleOrder(models.Model):
    _inherit = "sale.order"

    is_booking_type = fields.Boolean(string="Citas")
    payment_start_date = fields.Datetime("Payment initiated time")

    def check_active_bk_transactions(self):
        self.ensure_one()
        active_trans = self.transaction_ids.filtered(lambda l: l.state in ['pending', 'authorized', 'done'])
        if active_trans:
            return True
        return False

    @api.onchange('order_line')
    def compute_booking_type(self):
        for rec in self:
            if rec.order_line:
                if any(line.product_id.is_booking_type == True for line in rec.order_line):
                    rec.is_booking_type = True


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    booking_slot_id = fields.Many2one("booking.slot", string="Hora/Ubicación disponible")
    # Booking Slot
    booking_date = fields.Date(string="Fecha de cita")
    # Booking Date
    booked_slot_id = fields.Many2one(related="booking_slot_id.time_slot_id", string="Horarios", store=True)
    booked_plan_id = fields.Many2one(related="booking_slot_id.plan_id", string="Ubicaciones", store=True)
    patient_name = fields.Char(string='Patient Name')
    ruc = fields.Char(string='Identification Card')
    covid_test = fields.Selection([('yes', 'Yes'), ('no', 'No')], string='Covid-19 Test', default='no')
    traveled = fields.Selection([('yes', 'Yes'), ('no', 'No')], string='Traveled', default='no')
    other_symptom = fields.Text('Note')
    symptom_ids = fields.Many2many('lis.symptom', relation='sale_order_line_symptom_rel', string='Symptom')
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
    is_threw_up = fields.Boolean(string='Vomitos')
    patient_id = fields.Many2one('res.partner', string='Patient')
    previous_test_result = fields.Selection([('positive', 'Positive'), ('negative', 'Negative')],
                                            string='Result of the previous test')
    test_result = fields.Selection([('positive', 'Positive'), ('negative', 'Negative')], string='Test Result')
    date_of_previous_test = fields.Date(string='Date of_ Previous Test', default=fields.Date.context_today)

    @api.depends('product_id', 'booking_date', 'booking_slot_id')
    def compute_booking_line_name(self):
        for rec in self:
            rec.name = ''
            product_obj = rec.product_id or False
            if product_obj and product_obj.is_booking_type:
                name = "Booking for " + product_obj.name
                if rec.booking_date:
                    name += " on " + str(rec.booking_date)
                if rec.booking_slot_id:
                    name += " (" + rec.booking_slot_id.name_get()[0][1] + ")"
                rec.name = name
        return

    @api.model
    def create(self, vals):
        _logger.info("~~~1~~~~~create~~~~~~~~~~~%r~~~~~~~~~~~~",vals)
        res = super(SaleOrderLine, self).create(vals)
        res.compute_booking_line_name()
        return res

    def write(self, vals):
        _logger.info("~~~1~~~~~booking_date~~~~~~~~~~~%r~~~~~~~~~~~~",vals)
        res = super(SaleOrderLine, self).write(vals)
        _logger.info("~~~~2~~~~booking_date~~~~~~~~~~~%r~~~~~~~~~~~~",vals.get('booking_date'))
        if vals.get('booking_date') or vals.get('booking_slot_id') or vals.get('product_id'):
            self.compute_booking_line_name()
        return res

    @api.onchange('product_id','booking_date','booking_slot_id')
    def booking_values_change(self):
        for rec in self:
            rec.compute_booking_line_name()
        return

    def _get_display_price(self, product):
        for rec in self:
            if rec.booking_slot_id:
                return rec.booking_slot_id.with_context(pricelist=self.order_id.pricelist_id.id).price
        return super(SaleOrderLine, self)._get_display_price(product)

    @api.model
    def remove_booking_product_draft_order_lines(self):
        bk_orders = self.search([('state','=','draft'),('booking_slot_id','!=',None)])
        for so in bk_orders:
            sale_order = so.order_id
            payment_start_date = sale_order.payment_start_date
            rd = relativedelta(datetime.datetime.now(), so.create_date)
            if not payment_start_date:
                if rd.minutes > 5:
                    so.unlink();
            else:
                prd = relativedelta(datetime.datetime.now(), payment_start_date)
                if prd.minutes > 10:
                    if not sale_order.check_active_bk_transactions():
                        so.unlink();
                        sale_order.compute_booking_type()
                        if not sale_order.is_booking_type:
                            sale_order.payment_start_date = None


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_booking_type = fields.Boolean("Disponible para agendar")
    br_start_date = fields.Date("Fecha de inicio")
    br_end_date = fields.Date("Fecha final")
    # max_bk_qty = fields.Integer("Max Booking Qty")
    booking_day_slot_ids = fields.One2many("day.slot.config", "product_id", string="Configurar horas/ubicaciones por dia")

    def get_available_bk_qty(self):
        for rec in self:
            context = dict(rec._context) or {}
            context['active_id'] = rec.id
            return {
                'name':'Citas disponibles por día',
                # Booking Available Quantity
                'type':'ir.actions.act_window',
                'res_model':'booking.quantity.wizard',
                'view_mode':'form',
                # 'view_type':'form',
                'view_id':rec.env.ref('website_booking_system.booking_available_quantity_wizard_form_view').id,
                'context' : context,
                'target':'new',
            }

    @api.model
    def get_bk_slot_available_qty(self, bk_date, slot_plan_id):
        """ Return: Total quantity available on a particular date in a provided slot.
            bk_date: Date on with quantity will be calculated.
            slot_plan_id: Plan in any slot on with quantity will be calculated."""
        slot_plan_obj = self.env["booking.slot"].browse([int(slot_plan_id)])
        sol_objs = slot_plan_obj.line_ids.filtered(lambda line: line.booking_date == bk_date).mapped('product_uom_qty')
        return slot_plan_obj.quantity - sum(sol_objs)

    def get_bk_open_closed_days(self, state):
        """State : State of the booking product(open/closed).
            Return: List of days of the week on the basis of state.
            e.g.-['mon','tue','sun']"""
        bk_open_days = self.booking_day_slot_ids.filtered(lambda day_sl: day_sl.booking_status == 'open' and len(day_sl.booking_slots_ids)).mapped('name')
        if state == 'open':
            return bk_open_days
        else:
            bk_closed_days = list(set(Days.values()) - set(bk_open_days))
            return bk_closed_days

    @api.model
    def get_available_day_slots(self, slots, sel_date):
        av_slots = []
        if sel_date and slots:
            rd = relativedelta(datetime.date.today(), sel_date)
            if rd.days == 0 and rd.months == 0 and rd.years == 0:
                for slot in slots:
                    start_time = slot.start_time
                    start_time = slot.float_convert_in_time(start_time)
                    current_time = datetime.datetime.now().replace(microsecond=0).replace(second=0)
                    user_tz = pytz.timezone(self.env.user.tz or 'UTC')
                    current_time = pytz.utc.localize(current_time).astimezone(user_tz)
                    hour = int(start_time.split(":")[0])
                    min = int(start_time.split(":")[1])
                    if hour > current_time.hour or (hour == current_time.hour and min > current_time.minute):
                        av_slots.append(slot)
                return av_slots
        return slots

    def get_booking_slot_for_day(self, sel_date):
        """Return: List of slots and their plans with qty and price of a day"""
        self.ensure_one()
        day = Days[sel_date.weekday()]
        day_config = self.booking_day_slot_ids.filtered(lambda day_sl: day_sl.name == day and day_sl.booking_status == 'open')
        day_slots = day_config.booking_slots_ids
        time_slots = day_slots.mapped('time_slot_id')
        time_slots = self.get_available_day_slots(time_slots, sel_date)
        slots_plans_list = []
        for slot in time_slots:
            d1 = {}
            d2 = []
            d1['slot'] = {
                'name' : slot.name_get()[0][1],
                'id' : slot.id,
            }
            d_slots = day_slots.filtered(lambda r: r.time_slot_id.id == slot.id)
            for d in d_slots:
                d2.append({
                    'name' : d.plan_id.name,
                    'id' : d.id,
                    'qty' : d.quantity,
                    'price' : d.price,
                })
            d1['plans'] = d2
            slots_plans_list.append(d1)
        return slots_plans_list

    def get_booking_onwards_price(self):
        """Return: Minimum price of a booking product available in any slot."""
        self.ensure_one()
        prices = sorted(self.booking_day_slot_ids.mapped('booking_slots_ids.price'))
        return prices[0] if prices else 0

    @api.onchange('br_start_date')
    def booking_start_date_validation(self):
        self.validate_booking_dates(start_date=self.br_start_date)

    @api.onchange('br_end_date')
    def booking_end_date_validation(self):
        self.validate_booking_dates(end_date=self.br_end_date)

    @api.onchange('is_booking_type')
    def update_product_type_for_booking(self):
        if self.is_booking_type:
            self.type = 'service'

    def validate_booking_dates(self, start_date=None, end_date=None):
        if type(start_date) == str:
            start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()
        if type(end_date) == str:
            end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d').date()
        current_date = fields.Date.today()
        if start_date and end_date:
            if start_date < current_date:
                raise UserError(_("Por favor seleccione una fecha de inicio correcta, la fecha de inicio no debe ser anterior a la fecha actual."))
            if end_date < start_date:
                raise UserError(_("Por favor seleccione una fecha final correcta, la fecha final no debe ser anterior a la fecha de inicio."))
            return True
        if start_date:
            if start_date < current_date:
                raise UserError(_("Por favor seleccione una fecha de inicio correcta, la fecha de inicio no debe ser anterior a la fecha actual."))
            if self.br_end_date and start_date > self.br_end_date:
                raise UserError(_("Por favor seleccione una fecha de inicio correcta, la fecha de inicio no debe ser posterior a la fecha final."))
            return True
        if end_date:
            if end_date < current_date:
                raise UserError(_("Por favor seleccione una fecha final correcta, la fecha final no debe ser anterior a la fecha actual."))
            if self.br_start_date and end_date < self.br_start_date:
                raise UserError(_("Por favor seleccione una fecha final correcta, la fecha final no debe ser anterior a la fecha de inicio."))
            return True

    @api.model
    def create(self, vals):
        self.validate_booking_dates(vals.get("br_start_date"), vals.get("br_end_date"))
        return super(ProductTemplate, self).create(vals)

    def write(self, vals):
        for rec in self:
            rec.validate_booking_dates(vals.get("br_start_date"), vals.get("br_end_date"))
        return super(ProductTemplate, self).write(vals)


class LisSymptom(models.Model):
    _name = 'lis.symptom'
    _description = 'Symptom'
    _order = 'name asc'

    name = fields.Char('Symptom', required=True)
    color = fields.Integer('Color')

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "Symptom name already exists !"),
    ]