# -*- coding: utf-8 -*-
import logging
from odoo import http, _
from odoo.http import request
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

class MembershipWebsite(http.Controller):

    # Helper method to get partner (create if not exists)
    def _get_applicant_partner(self, name, email, phone=None):
        Partner = request.env['res.partner'].sudo()
        # Try to find partner by email (normalize email)
        normalized_email = email.strip().lower() if email else None
        if not normalized_email:
             # If no email, try by name and phone (less reliable)
             domain = [('name', '=', name)]
             if phone:
                 domain = ['|', ('phone', '=', phone), ('mobile', '=', phone)] + domain
             partner = Partner.search(domain, limit=1)
        else:
            partner = Partner.search([('email', '=ilike', normalized_email)], limit=1) # Use =ilike for case-insensitivity

        if not partner:
            _logger.info(f"Creating new partner for membership application: {name} ({email})")
            partner_vals = {
                'name': name,
                'email': normalized_email,
                'phone': phone,
                'company_type': 'person', # Assume individual applicant
                # 'website_id': request.website.id, # Associate with current website
            }
            # Check if website module adds specific fields
            if hasattr(Partner, 'website_id') and request.website:
                 partner_vals['website_id'] = request.website.id

            partner = Partner.create(partner_vals)
        else:
             _logger.info(f"Found existing partner for membership application: {partner.name} ({partner.id})")
             # Optional: Update phone if provided and missing on partner?
             # if phone and not partner.phone and not partner.mobile:
             #     partner.sudo().write({'phone': phone})
        return partner

    # Route to display the form
    @http.route('/cooperative/apply', type='http', auth='public', website=True, sitemap=True)
    def membership_apply_form(self, **kw):
        try:
            cooperatives = request.env['vcp.cooperative'].search([('active', '=', True)]) # Fetch active cooperatives
            values = {
                'cooperatives': cooperatives,
                'error': kw.get('error'),
                'error_message': kw.get('error_message'),
                'submitted_data': kw # Pass back submitted data on error
            }
            return request.render('vcp.membership_application_form_template', values)
        except Exception as e:
            _logger.error(f"Error rendering membership application form: {e}", exc_info=True)
            # Render a generic error page or the form with a generic error
            return request.render('vcp.membership_application_form_template', {
                'cooperatives': [],
                'error': True,
                'error_message': _("An error occurred while loading the form. Please try again later.")
            })


    # Route to handle form submission
    @http.route('/cooperative/apply/submit', type='http', auth='public', website=True, methods=['POST'], csrf=True)
    def membership_apply_submit(self, **post):
        # Basic Validation
        required_fields = ['applicant_name', 'applicant_email', 'cooperative_id', 'motivation']
        missing_fields = [field for field in required_fields if not post.get(field)]
        if missing_fields:
            error_msg = _("Please fill in all required fields: %s") % ', '.join(mf.replace('_', ' ').title() for mf in missing_fields)
            post['error'] = True
            post['error_message'] = error_msg
            # Re-render form with error and submitted data
            return self.membership_apply_form(**post)

        try:
            cooperative_id = int(post.get('cooperative_id'))
            applicant_name = post.get('applicant_name')
            applicant_email = post.get('applicant_email')
            applicant_phone = post.get('applicant_phone') # Optional
            motivation = post.get('motivation')

            # Get or create partner
            partner = self._get_applicant_partner(applicant_name, applicant_email, applicant_phone)

            # Prepare application values
            application_vals = {
                'partner_id': partner.id,
                'cooperative_id': cooperative_id,
                'motivation': motivation,
                'state': 'submitted', # Automatically set state to submitted from web form
                # 'application_date': fields.Datetime.now(), # Default is set on model
            }

            # Create the application using sudo() as public user has no write access
            application = request.env['vcp.membership.application'].sudo().create(application_vals)
            _logger.info(f"Membership application created from website: {application.name} for partner {partner.id}")

            # Redirect to a thank you page
            return request.redirect('/cooperative/apply/thankyou')

        except ValidationError as ve:
             _logger.warning(f"Validation Error submitting membership application: {ve}")
             post['error'] = True
             post['error_message'] = str(ve)
             return self.membership_apply_form(**post)
        except ValueError: # Handle invalid cooperative_id conversion
             _logger.warning(f"Invalid cooperative ID received: {post.get('cooperative_id')}")
             post['error'] = True
             post['error_message'] = _("Invalid cooperative selected.")
             return self.membership_apply_form(**post)
        except Exception as e:
            _logger.error(f"Error processing membership application submission: {e}", exc_info=True)
            post['error'] = True
            post['error_message'] = _("An unexpected error occurred. Please try again or contact support.")
            # Re-render form with error
            return self.membership_apply_form(**post)


    # Route for the thank you page
    @http.route('/cooperative/apply/thankyou', type='http', auth='public', website=True, sitemap=False)
    def membership_apply_thankyou(self, **kw):
        return request.render('vcp.membership_application_thankyou_template')
    
    # --- Cooperative Creation Application Routes ---

    # Route to display the cooperative creation form
    @http.route('/cooperative/create/apply', type='http', auth='public', website=True, sitemap=True)
    def cooperative_create_apply_form(self, **kw):
        try:
            cooperative_types = request.env['vcp.cooperative.type'].search([('active', '=', True)])
            values = {
                'cooperative_types': cooperative_types,
                'error': kw.get('error'),
                'error_message': kw.get('error_message'),
                'submitted_data': kw # Pass back submitted data on error
            }
            # Use a distinct template name
            return request.render('vcp.cooperative_application_form_template', values)
        except Exception as e:
            _logger.error(f"Error rendering cooperative application form: {e}", exc_info=True)
            return request.render('vcp.cooperative_application_form_template', {
                'cooperative_types': [],
                'error': True,
                'error_message': _("An error occurred while loading the form. Please try again later.")
            })

    # Route to handle cooperative creation form submission
    @http.route('/cooperative/create/apply/submit', type='http', auth='public', website=True, methods=['POST'], csrf=True)
    def cooperative_create_apply_submit(self, **post):
        # Basic Validation
        required_fields = ['proposer_name', 'proposer_email', 'proposed_name', 'proposed_type_id', 'proposed_description']
        missing_fields = [field for field in required_fields if not post.get(field)]
        if missing_fields:
            error_msg = _("Please fill in all required fields: %s") % ', '.join(mf.replace('_', ' ').title() for mf in missing_fields)
            post['error'] = True
            post['error_message'] = error_msg
            # Re-render form with error and submitted data
            return self.cooperative_create_apply_form(**post)

        try:
            proposed_type_id = int(post.get('proposed_type_id'))
            proposer_name = post.get('proposer_name')
            proposer_email = post.get('proposer_email')
            proposer_phone = post.get('proposer_phone') # Optional
            proposed_name = post.get('proposed_name')
            proposed_description = post.get('proposed_description')

            # Get or create proposer partner (using the same helper method)
            # Ensure _get_applicant_partner is accessible or defined in this class
            proposer_partner = self._get_applicant_partner(proposer_name, proposer_email, proposer_phone)

            # Prepare application values
            application_vals = {
                'proposer_partner_id': proposer_partner.id,
                'proposed_name': proposed_name,
                'proposed_type_id': proposed_type_id,
                'proposed_description': proposed_description,
                'state': 'submitted', # Automatically set state to submitted from web form
            }

            # Create the application using sudo()
            application = request.env['vcp.cooperative.application'].sudo().create(application_vals)
            _logger.info(f"Cooperative application created from website: {application.name} by partner {proposer_partner.id}")

            # Redirect to a thank you page
            return request.redirect('/cooperative/create/apply/thankyou')

        except ValidationError as ve:
             _logger.warning(f"Validation Error submitting cooperative application: {ve}")
             post['error'] = True
             post['error_message'] = str(ve)
             return self.cooperative_create_apply_form(**post)
        except ValueError: # Handle invalid proposed_type_id conversion
             _logger.warning(f"Invalid cooperative type ID received: {post.get('proposed_type_id')}")
             post['error'] = True
             post['error_message'] = _("Invalid cooperative type selected.")
             return self.cooperative_create_apply_form(**post)
        except Exception as e:
            _logger.error(f"Error processing cooperative application submission: {e}", exc_info=True)
            post['error'] = True
            post['error_message'] = _("An unexpected error occurred. Please try again or contact support.")
            # Re-render form with error
            return self.cooperative_create_apply_form(**post)

    # Route for the cooperative creation thank you page
    @http.route('/cooperative/create/apply/thankyou', type='http', auth='public', website=True, sitemap=False)
    def cooperative_create_apply_thankyou(self, **kw):
        # Use a distinct template name
        return request.render('vcp.cooperative_application_thankyou_template')

