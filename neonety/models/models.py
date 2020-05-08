# -*- coding: utf-8 -*-
from odoo import models, fields, api
import datetime
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta
import logging
_logger = logging.getLogger(__name__)

SEX_TYPES = [
	('Masculino',"Masculino"),
	('Femenino',"Femenino"),
]

def calculate_age(_birth_date):
	age = 0
	current_date = datetime.date.today()
	birth_date = _birth_date
	born = relativedelta(current_date,birth_date).years
	if born > 0:
		age = born
	return age


class NeonetyCountry(models.Model):
	_name = 'res.country'
	_inherit = 'res.country'

	province_ids = fields.One2many('neonety.province', 'country_id', string='Provincias', ondelete='cascade')
	# = fields.One2many('neonety.region', 'country_id', string='Regiones', ondelete='cascade')


class NeonetyProvince(models.Model):
	_name = 'neonety.province'

	code = fields.Char(string='Código', size=3, required=True, translate=True)
	name = fields.Char(string='Nombre', size=255, required=True, translate=True)
	country_id = fields.Many2one('res.country', string='País', required=False, translate=True, compute='_get_country_id', store=True, ondelete='cascade')
	district_ids = fields.One2many('neonety.district', 'province_id', string='Distritos')

	@api.depends('name')
	def _get_country_id(self):
		country = self.pool.get('res.country')
		country_id = self.env['res.country'].search([['name', '=', 'Panama']]).id
		self.country_id = country_id


class NeonetyDistrict(models.Model):
	_name = 'neonety.district'

	code = fields.Char(string='Código', size=3, required=True, translate=True)
	name = fields.Char(string='Nombre', size=255, required=True, translate=True)
	country_id = fields.Many2one('res.country', string='País', required=False, translate=True, compute='_get_country_id', store=True)
	province_id = fields.Many2one('neonety.province', string='Provincia', required=False, translate=True)
	sector_ids = fields.One2many('neonety.sector', 'district_id', string='Corregimientos')

	@api.depends('name')
	def _get_country_id(self):
		country = self.pool.get('res.country')
		country_id = self.env['res.country'].search([['name', '=', 'Panama']]).id
		self.country_id = country_id


class NeonetySector(models.Model):
	_name = 'neonety.sector'

	code = fields.Char(string='Código', size=3, required=True, translate=True)
	name = fields.Char(string='Nombre', size=255, required=True, translate=True)
	country_id = fields.Many2one('res.country', string='País', required=False, translate=True, compute='_get_country_id', store=True)
	province_id = fields.Many2one('neonety.province', string='Provincia', required=False, translate=True)
	district_id = fields.Many2one('neonety.district', string='Distrito', required=False, translate=True)

	@api.depends('name')
	def _get_country_id(self):
		country = self.pool.get('res.country')
		country_id = self.env['res.country'].search([['name', '=', 'Panama']]).id
		self.country_id = country_id


class NeonetyPartnerConcept(models.Model):
	_name = 'neonety.partner.concept'

	name = fields.Char(string='Concepto', required=True, translate=True)
	status = fields.Boolean(string='Estatus', required=True, translate=True)


class NeonetyRegion(models.Model):
	_name = 'neonety.region'

	code = fields.Char(string='Código', size=3, required=True)
	name = fields.Char(string='Nombre', size=255, required=True)
	country_id = fields.Many2one('res.country', string='País', required=False, compute='_get_country_id', store=True, ondelete='cascade')
	province_id = fields.Many2one('neonety.province', string='Provincia')


