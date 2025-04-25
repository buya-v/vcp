from odoo import models, fields

class CooperativeType(models.Model):
    _name = 'vcp.cooperative.type'
    _description = 'Cooperative Type'

    name = fields.Char(string='Type Name', required=True)
    description = fields.Text(string='Description')
    active = fields.Boolean(string='Active', default=True, help='Indicates whether this cooperative type is active.')