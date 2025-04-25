from odoo.tests.common import HttpCase

class TestMembershipRequest(HttpCase):

    def test_membership_request_form(self):
        response = self.url_open('/membership/request')
        self.assertEqual(response.status_code, 200)

    def test_submit_membership_request(self):
        response = self.url_open('/membership/request/submit', data={
            'name': 'John Doe',
            'email': 'john.doe@example.com',
            'partner_type': 'herder',
        })
        self.assertEqual(response.status_code, 200)