# See LICENSE file for full copyright and licensing details.

import base64  # Used when downloading log files to transfer binary data
import os.path # Used to navigate files and directories
import subprocess # Runs external OS processes
import logging

_logger = logging.getLogger(__name__)
from lxml import etree # Used to manipulate XML architectures dynamically

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.modules.module import get_resource_from_path  # moved from odoo.modules in v19
from odoo.osv import expression
from odoo.fields import Domain
from odoo.tools import html2plaintext

PID_FILE = '/var/run/'

DEFAULT_SERVER_CONFIG = """[options]
admin_passwd = captain_v19ce@dm!n
db_host = False
db_port = False
db_user = serpentcs
db_password = False
addons_path = /home/serpentcs/workspace/odoo_ce/19.0CE/addons,/home/serpentcs/workspace/odoo_ce/19.0CE/odoo/addons
log_level = info
cpu_time_limit = 3600
limit_time_real = 3600
http_port = 
dbfilter = """

class InstanceInstance(models.Model):
    _name = 'instance.instance'
    _description = "Instance"
    _inherit = ['mail.thread']

    name = fields.Char(string='Name', required=True)
    odoo_version = fields.Many2one('ir.config_parameter', string='Version')
    branch_ids = fields.One2many('branch.branch', 'instance_id', string='Branch')
    state = fields.Selection([
        ('draft', 'Draft'), 
        ('confirm', 'Confirm')
    ], string='State', default='draft', tracking=True)
    server_config = fields.Text(string='Server Configuration',default=DEFAULT_SERVER_CONFIG)
    status = fields.Char(compute="_compute_instance_status", string='Status')
    http_port = fields.Integer(string='Http Port')
    pid = fields.Char(string='Process ID')
    db_name = fields.Char(string="Database Name")
    requested_by = fields.Char(string="Requested By")
    gevent_port = fields.Char(string="Gevent Port")

    config_file = fields.Char(string="Configuration File",help="Absolute path of the Odoo configuration file.")
    working_directory = fields.Char(string="Working Directory")
    
    _sql_constraints = [
        ('gevent_port_unique', 'UNIQUE(gevent_port)', 'Gevent Port must be unique!')
    ]

    def _compute_instance_status(self):
        for rec in self:
            if rec.name:
                pid_filepath = os.path.join(str(PID_FILE), rec.name + '.pid')
                sudo_password = rec.get_password()
                command = f'start-stop-daemon --status --pidfile {pid_filepath}'
                status_res = os.system(f'echo "{sudo_password}"|sudo -S {command}')
                rec.status = 'Running' if status_res == 0 else 'Stopped'
            else:
                rec.status = 'Stopped'

    @api.model
    def get_view(self, view_id=None, view_type='form', **options):
        '''Override method to disable create/edit buttons for non-managers.'''
        res = super().get_view(view_id=view_id, view_type=view_type, **options)
        
        # In modern Odoo, use has_group for privilege checking
        if not self.env.user.has_groups('instance_management.instance_manager_group'):
            doc = etree.XML(res['arch'])
            if view_type in ('tree', 'list'):
                nodes = doc.xpath("//tree") + doc.xpath("//list")
                for node in nodes:
                    node.set('create', 'false')
                    node.set('edit', 'false')
                res['arch'] = etree.tostring(doc, encoding='unicode')
            elif view_type == 'form':
                nodes = doc.xpath("//form")
                for node in nodes:
                    node.set('create', 'false')
                    node.set('edit', 'false')
                res['arch'] = etree.tostring(doc, encoding='unicode')
        return res

    def write(self, vals):
        '''Update the server configuration file on save.'''
        res = super().write(vals)
        ir_config_para_obj = self.env['ir.config_parameter']
        for rec in self:
            config_path = ir_config_para_obj.sudo().get_param('instance_config_path')
            if config_path:
                config_file = os.path.join(config_path, rec.name + '.conf')
                if vals.get('server_config') and os.path.isfile(config_file):
                    with open(config_file, "w", encoding="utf-8") as file:
                        file.write(rec.server_config or '')
        return res
