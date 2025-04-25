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
        help='The type of this cooperative.'
    )
    member_ids = fields.One2many(
        'vcp.cooperative.member', 'cooperative_id', string='Members',
        help='The members of this cooperative.'
    )
    active = fields.Boolean(string='Active', default=True, help='Indicates whether this cooperative is active.')
    member_count = fields.Integer(string='Member Count', compute='_compute_member_count', store=True, help='The number of members in this cooperative.')

    @api.depends('member_ids')
    def _compute_member_count(self):
        for cooperative in self:
            cooperative.member_count = len(cooperative.member_ids)

