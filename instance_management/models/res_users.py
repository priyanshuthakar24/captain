# See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ResUser(models.Model):
    _inherit = 'res.users'

    git_id = fields.Char(
        'GIT Login',
        help='Login ID for GIT to access the branch repository'
    )
    git_pass = fields.Char(
        'GIT Password',
        help='GIT Password access the branch repository'
    )
    instance_ids = fields.Many2many(
        'instance.instance',
        'rel_user_instance',
        'user_id',
        'instance_id',
        string="Instance"
    )
