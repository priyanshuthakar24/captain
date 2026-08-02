# See LICENSE file for full copyright and licensing details.

import base64  # Used when downloading log files to transfer binary data
import logging
import os.path  # Used to navigate files and directories

_logger = logging.getLogger(__name__)
from lxml import etree  # Used to manipulate XML architectures dynamically

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.fields import Domain
from odoo.tools import html2plaintext

from ..services import GitService, InstanceService
from ..utils import read_log_tail, require_system_parameter , DEFAULT_SERVER_CONFIG


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

    def _get_instance_service(self):
        return InstanceService(self.env)

    def _get_git_service(self):
        return GitService(self.env)

    def _compute_instance_status(self):
        for rec in self:
            if rec.name:
                rec.status = rec._get_instance_service().get_status(rec)
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
        for rec in self:
            if vals.get('server_config'):
                rec._get_instance_service().sync_server_config(rec)
        return res

    #! New to work on this method to show the live log's
    def download_logfile(self):
        '''Provides log file downloading functionality.'''
        for rec in self:
            log_path = require_system_parameter(self.env, 'instance_logfile_path')
            log_file = os.path.join(log_path, rec.name + '.log')
            if not os.path.isfile(log_file):
                raise UserError(_("No log file available for %s", rec.name))

            file_data = read_log_tail(log_file, size=15000)
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
        for rec in self:
            rec._get_instance_service().start(rec)
        return True

    def stop_server(self):
        '''Stops the server instance.'''
        for rec in self:
            rec._get_instance_service().stop(rec)
        return True

    def restart_server(self):
        for rec in self:
            rec._get_instance_service().restart(rec)
        return True

    def check_instance_status(self):
        for rec in self:
            status = rec._get_instance_service().get_status(rec)
            if status == 'Running':
                raise UserError(_("Current Instance is Running"))
            raise UserError(_("Current Instance is Stopped"))
        return True

    def restart_postgres(self):
        self._get_instance_service().restart_postgres()
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
        
    def action_bulk_start(self):
        failed = []

        for instance in self:
            try:
                if instance.status != "Running":
                    instance._get_instance_service().start(instance)
            except Exception as e:
                failed.append(f"{instance.name}: {e}")
                _logger.exception("Failed to start %s", instance.name)

        if failed:
            raise UserError(
                _("Some instances failed to start:\n\n%s") % "\n".join(failed)
            )

        return True
    
    def action_bulk_stop(self):
        for instance in self:
            try:
                if instance.status == "Running":
                    instance._get_instance_service().stop(instance)
            except Exception as e:
                _logger.exception(e)

        return True
    
    def action_bulk_restart(self):
        for instance in self:
            try:
                instance._get_instance_service().restart(instance)
            except Exception as e:
                _logger.exception(e)

        return True
    
    def get_latest_logs(self):
        self.ensure_one()

        log_path = require_system_parameter(
            self.env,
            "instance_logfile_path",
        )

        logfile = os.path.join(
            log_path,
            f"{self.name}.log",
        )

        if not os.path.isfile(logfile):
            return "No log file found."

        return read_log_tail(
            logfile,
            size=15000,
        )
    
    def action_live_logs(self):
        self.ensure_one()

        return {
            "type": "ir.actions.client",
            "tag": "captain_live_log",
            "params": {
                "instanceId": self.id,
                "instanceName": self.name,
            },
        }
        
    import os

    def get_live_logs(self, offset=0):
        self.ensure_one()

        log_path = require_system_parameter(
            self.env,
            "instance_logfile_path",
        )

        logfile = os.path.join(
            log_path,
            f"{self.name}.log",
        )

        if not os.path.isfile(logfile):
            return {
                "logs": "",
                "offset": 0,
            }

        filesize = os.path.getsize(logfile)

        if offset > filesize:
            offset = 0

        if offset == 0:
            offset = max(0, filesize - 20000)

        with open(logfile, "rb") as fp:
            fp.seek(offset)
            logs = fp.read()
            offset = fp.tell()

        return {
            "logs": logs.decode("utf-8", errors="ignore"),
            "offset": offset,
        }