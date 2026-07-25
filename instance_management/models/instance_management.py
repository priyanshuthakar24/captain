# See LICENSE file for full copyright and licensing details.

import base64
import io
import os.path
import subprocess

from lxml import etree

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.modules import get_resource_from_path

PID_FILE = '/var/run/'


class InstanceInstance(models.Model):
    _name = 'instance.instance'
    _description = "Instance"
    _inherit = ['mail.thread']

    def _get_instance_status(self):
        for rec in self:
            if rec.name:
                pid_filepath = os.path.join(str(PID_FILE), rec.name + '.pid')
                # get root password configured in the company
                sudoPassword = self.get_password()
                command = 'start-stop-daemon --status --pidfile ' + pid_filepath
                status_res = os.system('echo %s|sudo -S %s' %
                                       (sudoPassword, command))
                if status_res == 0:
                    rec.status = 'Running'
                else:
                    rec.status = 'Stopped'
            else:
                raise UserError(_("There is no Name found for Instance"))

    name = fields.Char('Name')
    odoo_version = fields.Many2one('ir.config_parameter', 'Version')
    branch_ids = fields.One2many('branch.branch', 'instance_id', 'Branch')
    state = fields.Selection([('draft', 'Draft'), ('confirm', 'Confirm')],
                             string='State', default='draft',
                             tracking=True)
    server_config = fields.Text('Server Configuration')
    status = fields.Char(compute="_get_instance_status", string='Status')
    xmlrpc_port = fields.Integer('XmlRPC Port')
    pid = fields.Char('Process ID')
    db_name = fields.Char(string="Database Name")
    requested_by = fields.Char(string="Requested By")
    long_polling_port = fields.Char(string="LongPolling Port")

    _sql_constraints = [
        ('long_polling_port_unique', 'UNIQUE(long_polling_port)', 'LongPolling Port must be unique!')
    ]

    @api.model
    def get_view(self, view_id=None, view_type='form', **options):
        '''Override method to disable create/edit button for tree, form view
        for user of group instance user'''
        res = super(InstanceInstance, self).get_view(view_id=view_id, view_type=view_type, **options)
        doc = etree.XML(res['arch'])
        if not self.user_has_groups('instance_management.instance_manager_group'):
            # disable create and edit button for instance user group.
            if view_type in ('tree', 'list'):
                nodes = doc.xpath("//tree") + doc.xpath("//list")
                for node in nodes:
                    node.set('create', 'false')
                    node.set('edit', 'false')
                res['arch'] = etree.tostring(doc)
            if view_type == 'form':
                nodes = doc.xpath("//form")
                for node in nodes:
                    node.set('create', 'false')
                    node.set('edit', 'false')
                res['arch'] = etree.tostring(doc)
        return res

    def write(self, vals):
        '''update the server configuration file'''
        ir_config_para_obj = self.env['ir.config_parameter']
        res = super(InstanceInstance, self).write(vals)
        for rec in self:
            config_path = ir_config_para_obj.get_param('instance_config_path')
            if config_path:
                config_file = config_path + rec.name + '.conf'
                is_config_file = os.path.isfile(config_file)
                if vals.get('server_config') and is_config_file:
                    with io.FileIO(config_file, "w") as file:
                        file.write(rec.server_config.encode('utf-8'))
        return res

    def download_logfile(self):
        '''This method will provide the functionality to download the log file of the current instance.'''
        ir_config_para_obj = self.env['ir.config_parameter']

        for rec in self:
            # get log file path from system para
            log_path = ir_config_para_obj.get_param('instance_logfile_path')
            if not log_path:
                raise UserError(
                    _("There is no key defined in the system parameter for Log file path with name 'instance_logfile_path'."))
            # prepare log file path
            log_file = log_path + rec.name + '.log'
            # check if log file is exist or not, if not it will create an empty file
            is_log_file = os.path.isfile(log_file)
            if not is_log_file:
                raise UserError(
                    _("There is no log file available for %s") % (rec.name))
            # read only last few lines of logfile
            with open(log_file, "r") as f:
                f.seek(0, 2)  # Seek @ EOF
                fsize = f.tell()  # Get Size
                f.seek(max(fsize - 15000, 0), 0)  # Set pos @ last n chars
                file_lines = f.readlines()
                file_data = " ".join(str(lines) for lines in file_lines)
            read_log_data = base64.b64encode(file_data.encode('UTF-8'))
        download_log_rec = self.env['download.log'].create({
            'name': rec.name,
            'file_download': read_log_data
        })
        return {
            'name': _('Log File'),
            'res_id': download_log_rec.id,
            'view_mode': 'form',
            'res_model': 'download.log',
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    def get_password(self):
        '''This method will fetch the root password defined in the company configuration.'''
        for rec in self:
            sudopassword = self.env.user and self.env.user.company_id and \
                self.env.user.company_id.root_password
            if not sudopassword:
                raise UserError(
                    _('Please configure Root Password in company Configuration!'))
            return sudopassword

    def validate(self):
        for rec in self:
            rec.state = 'confirm'

    def start_server(self):
        '''This method will start the instance.'''
        ir_config_para_obj = self.env['ir.config_parameter']
        for rec in self:
            # Check pid file
            pid_filepath = os.path.join(str(PID_FILE), rec.name + '.pid')
            # get daemon from system para
            daemon = rec.odoo_version and rec.odoo_version.value
            # get config file path from system para
            config_path = ir_config_para_obj.get_param('instance_config_path')
            if not config_path:
                raise UserError(
                    _("There is no key defined in the system parameter for Config file path with name 'instance_config_path'."))
            if not os.path.isdir(config_path):
                raise UserError(
                    _("There is no directory found %s to save the .conf file!" % config_path))
            # prepare config file path
            config_file = config_path + rec.name + '.conf'
            # check if config file is exist or not, if not it will create and write content for server configuration
            is_config_file = os.path.isfile(config_file)

            if not is_config_file:
                with io.FileIO(config_file, "w") as file:
                    file.write(rec.server_config.encode())

            # get log file path from system para
            log_path = ir_config_para_obj.get_param('instance_logfile_path')
            if not log_path:
                raise UserError(
                    _("There is no key defined in the system parameter for Log file path with name 'instance_logfile_path'."))
            if not os.path.isdir(log_path):
                raise UserError(
                    _("There is no directory found %s to save the .log file!" % log_path))
            # prepare log file path
            log_file = log_path + rec.name + '.log'
            # check if log file is exist or not, if not it will create an empty file
            is_log_file = os.path.isfile(log_file)
            if not is_log_file:
                open(log_file, "a").close()
            # get instance user from system para
            ins_user = ir_config_para_obj.get_param('instance_user')
            # get root password configured in the company
            sudoPassword = self.get_password()

            command = 'start-stop-daemon --start --quiet --pidfile ' + pid_filepath + \
                ' --chuid ' + ins_user + ':' + ins_user + ' --background --make-pidfile --exec ' + daemon + \
                ' -- --config ' + config_file + ' --logfile ' + log_file
            print("command", command)
            start_resp = os.system('echo %s|sudo -S %s' %
                                   (sudoPassword, command))
            if start_resp != 0:
                raise UserError(
                    _("Server is not starting, Please check configurations!"))
            user = self.env.user.name
            msg = _("Server is Started by %s " % user)
            self.sudo().message_post(body=msg)
            if os.path.isfile(pid_filepath):
                rec.pid = open(pid_filepath).read()
        return True

    def stop_server(self):
        '''This method will stop the current instance.'''
        for rec in self:
            pid_filepath = os.path.join(str(PID_FILE), rec.name + '.pid')
            # get root password configured in the company
            sudoPassword = self.get_password()
            command = 'start-stop-daemon --stop --quiet --pidfile ' + \
                pid_filepath + ' --oknodo --retry 3'
            os.system('echo %s|sudo -S %s' % (sudoPassword, command))
            os.system('echo %s|sudo -S %s' %
                      (sudoPassword, ' rm -f ' + pid_filepath))
            user = self.env.user.name
            msg = _("Server is Stopped by %s " % user)
            self.sudo().message_post(body=msg)
            rec.pid = ''
        return True

    def restart_server(self):
        for rec in self:
            self.stop_server()
            self.start_server()
            pid_filepath = os.path.join(str(PID_FILE), rec.name + '.pid')
            if os.path.isfile(pid_filepath):
                rec.pid = open(pid_filepath).read()
        return True

    def check_instance_status(self):
        '''Methods to check the status of the instance'''
        for rec in self:
            pid_filepath = os.path.join(str(PID_FILE), rec.name + '.pid')
            # get root password configured in the company
            sudoPassword = self.get_password()
            command = 'start-stop-daemon --status --pidfile ' + pid_filepath
            ins_res = os.system('echo %s|sudo -S %s' % (sudoPassword, command))
            if ins_res == 0:
                raise UserError(_("Current Instance is Running"))
            else:
                raise UserError(_("Current Instance is Stopped"))
        return True

    def restart_postgres(self):
        for rec in self:
            os.chdir(get_module_resource('instance_management', 'models'))
            sudoPassword = self.get_password()
            os.system('python3 restart_postgres.py %' % sudoPassword)
        return True

    @api.model
    def _search(self, domain, offset=0, limit=None, order=None, **kwargs):
        # See instance for instance user groups based on assigned instance.
        context = dict(self._context)
        if context.get('is_restrict_instence_based_on_users') and not self.user_has_groups('instance_management.instance_manager_group'):
            domain.append(('id', 'in', self.env.user.instance_ids.ids))
        return super()._search(domain, offset, limit, order, **kwargs)


class RepoRepo(models.Model):
    _name = 'repo.repo'
    _description = "Repo"

    name = fields.Char('Name', required=True)
    code = fields.Char('Code', required=True)


class BranchBranch(models.Model):
    _name = 'branch.branch'
    _description = "Branch"
    _rec_name = 'branch_path'

    branch_path = fields.Char('Branch Path')
    repo_id = fields.Many2one('repo.repo')
    instance_id = fields.Many2one('instance.instance', 'Instance')

    def get_revisions(self):
        '''This method will pull the latest source code from the server'''
        for rec in self:
            if not rec.repo_id:
                raise UserError(_("Please select Repository First!"))
            if rec.branch_path and rec.repo_id:
                if not os.path.isdir(rec.branch_path):
                    raise UserError(
                        _("There is no directory found %s!" % rec.branch_path))
                # change the current directory to branch directory and pull the code
                os.chdir(rec.branch_path)
                repo = rec.repo_id and rec.repo_id.code
                pull_resp = subprocess.call(repo + ' pull', shell=True)
                if pull_resp != 0:
                    raise UserError(
                        _("Something is wrong, Please contact the Admin to check the log."))
                else:
                    raise UserError(_("Code is updated Successfully!"))
        return True


class InstanceInfo(models.Model):
    _name = 'instance.info'
    _description = "Instance Info"

    version = fields.Char()
    instance_id = fields.Many2one('instance.instance', string="Instance")
    module_id = fields.Many2one('module.info', string="Module")
