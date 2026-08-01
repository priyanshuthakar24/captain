# See LICENSE file for full copyright and licensing details.

import os
import  logging
from odoo import _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)
from ..utils.file_utils import ensure_config_file, ensure_log_file, get_instance_pid_path, write_server_config
from ..utils.system_utils import get_system_parameter, require_system_parameter, run_command


class InstanceService:
    """Reusable service layer for instance lifecycle operations."""

    def __init__(self, env):
        self.env = env

    def sync_server_config(self, instance):
        """Persist the instance server config to the configured config path."""
        config_path = get_system_parameter(self.env, 'instance_config_path')
        if config_path:
            write_server_config(config_path, instance.name, instance.server_config or '')
        return config_path

    def ensure_runtime_files(self, instance):
        """Create config/log files and return their paths for a given instance."""
        config_path = require_system_parameter(self.env, 'instance_config_path')
        if not os.path.isdir(config_path):
            raise UserError(_("Directory %s to save .conf file does not exist!") % config_path)

        log_path = require_system_parameter(self.env, 'instance_logfile_path')
        if not os.path.isdir(log_path):
            raise UserError(_("Directory %s to save .log file does not exist!") % log_path)

        config_file = ensure_config_file(config_path, instance.name, instance.server_config or '')
        log_file = ensure_log_file(log_path, instance.name)
        return config_file, log_file

    def start(self, instance):
        """Start a single instance."""
        config_file, log_file = self.ensure_runtime_files(instance)
        pid_filepath = get_instance_pid_path(instance.name)
        daemon = instance.odoo_version and instance.odoo_version.value
        if not daemon:
            raise UserError(_('Please configure an Odoo version for this instance.'))

        ins_user = get_system_parameter(self.env, 'instance_user')
        sudo_password = instance.get_password()

        command = (
            f'start-stop-daemon --start --quiet --pidfile {pid_filepath} '
            f'--chuid {ins_user}:{ins_user} --background --make-pidfile '
            f'--exec {daemon} -- --config {config_file} --logfile {log_file}'
        )
        start_resp = run_command(command, sudo_password=sudo_password)
        if start_resp != 0:
            raise UserError(_('Server failed to start. Please check log configurations!'))

        instance.message_post(body=_('Server started by %s', self.env.user.name))
        if os.path.isfile(pid_filepath):
            with open(pid_filepath, 'r', encoding='utf-8') as pid_handle:
                instance.pid = pid_handle.read().strip()
        return True

    def stop(self, instance):
        """Stop a single instance."""
        pid_filepath = get_instance_pid_path(instance.name)
        sudo_password = instance.get_password()
        command = f'start-stop-daemon --stop --quiet --pidfile {pid_filepath} --oknodo --retry 3'
        run_command(command, sudo_password=sudo_password)
        run_command(f'rm -f {pid_filepath}', sudo_password=sudo_password)

        instance.message_post(body=_('Server stopped by %s', self.env.user.name))
        instance.pid = False
        return True

    def restart(self, instance):
        """Restart a single instance."""
        self.stop(instance)
        self.start(instance)
        return True

    def get_status(self, instance):
        """Return the runtime status string for an instance."""
        pid_filepath = get_instance_pid_path(instance.name)
        sudo_password = instance.get_password()
        command = f'start-stop-daemon --status --pidfile {pid_filepath}'
        status_resp = run_command(command, sudo_password=sudo_password)
        return 'Running' if status_resp == 0 else 'Stopped'

    def restart_postgres(self):
        """Restart PostgreSQL via systemctl."""
        sudo_password = self.env.company.root_password
        if not sudo_password:
            raise UserError(_('Please configure Root Password in Company Configuration!'))

        command = 'systemctl restart postgresql'
        result = run_command(command, sudo_password=sudo_password, capture_output=True)
        if result.returncode != 0:
            raise UserError(_('Failed to restart PostgreSQL service: %s') % result.stderr.strip())
        return True