class NeonetyPartner(models.Model):
	_name = 'res.partner'
	_inherit = 'res.partner'

	@api.depends('name')
	def _get_country_id(self):
		country = self.pool.get('res.country')
		country_id = self.env['res.country'].search([['name', '=', 'Panama']]).id
		self.country_id = country_id

	ruc = fields.Char(string='RUC', size=20)
	dv = fields.Char(string='DV', size=2)
	operation_notice_number = fields.Char(string=' No. Aviso de Operación', size=50)
	partner_nationality = fields.Selection([
		('local', 'Local'),
		('extranjero', 'Extranjero')],
		string='Nacionalidad del cliente ó proveedor')
	partner_type = fields.Selection([
		('natural', 'Persona natural (N)'),
		('juridica', 'Persona jurídica (J)'),
		('extranjero', 'Extranjero (E)')],
		string='Tipo de cliente ó proveedor')
	neonety_partner_concept_id = fields.Many2one('neonety.partner.concept', string='Concepto', default=None)
	neonety_country_id = fields.Many2one('res.country', string='País', default=lambda self: self._get_country_id())
	country_id = fields.Many2one('res.country', string='País', default=lambda self: self._get_country_id())
	province_id = fields.Many2one('neonety.province', string='Provincia')
	district_id = fields.Many2one('neonety.district', string='Distrito')
	sector_id = fields.Many2one('neonety.sector', string='Corregimiento')
	street = fields.Char(string='Dirección')
	sex = fields.Selection(SEX_TYPES, string='Sexo')
	birth_date = fields.Date(string='Fecha de Nacimiento')
	age = fields.Char(string='Edad', compute='_calculate_age', default='0')

	@api.depends('birth_date')
	def _calculate_age(self):
		for record in self:
			record.age = '0'
			if record.birth_date:
				born = calculate_age(_birth_date=record.birth_date)
				if born > 0:
					record.age = '{0} año(s) de edad'.format(born)

	@api.onchange('birth_date')
	def _onchange_birth_date(self):
		self.age = '0'
		if self.birth_date:
			born = calculate_age(_birth_date=self.birth_date)
			if born > 0:
				self.age = '{0} año(s) de edad'.format(born)

	def _get_country_id(self):
		self._cr.execute("SELECT id FROM res_country WHERE code LIKE 'PA' LIMIT 1")
		country_id = self._cr.fetchone()
		return country_id

	@api.onchange('neonety_country_id')
	def onchange_neonety_country_id(self):
		res = {}
		if self.neonety_country_id:
			self._cr.execute('SELECT id, name FROM neonety_province WHERE country_id = %s', (self.neonety_country_id.id, ))
			provinces = self._cr.fetchall()
			ids = []

			for province in provinces:
				ids.append(province[0])
			res['domain'] = {'province_id': [('id', 'in', ids)]}
		return res

	@api.onchange('province_id')
	def onchange_province_id(self):
		res = {}

		if self.province_id:
			self._cr.execute('SELECT neonety_district.id, neonety_district.name FROM neonety_district WHERE neonety_district.province_id = %s AND neonety_district.country_id = ( SELECT neonety_province.country_id FROM neonety_province WHERE neonety_province.id = %s) ', (self.province_id.id, self.province_id.id))
			districts = self._cr.fetchall()
			ids = []

			for district in districts:
				ids.append(district[0])
			res['domain'] = {'district_id': [('id', 'in', ids)]}
		return res

	@api.onchange('district_id')
	def onchange_district_id(self):
		res = {}

		if self.district_id:
			self._cr.execute('SELECT neonety_sector.id, neonety_sector.name FROM neonety_sector WHERE neonety_sector.district_id = %s AND  neonety_sector.country_id = ( SELECT neonety_district.country_id FROM neonety_district WHERE neonety_district.id = %s) ', (self.district_id.id, self.district_id.id))
			sectors = self._cr.fetchall()
			ids = []

			for sector in sectors:
				ids.append(sector[0])
			res['domain'] = {'sector_id': [('id', 'in', ids)]}
		return res

	def _check_fields_required(self, vals):
		errors = []
		if 'email' in vals:
			if vals['email']:
				import re
				match = re.match('^[_a-zA-Z0-9-]+(\.[_a-zA-Z0-9-]+)*@[a-zA-Z0-9-]+(\.[a-zA-Z0-9-]+)*(\.[a-zA-Z]{2,4})$', vals['email'])
				if match == None:
					errors.append('El Email tiene un formato inválido, formado esperado: "example@domain.com"')
		if len(errors) > 0:
			raise ValidationError("\n".join(errors))

	def _check_ruc_exists(self, vals, pk=0):
		if 'ruc' in vals:
			if vals['ruc']:
				ruc = vals.get('ruc', False)
				if ruc:
					ruc = ruc.replace(' ', '') if '-' in ruc else ruc
					ruc = ruc.replace(" ", '') if " " in ruc else ruc
					if pk > 0:
						counter = self.env['res.partner'].search_count([('ruc', '=', ruc), ('id', '!=', pk)])
					else:
						counter = self.env['res.partner'].search_count([('ruc', '=', ruc)])
					if counter > 0:
						raise ValidationError('El RUC ya se encuentra registrado en otra cuenta.')

	@api.model
	def create(self, vals):
		self._check_ruc_exists(vals=vals)
		if 'ruc' in vals:
			ruc = vals.get('ruc', False)
			if ruc:
				ruc = ruc.replace(' ', '') if '-' in ruc else ruc
				ruc = ruc.replace(" ", '') if " " in ruc else ruc
				vals['ruc'] = ruc
		partner = super(NeonetyPartner, self).create(vals)
		self._check_fields_required(vals=vals)
		return partner
    
	def write(self, vals):
		if 'ruc' in vals:
			ruc = vals.get('ruc', False)
			if ruc:
				ruc = ruc.replace(' ', '') if '-' in ruc else ruc
				ruc = ruc.replace(" ", '') if " " in ruc else ruc
				vals['ruc'] = ruc
		partner = super(NeonetyPartner, self).write(vals)
		self._check_fields_required(vals=vals)
		self._check_ruc_exists(vals=vals, pk=self.id)
		return partner