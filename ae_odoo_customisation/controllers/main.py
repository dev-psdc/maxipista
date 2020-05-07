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
