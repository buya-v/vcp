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

