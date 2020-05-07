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

from odoo import models, fields, api, _
from datetime import date, timedelta, datetime
from lxml import etree
from odoo.exceptions import UserError
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

class BookingQuantity(models.TransientModel):
    _name="booking.quantity.wizard"

    @api.model
    def default_get(self,default_fields):
        res = super(BookingQuantity, self).default_get(default_fields)
        product_obj = self.env['product.template'].browse(self._context.get('active_id'))
        if product_obj and product_obj.is_booking_type:
            res['bk_product_id'] = product_obj.id
        return res

    bk_date = fields.Date("Fecha de cita", required=True)
    # Booking Date
    bk_product_id = fields.Many2one("product.template", required=True, string="Producto para agendar")
    # Booking Product
    bk_av_qty = fields.Integer(string="Available Booking Quantity")
    time_slot_id = fields.Many2one("booking.time.slot", string="Time Slot")
    plan_id = fields.Many2one("booking.plan", string="Booking Plan")
    booking_slot_id = fields.Many2one("booking.slot", required=True, string="Booking Slot")

    @api.onchange('bk_date')
    def update_bk_slots_domain(self):
        bk_product = self.bk_product_id
        if bk_product and self.bk_date:
            slot_plan_ids = []
            start_date = datetime.strptime(str(bk_product.br_start_date),'%Y-%m-%d').date()
            end_date = datetime.strptime(str(bk_product.br_end_date),'%Y-%m-%d').date()
            bk_date = datetime.strptime(str(self.bk_date),'%Y-%m-%d').date()
            if bk_date < start_date or bk_date > end_date:
                raise UserError(_("Selected Date is beyond the configured start and end date."))
            if start_date <= bk_date and bk_date <= end_date:
                bk_day = Days[bk_date.weekday()]
                slot_plan_objs = bk_product.booking_day_slot_ids.filtered(lambda day_sl: day_sl.name == bk_day and day_sl.booking_status == 'open').mapped('booking_slots_ids')
                slot_plan_ids = slot_plan_objs.ids if slot_plan_objs else slot_plan_ids
            domain = [('id', 'in', slot_plan_ids)]
            self.booking_slot_id = None
            return {'domain': {'booking_slot_id': domain }}

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(BookingQuantity, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        product_obj = self.env['product.template'].browse(self._context.get('active_id'))
        slot_plan_ids = product_obj.booking_day_slot_ids.filtered(lambda day_sl: day_sl.booking_status == 'open').mapped('booking_slots_ids')
        slot_plan_ids = slot_plan_ids.ids if slot_plan_ids else []

        doc = etree.XML(res['arch'])
        for node in doc.xpath("//field[@name='booking_slot_id']"):
            node.set(
                'domain', "[('id', 'in', %s)]" % slot_plan_ids)
        res['arch'] = etree.tostring(doc)
        return res

    def get_bk_available_qty(self):
        bk_date = self.bk_date
        product_obj = self.bk_product_id
        plan_slot_obj = self.booking_slot_id
        if bk_date and plan_slot_obj:
            data = product_obj.get_bk_slot_available_qty(bk_date, plan_slot_obj.id)
            self.bk_av_qty = int(data)
            context = dict(self._context) or {}
            context["is_done"] = True
            return {
                'name':'Citas disponibles por día',
                # Booking Available Quantity
                'type':'ir.actions.act_window',
                'res_model':'booking.quantity.wizard',
                'view_mode':'form',
                'view_type':'form',
                'res_id': self.id,
                'view_id':self.env.ref('website_booking_system.booking_available_quantity_wizard_form_view').id,
                'context' : context,
                'target':'new',
            }
