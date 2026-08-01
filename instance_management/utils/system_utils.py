# See LICENSE file for full copyright and licensing details.

import subprocess

from odoo import _
from odoo.exceptions import UserError


def get_system_parameter(env, key):
    """Fetch a system parameter for the current environment."""
    return env['ir.config_parameter'].sudo().get_param(key)


def require_system_parameter(env, key):
    """Fetch a required system parameter or raise a user-friendly error."""
    value = get_system_parameter(env, key)
    if not value:
        raise UserError(_("System parameter '%s' is missing.") % key)
    return value


def run_command(command, sudo_password=None, *, check=False, capture_output=False):
    """Run a shell command, optionally with sudo via password input."""
    shell_command = command
    if sudo_password:
        shell_command = f'echo "{sudo_password}" | sudo -S {command}'

    kwargs = {'shell': True, 'text': True}
    if capture_output:
        kwargs.update({'stdout': subprocess.PIPE, 'stderr': subprocess.PIPE})

    try:
        completed = subprocess.run(shell_command, check=check, **kwargs)
    except subprocess.CalledProcessError as exc:
        if capture_output:
            raise
        return exc.returncode

    if capture_output:
        return completed
    return completed.returncode
