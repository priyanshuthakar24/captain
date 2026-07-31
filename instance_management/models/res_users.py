# See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ResUser(models.Model):
    _inherit = 'res.users'

    git_username = fields.Char(
        'GIT Username',
        help='Login ID for GIT to access the branch repository'
    )
    git_pat = fields.Char(
        'GIT Personal Token',
        help='GIT Personal access token to take the pull'
    )
    instance_ids = fields.Many2many(
        'instance.instance',
        'rel_user_instance',
        'user_id',
        'instance_id',
        string="Instance"
    )
