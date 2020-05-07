from odoo import api, fields, models, SUPERUSER_ID, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    region_id = fields.Many2one('neonety.region', string='Region')
