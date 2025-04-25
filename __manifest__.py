{
    'name': 'Virtual Cooperative Management',
    'version': '1.0',
    'summary': 'Manage virtual cooperatives and their members',
    'description': """
        This module allows users to manage virtual cooperatives, add members, 
        handle membership requests, and integrate with the portal for member self-service.
    """,
    'author': 'Virtual Cooperative Project Team',
    'website': 'https://vcp.mofa.gov.mn',
    'category': 'Custom',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'portal',
        # 'queue_job',  # Disabled asynchronous processing
        'web',        # Required for OWL framework integration
    ],
    'data': [
        'security/ir.model.access.csv',
        # 'security/security.xml',
        'views/cooperative_views.xml',
        'views/cooperative_type_views.xml',
        # 'views/portal_templates.xml',
    ],
    
    # 'assets': {
    #     'web.assets_backend': [
    #         'vcp/static/src/js/membership_form.js',
    #     ],
    #     'web.assets_qweb': [
    #         'vcp/static/src/xml/membership_form_templates.xml',
    #     ],
    # },
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}