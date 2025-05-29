from odoo import models, fields

class ResPartner(models.Model):
    _inherit = 'res.partner'

    cooperative_membership_ids = fields.One2many(
        'vcp.cooperative.member', 'partner_id', string='Cooperative Memberships',
        help='The cooperatives this member belongs to.'
    )

    company_type_selection = fields.Selection(
        selection=[
            ('primary_coop', 'Primary Cooperative'),
            ('joint_coop', 'Joint Cooperative'),
            ('asso_coop', 'Association Cooperative'),
            ('nat_coop', 'National Cooperative Association'),
            ('nbfi', 'Non Banking Financial Institution'),
            ('bank', 'Bank'),
            ('company', 'Limited Liability Company'),
            ('lc', 'listed Company'),
            ('gov', 'Government Institution'),
            ('ngo', 'Non Government Organisation'),
            ('other', 'Other')
        ],
        string='Company Type',
        help="Specify the type of company. This is typically relevant when 'Is a Company' is checked."
    )