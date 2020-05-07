from odoo import api, fields, models, SUPERUSER_ID, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_patient = fields.Boolean(string='Is Patient')

