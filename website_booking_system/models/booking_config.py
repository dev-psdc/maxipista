# -*- coding: utf-8 -*-
##########################################################################
# All Rights Reserved.
##########################################################################

from odoo import api, fields, models, _
from odoo.exceptions import Warning, UserError

import math
from datetime import datetime
import logging
_logger = logging.getLogger(__name__)

Days = [
    ('sun','Domingo'),
    ('mon','Lunes'),
    ('tue','Martes'),
    ('wed','Miércoles'),
    ('thu','Jueves'),
    ('fri','Viernes'),
    ('sat','Sábado'),
]


class BookingPlan(models.Model):
    _name = "booking.plan"

    name = fields.Char(string="Name", required=True)
    discription = fields.Html(string="Description", help="Booking plan description.")
    sequence = fields.Integer(help="Determine the display order", default=1)

    def _check_unique_insesitive(self, context=None):
        recs = self.search_count([('name', '=ilike', self.name)])
        if recs > 1:
            return False
        return True

    _constraints = [(_check_unique_insesitive, _('This booking plan is already exist!'), ['name'])]


class BookingTimeSlot(models.Model):
    _name = "booking.time.slot"

    sequence = fields.Integer(help="Determine the display order", default=1)
    start_time = fields.Float(string="De", required=True, help="Introduzca la hora de inicio de atencion.")
    end_time = fields.Float(string="Hasta", required=True, help="Introduzca la hora de final de atencion.")

    # SQL Constraints
    _sql_constraints = [
        ('booking_time_slot_uniq', 'unique(start_time, end_time)', _('This time slot is already exist.'))
    ]

    def float_convert_in_time(self, float_val):
        """Convert any float value in 24 hrs time formate."""
        if float_val < 0:
            float_val = abs(float_val)
        hour = math.floor(float_val)
        min = round((float_val % 1) * 60)
        if min == 60:
            min = 0
            hour = hour + 1
        time = str(hour).zfill(2) + ":" + str(min).zfill(2)
        return time

    def time_convert_in_float(self, time_val):
        """Convert any 24 hrs time fomate value in float."""
        factor = 1;
        if time_val[0] == '-':
            time_val = time_val[1:]
            factor = -1
        float_time_pair = time_val.split(":")
        if len(float_time_pair) != 2:
            return factor*float(time_val)
        hours = int(float_time_pair[0])
        minutes = int(float_time_pair[1])
        return factor * round((hours + (minutes / 60)),2)

    def name_get(self):
        """Return: [(id, start_time-end_time)],
            e.g-[(1, 1:00-3:00)]"""
        result = []
        for rec in self:
            name = self.float_convert_in_time(rec.start_time) + '-' + self.float_convert_in_time(rec.end_time)
            result.append((rec.id, name))
        return result

    def check_time_values(self, vals):
        start_time = vals.get('start_time') if vals.get('start_time', None) != None else self.start_time
        end_time = vals.get('end_time') if vals.get('end_time', None) != None else self.end_time
        if start_time >= 24 or start_time < 0:
            raise UserError(_("Please enter a valid hour between 00:00 and 24:00"))
        if end_time >= 24 or end_time < 0:
            raise UserError(_("Please enter a valid hour between 00:00 and 24:00"))
        if start_time >= end_time:
            raise UserError(_("Please enter a valid start and end time."))
        same_objs = self.search([('start_time','=',start_time),('end_time','=',end_time)])
        if len(same_objs.ids) > 0:
            raise UserError(_("Record already exist with same timing."))

    @api.model
    def create(self, vals):
        self.check_time_values(vals)
        res = super(BookingTimeSlot, self).create(vals)
        return res

    def write(self, vals):
        if vals.get('start_time', None) != None and vals.get('end_time', None) != None:
            self.check_time_values(vals)
        elif vals.get('start_time', None) != None or vals.get('end_time', None) != None:
            for rec in self:
                rec.check_time_values(vals)
        res = super(BookingTimeSlot, self).write(vals)
        return res


class BookingSlotConfig(models.Model):
    _name = "day.slot.config"

    name = fields.Selection(selection=Days, string="Día", required=True)
    booking_status = fields.Selection(selection=[('open','Abierto'),('closed','Cerrado')], string="Estado(Abierto/Cerrado)", required=True, help="Select booking status for the day(Closed/Open).", default="open")
    booking_slots_ids = fields.One2many("booking.slot", "slot_config_id", string="Horas/Ubicaciones ", help="Add booking slots for the day.")
    product_id = fields.Many2one("product.template", string="Product")

    # SQL Constraints
    _sql_constraints = [
        ('booking_day_uniq', 'unique(name, product_id)', _("Record already exist, you can't create multiple records for the same day."))
    ]

    # @api.onchange('booking_slots_ids')
    # def validate_slot_plan(self):
    #     if self.booking_slots_ids:
    #         saved_data = self.env["booking.slot"].browse(self.booking_slots_ids.ids)
    #         print("saved data")
    #         print(saved_data)
    #         new_data = self.booking_slots_ids - saved_data
    #         print("new Data")
    #         print(new_data)
    #         for rec in new_data:
    #             print(rec)
    #             if rec.time_slot_id and rec.plan_id:
    #                 x = saved_data.filtered(lambda l: l.time_slot_id == rec.time_slot_id and l.plan_id == rec.plan_id)
    #                 # x = saved_data.filtered(lambda l: l.time_slot_id == rec.time_slot_id and l.plan_id == rec.plan_id)
    #                 if len(x) > 0:
    #                     raise UserError(_("Record already exist with same time slot and plan."))


class BookingSlot(models.Model):
    _name = "booking.slot"

    time_slot_id = fields.Many2one("booking.time.slot", required=True, string="Horas")
    plan_id = fields.Many2one("booking.plan", required=True, string="Ubicación")
    quantity = fields.Integer(string="Cantidad de citas")
    price = fields.Float(string="Precio", required=True)
    slot_config_id = fields.Many2one("day.slot.config", string="Day Slot Config")
    line_ids = fields.One2many("sale.order.line", "booking_slot_id", string="Booking Orders")

    def name_get(self):
        result = []
        for rec in self:
            name = rec.time_slot_id.name_get()[0][1] + ',' + rec.plan_id.name
            result.append((rec.id, name))
        return result

    def _check_unique_slot_plan(self, context=None):
        for rec in self:
            recs = self.search_count([('time_slot_id', '=', rec.time_slot_id.id), ('plan_id', '=', rec.plan_id.id), ('slot_config_id', '=', rec.slot_config_id.id)])
            if recs > 1:
                return False
            return True

    _constraints = [(_check_unique_slot_plan, _('This booking slot is already exist.'), ['time_slot_id', 'plan_id', 'slot_config_id'])]


class BookingConfig(models.Model):
    _name = "booking.config"

    day = fields.Selection(selection=Days, string="Día")
    start_time = fields.Float("Start Time")
    end_time = fields.Float("End Time")
    time_slot = fields.Integer("Slot time duration")
    buffer_cache = fields.Integer("Buffer cache time after each booking")
    br_start_time = fields.Float("Break Start Time")
    br_end_time = fields.Float("Break End Time")
    product__id = fields.Many2one("product.template", string="Bookng Product")



