# See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class DownloadLog(models.TransientModel):
    _name = 'download.log'
    _description = "Download Log"

    name = fields.Char('File Name')
    file_download = fields.Binary(
        'Click On Download Link To Download File', readonly=True)
