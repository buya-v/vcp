from odoo import models, fields

class ResPartner(models.Model):
    _inherit = 'res.partner'

    cooperative_membership_ids = fields.One2many(
        'vcp.cooperative.member', 'partner_id', string='Cooperative Memberships',
        help='The cooperatives this member belongs to.'
    )