# -*- coding: utf-8 -*-

import json

from odoo import http, _
from odoo.exceptions import UserError
from odoo.http import request
from odoo.addons.auth_signup.controllers.main import AuthSignupHome


class AuthSignup(AuthSignupHome):

    def do_signup(self, qcontext):
        """ Shared helper that creates a res.partner out of a token """
        values = { key: qcontext.get(key) for key in ('login', 'name', 'password', 'sex', 'birth_date', 'ruc') }
        if not values:
            raise UserError(_("The form was not properly filled in."))
        if values.get('password') != qcontext.get('confirm_password'):
            raise UserError(_("Passwords do not match; please retype them."))
        if not values.get('birth_date'):
            raise UserError(_("Please enter Birth Date."))
        elif len(values.get('birth_date')) != 10:
            raise UserError(_("There is some problem Birth Date."))
        elif values.get('birth_date'):
            year = values.get('birth_date').split('-')[0]
            month = values.get('birth_date').split('-')[1]
            day = values.get('birth_date').split('-')[2]
            if year and int(year) < 1950:
                raise UserError(_("Please enter correct Birth Year."))
            if month and int(month) > 12:
                raise UserError(_("Please enter correct Birth Month."))
            if day and int(day) > 31:
                raise UserError(_("Please enter correct Birth Day."))
        supported_lang_codes = [code for code, _ in request.env['res.lang'].get_installed()]
        lang = request.context.get('lang', '').split('_')[0]
        if lang in supported_lang_codes:
            values['lang'] = lang
        self._signup_with_values(qcontext.get('token'), values)
        request.env.cr.commit()


class FilterData(http.Controller):

    @http.route(['/booking/filterdata'], type='json', auth="public", methods=['POST'], website=True)
    def filterdata(self, **post):
        data = dict()
        province_id = post.get('province_id', False)
        if province_id:
            districts = request.env['neonety.district'].sudo().search([('province_id', '=', int(province_id))])
            dists = list()
            for district in districts:
                dists.append({district.id: district.name})
            data['districts'] = dists
            regions = request.env['neonety.region'].sudo().search([('province_id', '=', int(province_id))])
            region_lst = list()
            for region in regions:
                region_lst.append({region.id: region.name})
            data['regions'] = region_lst

        district_id = post.get('district_id', False)
        if district_id:
            sectors = request.env['neonety.sector'].sudo().search([('district_id', '=', int(district_id))])
            sectors_lst = list()
            for sector in sectors:
                sectors_lst.append({sector.id: sector.name})
            data['sectors'] = sectors_lst

        return data
