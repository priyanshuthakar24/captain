# See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    root_password = fields.Char(
        "Root Password",
        help="Root Password to start,stop and restart an instance from GUI."
    )
