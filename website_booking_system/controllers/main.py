# -*- coding: utf-8 -*-
#################################################################################
# Author      : Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# Copyright(c): 2015-Present Webkul Software Pvt. Ltd.
# License URL : https://store.webkul.com/license.html/
# All Rights Reserved.
#
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
# If not, see <https://store.webkul.com/license.html/>
#################################################################################
from odoo import api, http, tools, _
from odoo.http import request
from datetime import date, timedelta, datetime
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.tools import float_compare, date_utils

import ast
import json
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


class WebsiteSale(WebsiteSale):

    @http.route(['/shop/cart/update'], type='http', auth="public", methods=['POST'], website=True, csrf=False)
    def cart_update(self, product_id, add_qty=1, set_qty=0, **kw):
        res = super(WebsiteSale, self).cart_update(product_id, add_qty, set_qty)
        bk_plan = kw.get('bk_plan', False)
        bk_date = kw.get('bk_date', False)
        bk_covid_test = kw.get('bk_covid_test', False)
        bk_patient_name = kw.get('bk_patient_name', False)
        bk_id_card = kw.get('bk_id_card', False)
        bk_other_symptom = kw.get('bk_other_symptom', False)
        bk_previous_test_result = kw.get('bk_previous_test_result', False)
        bk_date_of_previous_test = kw.get('bk_date_of_previous_test', False)
        bk_birthday = kw.get('bk_birthday', False)
        bk_email = kw.get('bk_email', False)
        country = kw.get('country_id', False)
        province = kw.get('province_id', False)
        district = kw.get('district_id', False)
        sector = kw.get('sector_id', False)
        region = kw.get('region_id', False)
        sex = kw.get('sex', False)

        if bk_plan:
            bk_slot_obj = request.env["booking.slot"].browse([int(bk_plan)])
            sale_order = request.website.sale_get_order()
            order_line = sale_order.order_line.filtered(lambda l: l.product_id.id == int(product_id))
            order_line.write({
                'booking_slot_id': bk_slot_obj.id,
                'price_unit': bk_slot_obj.price,
                'booking_date': bk_date if bk_date else None,
                'patient_name': bk_patient_name,
                'ruc': bk_id_card,
                'covid_test': bk_covid_test,
                'other_symptom': bk_other_symptom,
                'previous_test_result': bk_previous_test_result,
                'date_of_previous_test': bk_date_of_previous_test,
            })
            sale_order.write({
                'is_booking_type': True,
            })

            patient = request.env['res.partner'].sudo().search([('ruc', '=', bk_id_card)])
            if patient:
                patient_id = patient
            else:
                partner = request.env['res.partner']
                patient_id = partner.sudo().create({
                    'name': bk_patient_name,
                    'ruc': bk_id_card,
                    'is_patient': True,
                    'birth_date': bk_birthday if bk_date else None,
                    'email': bk_email,
                    'country_id': country,
                    'province_id': province,
                    'district_id': district,
                    'sector_id': sector,
                    'region_id': region,
                    'sex': sex,
                }).id

            order_line.write({
                'patient_id': patient_id,
            })
        return res

    @http.route(['/shop/checkout'], type='http', auth="public", website=True)
    def checkout(self, **post):
        check = request.website.bk_products_validation()
        if not check:
            return request.redirect("/shop/cart")
        return super(WebsiteSale, self).checkout(**post)

    @http.route(['/shop/payment'], type='http', auth="public", website=True)
    def payment(self, **post):
        check = request.website.bk_products_validation()
        if not check:
            return request.redirect("/shop/cart")
        order = request.website.sale_get_order()
        if order:
            order.payment_start_date = datetime.now()
        return super(WebsiteSale, self).payment(**post)


