# See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class IrConfigParameter(models.Model):
    _inherit = 'ir.config_parameter'

    for_version = fields.Boolean(
        'Is Version?',
        help='Set True if the parameter is configured for odoo instance version'
    )