#! New to work on this method to show the live log's
    def download_logfile(self):
        '''Provides log file downloading functionality.'''
        ir_config_para_obj = self.env['ir.config_parameter'].sudo()

        for rec in self:
            log_path = ir_config_para_obj.get_param('instance_logfile_path')
            if not log_path:
                raise UserError(_("There is no system parameter defined for 'instance_logfile_path'."))
            
            log_file = os.path.join(log_path, rec.name + '.log')
            if not os.path.isfile(log_file):
                raise UserError(_("No log file available for %s", rec.name))
            
            with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
                f.seek(0, 2)  # Seek EOF
                fsize = f.tell()
                f.seek(max(fsize - 15000, 0), 0)  # Read last 15k chars
                file_lines = f.readlines()
                file_data = "".join(file_lines)

            read_log_data = base64.b64encode(file_data.encode('utf-8'))

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
        '''Fetches the root password defined in company configuration.'''
        self.ensure_one()
        sudo_password = self.env.company.root_password
        if not sudo_password:
            raise UserError(_('Please configure Root Password in Company Configuration!'))
        return sudo_password

    def validate(self):
        for rec in self:
            rec.state = 'confirm'

    def start_server(self):
        '''Starts the server instance.'''
        ir_config_para_obj = self.env['ir.config_parameter'].sudo()
        for rec in self:
            pid_filepath = os.path.join(str(PID_FILE), rec.name + '.pid')
            daemon = rec.odoo_version and rec.odoo_version.value
            config_path = ir_config_para_obj.get_param('instance_config_path')
            
            if not config_path:
                raise UserError(_("System parameter 'instance_config_path' is missing."))
            if not os.path.isdir(config_path):
                raise UserError(_("Directory %s to save .conf file does not exist!", config_path))
            
            config_file = os.path.join(config_path, rec.name + '.conf')
            if not os.path.isfile(config_file):
                with open(config_file, "w", encoding="utf-8") as file:
                    file.write(rec.server_config or '')

            log_path = ir_config_para_obj.get_param('instance_logfile_path')
            if not log_path:
                raise UserError(_("System parameter 'instance_logfile_path' is missing."))
            if not os.path.isdir(log_path):
                raise UserError(_("Directory %s to save .log file does not exist!", log_path))
            
            log_file = os.path.join(log_path, rec.name + '.log')
            if not os.path.isfile(log_file):
                open(log_file, "a").close()
            
            ins_user = ir_config_para_obj.get_param('instance_user')
            sudo_password = rec.get_password()

            command = f'start-stop-daemon --start --quiet --pidfile {pid_filepath} --chuid {ins_user}:{ins_user} --background --make-pidfile --exec {daemon} -- --config {config_file} --logfile {log_file}'
            start_resp = os.system(f'echo "{sudo_password}"|sudo -S {command}')
            if start_resp != 0:
                raise UserError(_("Server failed to start. Please check log configurations!"))
            
            rec.message_post(body=_("Server started by %s", self.env.user.name))
            if os.path.isfile(pid_filepath):
                with open(pid_filepath, 'r') as pf:
                    rec.pid = pf.read().strip()
        return True

    def stop_server(self):
        '''Stops the server instance.'''
        for rec in self:
            pid_filepath = os.path.join(str(PID_FILE), rec.name + '.pid')
            sudo_password = rec.get_password()
            command = f'start-stop-daemon --stop --quiet --pidfile {pid_filepath} --oknodo --retry 3'
            os.system(f'echo "{sudo_password}"|sudo -S {command}')
            os.system(f'echo "{sudo_password}"|sudo -S rm -f {pid_filepath}')
            
            rec.message_post(body=_("Server stopped by %s", self.env.user.name))
            rec.pid = False
        return True

    def restart_server(self):
        for rec in self:
            rec.stop_server()
            rec.start_server()
        return True

    def check_instance_status(self):
        for rec in self:
            pid_filepath = os.path.join(str(PID_FILE), rec.name + '.pid')
            sudo_password = rec.get_password()
            command = f'start-stop-daemon --status --pidfile {pid_filepath}'
            ins_res = os.system(f'echo "{sudo_password}"|sudo -S {command}')
            if ins_res == 0:
                raise UserError(_("Current Instance is Running"))
            else:
                raise UserError(_("Current Instance is Stopped"))
        return True

    def restart_postgres(self):
        for rec in self:
            sudo_password = rec.get_password()
            
            # Prepare the command: echoes sudo password into 'sudo -S' to run non-interactively
            cmd = f'echo "{sudo_password}" | sudo -S systemctl restart postgresql'
            
            try:
                result = subprocess.run(
                    cmd,
                    shell=True,
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                _logger.info("PostgreSQL service restarted successfully.")
            except subprocess.CalledProcessError as e:
                _logger.error("Failed to restart PostgreSQL: %s", e.stderr)
                raise UserError(f"Failed to restart PostgreSQL service: {e.stderr}")
            
        return True

    @api.model
    def _search(self, domain, offset=0, limit=None, order=None, **kwargs):
        if self.env.context.get('is_restrict_instence_based_on_users') and not self.env.user.has_groups('instance_management.instance_manager_group'):
            allowed_ids = self.env.user.with_context(is_restrict_instence_based_on_users=False).instance_ids.ids
            domain = Domain.AND([domain, [('id', 'in', allowed_ids)]])
        return super()._search(domain, offset=offset, limit=limit, order=order, **kwargs)
    @api.model
    def get_dashboard_data(self):
        instance_obj = self.with_context(
        is_restrict_instence_based_on_users=True
    )

        instances = instance_obj.search([], limit=10)

        running = 0
        stopped = 0

        for rec in instance_obj.search([]):
            if rec.status == "Running":
                running += 1
            else:
                stopped += 1
        messages = self.env["mail.message"].search(
            [
                ("model", "=", "instance.instance"),
            ],
            order="date desc",
            limit=5,
        )
        recent_activity = []

        for msg in messages:
            if not msg.body:
                continue

            recent_activity.append({
                "id": msg.id,
                "instance": msg.record_name,
                "message": html2plaintext(msg.body),
                "date": msg.date.strftime("%d %b %Y %H:%M"),
                "author": msg.author_id.name if msg.author_id else "System",
            })
        #_logger.info("Recent Activity Count: %s", len(recent_activity))
        #_logger.info("Recent Activity: %s", recent_activity)
        return {
            "total_instances": instance_obj.search_count([]),
            "running_instances": running,
            "stopped_instances": stopped,
            "databases": instance_obj.search_count([]),
            "recent_instances": [
                {
                    "id": rec.id,
                    "name": rec.name,
                    "version": rec.odoo_version.value if rec.odoo_version else "",
                    "status": rec.status,
                    "database": rec.db_name or "",
                }
                for rec in instances
            ],
            "recent_activity": recent_activity,
        }

class RepoRepo(models.Model):
    _name = 'repo.repo'
    _description = "Repo"

    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code', required=True)


class BranchBranch(models.Model):
    _name = 'branch.branch'
    _description = "Branch"
    _rec_name = 'branch_path'

    branch_path = fields.Char(string='Branch Path')
    repo_id = fields.Many2one('repo.repo', string='Repository')
    instance_id = fields.Many2one('instance.instance', string='Instance')

    def get_revisions(self):
        for rec in self:
            if not rec.repo_id:
                raise UserError(_("Please select Repository First!"))
            if rec.branch_path and rec.repo_id:
                if not os.path.isdir(rec.branch_path):
                    raise UserError(_("Directory %s not found!", rec.branch_path))
                os.chdir(rec.branch_path)
                repo = rec.repo_id.code
                pull_resp = subprocess.call(f"{repo} pull", shell=True)
                if pull_resp != 0:
                    raise UserError(_("Something went wrong, please check server logs."))
                else:
                    raise UserError(_("Code updated successfully!"))
        return True


class InstanceInfo(models.Model):
    _name = 'instance.info'
    _description = "Instance Info"

    version = fields.Char(string='Version')
    instance_id = fields.Many2one('instance.instance', string="Instance")
    module_id = fields.Many2one('module.info', string="Module")