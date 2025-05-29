from odoo import models, fields, api, _
import logging
# from odoo.addons.queue_job.job import job

_logger = logging.getLogger(__name__)


class Cooperative(models.Model):
    _name = 'vcp.cooperative'
    _description = 'Cooperative'

    name = fields.Char(string='Cooperative Name', required=True)
    description = fields.Text(string='Description')
    cooperative_type_id = fields.Many2one(
        'vcp.cooperative.type', string='Cooperative Type',
        help='The type of this cooperative.',
        ondelete='restrict'  # Added ondelete policy as suggested
    )
    partner_id = fields.Many2one(
        'res.partner', string='Associated Company', required=True,
        domain="[('is_company', '=', True)]",
        help="The company (partner) associated with this cooperative.",
        ondelete='restrict'
    )
    # Related address fields from partner_id
    street = fields.Char(related='partner_id.street', string="Street", readonly=True, store=True)
    street2 = fields.Char(related='partner_id.street2', string="Street 2", readonly=True, store=True)
    zip_code = fields.Char(related='partner_id.zip', string="Zip", readonly=True, store=True) # Renamed to zip_code to avoid potential keyword clash
    city = fields.Char(related='partner_id.city', string="City", readonly=True, store=True)
    state_id = fields.Many2one(
        related='partner_id.state_id',
        comodel_name='res.country.state',
        string="State",
        readonly=True,
        store=True
    )
    country_id = fields.Many2one(
        related='partner_id.country_id',
        comodel_name='res.country',
        string="Country",
        readonly=True,
        store=True
    )
    partner_tag_ids = fields.Many2many(
        comodel_name='res.partner.category',
        related='partner_id.category_id',
        string="Company Tags",
        readonly=True,
        # store=True is not typically used for Many2many related fields unless specific search/grouping needs arise.
    )
    company_type = fields.Selection(
        related='partner_id.company_type_selection',
        string="Company Type",
        readonly=True,
        store=True
    )


    member_ids = fields.One2many(
        'vcp.cooperative.member', 'cooperative_id', string='Members',
        help='The members of this cooperative.'
    )
    active = fields.Boolean(string='Active', default=True, help='Indicates whether this cooperative is active.')
    member_count = fields.Integer(
        string='Member Count',
        compute='_compute_member_count',
        store=True,
        help='The number of members in this cooperative.'
    )

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        """
        When the partner_id is changed, update the cooperative's name
        to match the partner's name.
        """
        if self.partner_id:
            self.name = self.partner_id.name

    @api.depends('member_ids')
    def _compute_member_count(self):
        # Optimized slightly: read group is often faster for counts,
        # but len() is fine for moderate numbers and simpler.
        # Keeping len() for simplicity unless performance becomes an issue.
        for cooperative in self:
            cooperative.member_count = len(cooperative.member_ids)

    # --- Action Methods (for buttons) ---
    def action_view_members(self):
        """
        Action method for the 'Members' stat button.
        Opens the list view of members for this cooperative.
        """
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id('vcp.action_cooperative_member_list') # Assumes you have an action defined for members
        if not action:
            # Fallback action definition if specific one not found
             action = {
                'name': _('Members'),
                'type': 'ir.actions.act_window',
                'res_model': 'vcp.cooperative.member',
                'view_mode': 'tree,form',
                'domain': [('cooperative_id', '=', self.id)],
                'context': {'default_cooperative_id': self.id} # Pre-fill cooperative when creating new member from here
            }
        else:
             # If using a predefined action, ensure the domain and context are set
             action['domain'] = [('cooperative_id', '=', self.id)]
             action['context'] = {'default_cooperative_id': self.id}

        return action
