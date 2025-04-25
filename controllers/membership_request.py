from odoo import http
from odoo.http import request

class MembershipRequestController(http.Controller):

    @http.route('/membership/request', type='http', auth='public', website=True)
    def membership_request_form(self, **kwargs):
        """Render the membership request form."""
        return request.render('vcp.membership_request_form', {})

    @http.route('/membership/request/submit', type='http', auth='public', website=True, methods=['POST'])
    def submit_membership_request(self, **kwargs):
        """Handle the form submission."""
        name = kwargs.get('name')
        email = kwargs.get('email')
        partner_type = kwargs.get('partner_type')

        # Validate required fields
        if not name or not email or not partner_type:
            return request.render('vcp.membership_request_form', {
                'error': 'All fields are required.'
            })

        # Validate partner type
        if partner_type not in ['herder', 'farmer']:
            return request.render('vcp.membership_request_form', {
                'error': 'Invalid partner type selected.'
            })

        # Check for duplicate email
        existing_partner = request.env['res.partner'].sudo().search([('email', '=', email)], limit=1)
        if existing_partner:
            return request.render('vcp.membership_request_form', {
                'error': 'A partner with this email already exists.'
            })

        # Create a new partner
        partner = request.env['res.partner'].sudo().create({
            'name': name,
            'email': email,
            'partner_type': partner_type,
        })

        # Optionally, add the partner to a default cooperative
        cooperative = request.env['vcp.cooperative'].sudo().search([], limit=1)
        if cooperative:
            cooperative.sudo().add_member(partner.id)

        return request.render('vcp.membership_request_success', {'partner': partner})