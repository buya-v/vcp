# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

import logging
_logger = logging.getLogger(__name__)

class CooperativeApplication(models.Model):
    _name = 'vcp.cooperative.application'
    _description = 'Cooperative Creation Application'
    _inherit = ['mail.thread', 'mail.activity.mixin'] # For chatter and activities
    _order = 'application_date desc, id desc'

    name = fields.Char(
        string='Application Reference', required=True, copy=False, readonly=True,
        index=True, default=lambda self: _('New')
    )
    proposer_partner_id = fields.Many2one(
        'res.partner', string='Proposer', required=True,
        tracking=True,
        help="The person or entity proposing the creation of the cooperative."
    )
    proposed_name = fields.Char(
        string='Proposed Cooperative Name', required=True, tracking=True,
        help="The intended name for the new cooperative."
    )
    proposed_type_id = fields.Many2one(
        'vcp.cooperative.type', string='Proposed Type', required=True,
        tracking=True, ondelete='restrict',
        help="The intended type for the new cooperative."
    )
    proposed_description = fields.Text(
        string='Proposed Description/Purpose', required=True, tracking=True,
        help="Detailed description of the cooperative's purpose and activities."
    )
    application_date = fields.Datetime(
        string='Application Date', required=True, readonly=True,
        default=fields.Datetime.now, copy=False, tracking=True,
        help="Date and time the application was submitted."
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled')
        ], string='Status', default='draft', required=True, copy=False, tracking=True,
        help="Status of the cooperative creation application.")

    rejection_reason = fields.Text(string='Rejection Reason', copy=False, tracking=True)

    reviewer_id = fields.Many2one(
        'res.users', string='Reviewed By', readonly=True, copy=False, tracking=True
    )
    review_date = fields.Datetime(
        string='Reviewed Date', readonly=True, copy=False, tracking=True
    )

    created_cooperative_id = fields.Many2one(
        'vcp.cooperative', string='Created Cooperative', readonly=True, copy=False,
        help="The cooperative record created upon approval of this application."
    )

    # --- Constraints ---
    @api.constrains('proposed_name')
    def _check_existing_cooperative_name(self):
        # Check against *existing* cooperatives, not just other applications
        for app in self:
            if app.proposed_name:
                existing_coop = self.env['vcp.cooperative'].search_count([
                    ('name', '=ilike', app.proposed_name),
                    # ('active', '=', True) # Optional: Only check against active ones?
                ])
                if existing_coop > 0:
                    # Raise warning, not validation error, as it's okay during draft/review
                    # Validation will happen explicitly before approval
                    _logger.warning(f"Proposed cooperative name '{app.proposed_name}' already exists.")
                    # Consider adding a non-blocking message to the form view?

    # --- CRUD Overrides ---
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('vcp.cooperative.application') or _('New')
        return super().create(vals_list)

    # --- Action Methods ---
    def action_submit(self):
        self.ensure_one()
        if self.state != 'draft':
            raise UserError(_("Only draft applications can be submitted."))
        self.write({'state': 'submitted'})
        self.message_post(body=_("Cooperative application submitted for review."))

    def action_review(self):
        self.ensure_one()
        if self.state != 'submitted':
             raise UserError(_("Only submitted applications can be marked as under review."))
        self.write({'state': 'under_review'})
        self.message_post(body=_("Cooperative application is now under review."))

    def action_approve(self):
        self.ensure_one()
        if self.state not in ('submitted', 'under_review'):
            raise UserError(_("Only submitted or under review applications can be approved."))

        # Explicit check for existing cooperative name before creation
        Cooperative = self.env['vcp.cooperative']
        existing_coop = Cooperative.search([('name', '=ilike', self.proposed_name)], limit=1)
        if existing_coop:
            raise UserError(_("A cooperative with the name '%s' already exists (ID: %d). Please propose a different name or reject this application.") % (existing_coop.name, existing_coop.id))

        # Create the cooperative record
        coop_vals = {
            'name': self.proposed_name,
            'cooperative_type_id': self.proposed_type_id.id,
            'description': self.proposed_description,
            # 'active': True, # Default is True
            # Add other default fields for vcp.cooperative if needed
        }
        try:
            new_cooperative = Cooperative.create(coop_vals)
            self.write({
                'state': 'approved',
                'reviewer_id': self.env.user.id,
                'review_date': fields.Datetime.now(),
                'created_cooperative_id': new_cooperative.id,
            })
            self.message_post(body=_("Application approved. Cooperative '%s' (ID: %d) created.") % (new_cooperative.name, new_cooperative.id))
            # Optional: Notify proposer
            # self.proposer_partner_id.message_post(...)
        except Exception as e:
             _logger.error(f"Failed to create cooperative for application {self.name}: {e}")
             raise UserError(_("Failed to create the cooperative record. Please check cooperative model configuration and data. Error: %s") % e)

    def action_reject(self):
        self.ensure_one()
        if self.state not in ('submitted', 'under_review'):
            raise UserError(_("Only submitted or under review applications can be rejected."))
        # Optional: Require a rejection reason via view attribute or check here
        # if not self.rejection_reason:
        #     raise UserError(_("Please provide a rejection reason before rejecting the application."))

        self.write({
            'state': 'rejected',
            'reviewer_id': self.env.user.id,
            'review_date': fields.Datetime.now(),
        })
        self.message_post(body=_("Application rejected. Reason: %s") % (self.rejection_reason or _("No reason provided.")))
        # Optional: Notify proposer

    def action_cancel(self):
        self.ensure_one()
        if self.state not in ('draft', 'submitted', 'under_review'):
             raise UserError(_("Only draft, submitted or under review applications can be cancelled."))
        self.write({'state': 'cancelled'})
        self.message_post(body=_("Application cancelled."))

    def action_reset_to_draft(self):
        self.ensure_one()
        if self.state not in ('cancelled', 'rejected'): # Only allow reset from terminal states
             raise UserError(_("Only cancelled or rejected applications can be reset to draft."))
        # Ensure no cooperative record was created or handle it if necessary
        if self.created_cooperative_id: # Check if a cooperative was linked
             raise UserError(_("Cannot reset an approved application that created a cooperative. Please handle the cooperative record '%s' (ID: %d) separately.") % (self.created_cooperative_id.name, self.created_cooperative_id.id))
        self.write({
            'state': 'draft',
            'reviewer_id': False,
            'review_date': False,
            'rejection_reason': False,
            # created_cooperative_id should already be False if not approved
        })
        self.message_post(body=_("Application reset to draft state."))

    # --- Helper Methods ---
    def action_view_created_cooperative(self):
        """ Action to view the cooperative created from this application. """
        self.ensure_one()
        if not self.created_cooperative_id:
            raise UserError(_("No cooperative has been created from this application yet."))

        return {
            'name': _('Created Cooperative'),
            'type': 'ir.actions.act_window',
            'res_model': 'vcp.cooperative',
            'view_mode': 'form',
            'res_id': self.created_cooperative_id.id,
            'target': 'current', # Or 'new' to open in a dialog/new window
        }

