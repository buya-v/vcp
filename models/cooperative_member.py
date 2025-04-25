from odoo import models, fields

class CooperativeMember(models.Model):
    _name = 'vcp.cooperative.member'
    _description = 'Cooperative Member'

    cooperative_id = fields.Many2one(
        'vcp.cooperative', string='Cooperative', required=True,
        help='The cooperative this member belongs to.'
    )
    partner_id = fields.Many2one(
        'res.partner', string='Member', required=True,
        help='The partner who is a member of this cooperative.'
    )
    member_type = fields.Selection([
        ('basic', 'Basic Member'),
        ('admin', 'Admin Member'),
    ], string='Member Type', default='basic', required=True,
        help='Defines the role of the member in the cooperative.')

    _sql_constraints = [
        ('unique_cooperative_member', 'unique(cooperative_id, partner_id)',
         'A member can only belong to a cooperative once.')
    ]