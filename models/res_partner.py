from odoo import models, fields, api

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

    # New fields for individuals
    surname = fields.Char(string="Surname")
    firstname = fields.Char(string="First Name")
    register = fields.Char(
        string="Register",
        help="Individual's registration number"
    )
    national_id = fields.Char(
        string="National ID",
        help="Individual's national ID number"
    )

    @api.onchange('firstname', 'surname')
    def _onchange_individual_name(self):
        """
        When firstname or surname is changed for an individual,
        update the main 'name' field.
        """
        if not self.is_company and (self.firstname or self.surname):
            parts = []
            if self.surname:
                parts.append(self.surname.strip())
            if self.firstname:
                parts.append(self.firstname.strip())
            self.name = " ".join(parts)