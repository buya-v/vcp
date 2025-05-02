# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)

class CooperativeMember(models.Model):
    _name = 'vcp.cooperative.member'
    _description = 'Cooperative Member'
    _inherit = ['mail.thread', 'mail.activity.mixin'] # Added for chatter/messaging
    _order = 'cooperative_id, partner_id' # Added default order

    cooperative_id = fields.Many2one(
        'vcp.cooperative', string='Cooperative', required=True,
        help='The cooperative this member belongs to.',
        ondelete='cascade', # Added: Delete membership if cooperative is deleted
        index=True # Added: Index for performance
    )
    partner_id = fields.Many2one(
        'res.partner', string='Member', required=True,
        help='The partner who is a member of this cooperative.',
        ondelete='cascade', # Added: Delete membership if partner is deleted (consider 'restrict' if needed)
        index=True # Added: Index for performance
    )
    member_type = fields.Selection([
        ('basic', 'Basic Member'),
        ('admin', 'Admin Member'),
        # Consider adding more types if needed later
    ], string='Member Type', default='basic', required=True, tracking=True, # Added tracking
        help='Defines the role or status of the member in the cooperative.')

    join_date = fields.Date(
        string='Join Date',
        default=fields.Date.context_today, # Set automatically on creation
        readonly=True, # Usually set once on creation
        copy=False, # Don't copy join date on duplication
        tracking=True # Added tracking
    )
    active = fields.Boolean(
        string='Active Member',
        default=True,
        index=True, # Added: Index for filtering active members
        tracking=True, # Added tracking
        help="Indicates if the membership is currently active. Uncheck to archive."
    )

    _sql_constraints = [
        ('unique_cooperative_member', 'unique(cooperative_id, partner_id)',
         'A partner can only be a member of the same cooperative once.')
    ]

    # --- Display Name ---
    @api.depends('partner_id', 'partner_id.name', 'cooperative_id', 'cooperative_id.name')
    def _compute_display_name(self):
        """ Computes a more descriptive display name. """
        for member in self:
            name = member.partner_id.name or _("Unknown Partner")
            coop_name = member.cooperative_id.name or _("Unknown Cooperative")
            member.display_name = f"{name} ({coop_name})"

    # Override display_name instead of name_get for modern Odoo
    display_name = fields.Char(string='Display Name', compute='_compute_display_name', store=False) # store=False is typical for display_name

    # --- Business Logic Methods (if any needed later) ---
    # Example:
    # def action_archive(self):
    #     self.write({'active': False})

    # def action_unarchive(self):
    #     self.write({'active': True})

