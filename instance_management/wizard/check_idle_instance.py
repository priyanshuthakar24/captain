# See LICENSE file for full copyright and licensing details.

import datetime
import logging
import os.path
import subprocess
from os import listdir

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

PID_FILE = '/var/run/'


class IdleInstance(models.TransientModel):
    _name = 'idle.instance'
    _description = "Idle Instance"

    name = fields.Html('Idle Instance Details')
    no_of_days = fields.Integer("Number of Days", default=0)
    state = fields.Boolean('State')

    def confirm(self):
        ir_config_obj = self.env['ir.config_parameter']
        log_path = ir_config_obj.get_param('instance_logfile_path')
        if not log_path:
            raise ValidationError(_("Please configure Instance Logfile Path in System Parameters!"))
        files = []
        instance_name = []
        result = []
        # check all log file from log file instance directory
        for log_file in listdir(log_path):
            file_path = os.path.join(log_path, log_file)
            if not os.path.isfile(file_path):
                continue
            # Read the last line of the log file
            try:
                line = subprocess.check_output(['tail', '-1', file_path]).decode().rstrip()
            except Exception:
                continue
            if not line:
                continue
            last_line_date = line.split(" ")[0]
            today_date = datetime.date.today()
            # get the date from last line
            try:
                last_date = datetime.datetime.strptime(
                    last_line_date, '%Y-%m-%d').date()
            except Exception as e:
                error_msg = 'Error!: %s in file %s' % (str(e), str(log_file))
                _logger.error(error_msg)
                continue
            # Compare the days
            if (today_date - last_date).days > self.no_of_days:
                files.append(log_file)
        for f in files:
            instance_name.append(f.split(".")[0])
        for rec in instance_name:
            pid_filepath = os.path.join(str(PID_FILE), rec + '.pid')
            # get root password configured in the company
            sudoPassword = self.env.user.company_id.root_password
            if not sudoPassword:
                raise ValidationError(_("Please configure Root Password in Company Configuration!"))
            command = 'start-stop-daemon --status --pidfile ' + pid_filepath
            status_res = os.system('echo %s|sudo -S %s' %
                                   (sudoPassword, command))
            if status_res == 0:
                result.append(rec)
        resulttext = ""
        # concate list of idle instance
        for lst in result:
            resulttext += "<li>" + str(lst) + "</li>"
        
        ctx = dict(self.env.context)
        ctx.update({
            'default_name': "<ul>" + resulttext + "</ul>",
            'default_state': True
        })
        return {
            'name': _("Idle Instance Details"),
            'view_mode': 'form',
            'res_model': 'idle.instance',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': ctx
        }