class BookingReservation(http.Controller):

    def get_all_week_days(self, sel_date, product_obj):
        """Return all week day,date list for the selected date"""
        bk_open_days = product_obj.get_bk_open_closed_days("open")
        if not bk_open_days:
            return False
        week_days = [None]*7
        end_date = product_obj.br_end_date
        current_date = self.get_default_date(product_obj.id)
        day = sel_date.weekday()
        v_date = sel_date - timedelta(days=day)
        for w_day in week_days:
            day = v_date.weekday()
            week_days[day] = {
                "day" : Days[day],
                "date_str" : datetime.strftime(v_date,'%d %b %Y'),
                "date" : datetime.strftime(v_date,'%Y-%m-%d'),
                "state" : "active" if current_date <= v_date and v_date <= end_date and Days[day] in bk_open_days else "inactive",
            }
            v_date = v_date + timedelta(days=1)
        return week_days

    # Update slots on week day selection
    @http.route(['/booking/reservation/update/slots'], type='json', auth="public", methods=['POST'], website=True)
    def booking_reservation_update_slots(self,**post):
        w_day = post.get('w_day',False)
        w_date = post.get('w_date',False)
        w_date = datetime.strptime(w_date,'%Y-%m-%d').date()
        product_id = post.get('product_id',False)

        if not product_id:
            return False
        product_obj = request.env["product.template"].browse(product_id)
        current_day_slots = product_obj.get_booking_slot_for_day(w_date)
        country = request.env['res.country'].sudo().search([])
        province = request.env['neonety.province'].sudo().search([])
        district = request.env['neonety.district'].sudo().search([])
        sector = request.env['neonety.sector'].sudo().search([])
        region = request.env['neonety.region'].sudo().search([])

        values = {
            'day_slots' : current_day_slots,
            'current_date' : w_date,
            'product' : product_obj,
            'country': country,
            'province': province,
            'district': district,
            'sector': sector,
            'region': region,
        }
        return request.env.ref("website_booking_system.booking_modal_bk_slots_n_plans_div").render(values, engine='ir.qweb')

    # Update plans on slot selection
    @http.route(['/booking/reservation/slot/plans'], type='json', auth="public", methods=['POST'], website=True)
    def booking_reservation_slot_plans(self,**post):
        sel_date = post.get('sel_date', False)
        sel_date = datetime.strptime(sel_date, '%Y-%m-%d').date()
        time_slot_id = post.get('time_slot_id', False)
        slot_plans = post.get('slot_plans', False)
        product_id = post.get('product_id', False)
        product_obj = request.env["product.template"].browse(product_id);
        slot_plans = ast.literal_eval(slot_plans)
        country = request.env['res.country'].sudo().search([])
        province = request.env['neonety.province'].sudo().search([])
        district = request.env['neonety.district'].sudo().search([])
        sector = request.env['neonety.sector'].sudo().search([])
        region = request.env['neonety.region'].sudo().search([])

        values = {
            'd_plans': slot_plans,
            'current_date': sel_date,
            'product': product_obj,
            'country': country,
            'province': province,
            'district': district,
            'sector': sector,
            'region': region,
        }
        return request.env.ref("website_booking_system.booking_sel_plans").render(values, engine='ir.qweb')

    def get_default_date(self, product_id):
        product_obj = request.env["product.template"].browse(product_id);
        w_open_days = product_obj.get_bk_open_closed_days("open")
        if not w_open_days:
            return False
        current_date = date.today()
        start_date = product_obj.br_start_date
        end_date = product_obj.br_end_date
        if end_date < current_date:
            return False
        elif current_date < start_date:
            current_date = start_date
        current_day = Days[current_date.weekday()]
        if current_day in w_open_days:
            return current_date
        while(current_day not in w_open_days):
            current_date = current_date + timedelta(days=1)
            current_day = Days[current_date.weekday()]
            if end_date < current_date:
                return False
        return current_date

    # Append booking Pop-Up modal
    @http.route(['/booking/reservation/modal'], type='json', auth="public", methods=['POST'], website=True)
    def booking_reservation_modal(self,**post):
        product_id = post.get('product_id',False)
        if not product_id:
            return False
        product_obj = request.env["product.template"].browse(product_id)
        values = {
            'booking_status' : False
        }
        current_date = self.get_default_date(product_id)
        if current_date:
            week_days = self.get_all_week_days(current_date, product_obj)
            current_day = Days[current_date.weekday()]
            end_date = product_obj.br_end_date
            current_day_slots = product_obj.get_booking_slot_for_day(current_date)
            w_closed_days = product_obj.get_bk_open_closed_days("closed")

            values.update({
                'booking_status' : True,
                'product' : product_obj,
                'week_days' : week_days,
                'w_closed_days' : json.dumps(w_closed_days),
                'current_day' : current_day,
                'current_date' : current_date,
                'day_slots' : current_day_slots,
                'end_date' : end_date,
                'default_date' : current_date,
            })
        return request.env.ref("website_booking_system.booking_and_reservation_modal_temp").render(values, engine='ir.qweb')

    # Update booking modal on date selection
    @http.route(['/booking/reservation/modal/update'], type='json', auth="public", methods=['POST'], website=True)
    def booking_reservation_modal_update(self,**post):
        product_id = post.get('product_id',False)
        new_date = post.get('new_date',False)
        if not product_id:
            return False
        product_obj = request.env["product.template"].browse(product_id);
        new_date = datetime.strptime(new_date,'%d/%m/%Y').date()
        end_date = product_obj.br_end_date

        week_days = self.get_all_week_days(new_date, product_obj)
        current_day = Days[new_date.weekday()]
        current_day_slots = product_obj.get_booking_slot_for_day(new_date)

        country = request.env['res.country'].sudo().search([])
        province = request.env['neonety.province'].sudo().search([])
        district = request.env['neonety.district'].sudo().search([])
        sector = request.env['neonety.sector'].sudo().search([])
        region = request.env['neonety.region'].sudo().search([])

        values = {
            'product': product_obj,
            'week_days': week_days if week_days else [],
            'current_day': current_day,
            'current_date': new_date,
            'day_slots': current_day_slots,
            'end_date': end_date,
            'country': country,
            'province': province,
            'district': district,
            'sector': sector,
            'region': region,

        }
        return request.env.ref("website_booking_system.booking_modal_bk_slots_main_div").render(values, engine='ir.qweb')

    @http.route(['/booking/reservation/cart/validate'], type='json', auth="public", methods=['POST'], website=True)
    def booking_reservation_cart_validate(self, **post):
        product_id = post.get('product_id', False)
        sale_order = request.website.sale_get_order()
        if sale_order:
            order_line = sale_order.order_line.filtered(lambda l: l.product_id.product_tmpl_id.id == int(product_id))
            return False if len(order_line) else True
        return True
