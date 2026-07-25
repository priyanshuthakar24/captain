# See LICENSE file for full copyright and licensing details.

import subprocess

from odoo import api, fields, models


class RunningPort(models.TransientModel):
    _name = 'running.port'
    _description = "Running Port"

    name = fields.Text('Running Instance Details')

    @api.model
    def default_get(self, fields_list):
        res = super(RunningPort, self).default_get(fields_list)
        command = 'ps -ax | grep odoo'
        process = subprocess.Popen([command], stdout=subprocess.PIPE,
                                   shell=True)
        out, err = process.communicate()
        res.update({'name': out.decode('utf-8', errors='ignore')})
        return res
