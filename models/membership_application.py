# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

import logging
_logger = logging.getLogger(__name__)

class MembershipApplication(models.Model):
    _name = 'vcp.membership.application'
    _description = 'Membership Application'
    _inherit = ['mail.thread', 'mail.activity.mixin'] # For chatter and activities
    _order = 'application_date desc, id desc'

    name = fields.Char(string='Application Reference', required=True, copy=False, readonly=True, index=True, default=lambda self: _('New'))
    partner_id = fields.Many2one(
        'res.partner', string='Applicant', required=True,
        tracking=True,
        help="The person or company applying for membership."
    )
    cooperative_id = fields.Many2one(
        'vcp.cooperative', string='Cooperative', required=True,
        tracking=True, ondelete='cascade', # Or 'restrict' if you don't want deleting coop to delete apps
        help="The cooperative the applicant wants to join."
    )
    application_date = fields.Datetime(
        string='Application Date', required=True, readonly=True,
        default=fields.Datetime.now, copy=False,
        tracking=True,
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
        help="Status of the membership application.")

    motivation = fields.Text(string='Motivation', help="Reason why the applicant wants to join.")

    rejection_reason = fields.Text(string='Rejection Reason', copy=False, tracking=True)

    reviewer_id = fields.Many2one('res.users', string='Reviewed By', readonly=True, copy=False, tracking=True)
    review_date = fields.Datetime(string='Reviewed Date', readonly=True, copy=False, tracking=True)

    member_id = fields.Many2one('vcp.cooperative.member', string='Created Member Record', readonly=True, copy=False)

    # --- Constraints ---
    @api.constrains('partner_id', 'cooperative_id', 'state')
    def _check_unique_pending_application(self):
        for app in self:
            if app.state in ('draft', 'submitted', 'under_review', 'approved'):
                domain = [
                    ('partner_id', '=', app.partner_id.id),
                    ('cooperative_id', '=', app.cooperative_id.id),
                    ('state', 'in', ('draft', 'submitted', 'under_review', 'approved')),
                    ('id', '!=', app.id)
                ]
                existing_apps = self.search_count(domain)
                if existing_apps > 0:
                    raise ValidationError(_("An active or pending application already exists for this applicant and cooperative."))
            # Also check if already an active member
            if app.state != 'approved' and app.partner_id and app.cooperative_id:
                 existing_member = self.env['vcp.cooperative.member'].search_count([
                     ('partner_id', '=', app.partner_id.id),
                     ('cooperative_id', '=', app.cooperative_id.id),
                     # Add state check if members have states ('active', '=', True)
                 ])
                 if existing_member > 0:
                     raise ValidationError(_("This applicant is already a member of this cooperative."))


    # --- CRUD Overrides ---
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('vcp.membership.application') or _('New')
        return super().create(vals_list)

    # --- Action Methods ---
    def action_submit(self):
        self.ensure_one()
        if self.state != 'draft':
            raise UserError(_("Only draft applications can be submitted."))
        self.write({'state': 'submitted'})
        # Optional: Notify cooperative managers/reviewers
        self.message_post(body=_("Application submitted for review."))

    def action_review(self):
        self.ensure_one()
        if self.state != 'submitted':
             raise UserError(_("Only submitted applications can be marked as under review."))
        self.write({'state': 'under_review'})

    def action_approve(self):
        self.ensure_one()
        if self.state not in ('submitted', 'under_review'):
            raise UserError(_("Only submitted or under review applications can be approved."))

        # Check again if member already exists (belt and suspenders)
        Member = self.env['vcp.cooperative.member']
        existing_member = Member.search([
            ('partner_id', '=', self.partner_id.id),
            ('cooperative_id', '=', self.cooperative_id.id),
        ], limit=1)

        if existing_member:
             # Link existing member if found (e.g., if constraint failed or was removed)
             self.write({
                'state': 'approved',
                'reviewer_id': self.env.user.id,
                'review_date': fields.Datetime.now(),
                'member_id': existing_member.id,
             })
             self.message_post(body=_("Application approved. Linked to existing member record."))
             _logger.warning(f"Application {self.name} approved, but member {existing_member.id} already existed for partner {self.partner_id.id} in cooperative {self.cooperative_id.id}.")

        else:
            # Create the member record
            # TODO: Determine the 'member_type' - needs to be defined or selected. Using a placeholder.
            member_vals = {
                'partner_id': self.partner_id.id,
                'cooperative_id': self.cooperative_id.id,
                'join_date': fields.Date.today(),
                # 'member_type': 'standard', # Example: Needs definition
                # Add other required fields for vcp.cooperative.member
            }
            try:
                new_member = Member.create(member_vals)
                self.write({
                    'state': 'approved',
                    'reviewer_id': self.env.user.id,
                    'review_date': fields.Datetime.now(),
                    'member_id': new_member.id,
                })
                self.message_post(body=_("Application approved and member record created."))
                # Optional: Notify applicant
                # self.partner_id.message_post(...)
            except Exception as e:
                 _logger.error(f"Failed to create member for application {self.name}: {e}")
                 raise UserError(_("Failed to create the member record. Please check member model configuration. Error: %s") % e)


    def action_reject(self):
        self.ensure_one()
        if self.state not in ('submitted', 'under_review'):
            raise UserError(_("Only submitted or under review applications can be rejected."))
        # Optional: Require a rejection reason
        # if not self.rejection_reason:
        #     raise UserError(_("Please provide a rejection reason before rejecting the application."))

        self.write({
            'state': 'rejected',
            'reviewer_id': self.env.user.id,
            'review_date': fields.Datetime.now(),
        })
        self.message_post(body=_("Application rejected. Reason: %s") % (self.rejection_reason or _("No reason provided.")))
        # Optional: Notify applicant

    def action_cancel(self):
        # Could be triggered by applicant from portal or by admin
        self.ensure_one()
        if self.state not in ('draft', 'submitted', 'under_review'):
             raise UserError(_("Only draft, submitted or under review applications can be cancelled."))
        self.write({'state': 'cancelled'})
        self.message_post(body=_("Application cancelled."))

    def action_reset_to_draft(self):
        # For administrative correction
        self.ensure_one()
        if self.state not in ('cancelled', 'rejected'): # Only allow reset from terminal states
             raise UserError(_("Only cancelled or rejected applications can be reset to draft."))
        # Ensure no member record was created or handle it if necessary
        if self.member_id and self.state == 'approved': # Should not happen based on state check, but good practice
             raise UserError(_("Cannot reset an approved application that created a member record. Please handle the member record separately."))
        self.write({
            'state': 'draft',
            'reviewer_id': False,
            'review_date': False,
            'rejection_reason': False,
            'member_id': False, # Clear link if it was somehow set
        })
        self.message_post(body=_("Application reset to draft state."))

