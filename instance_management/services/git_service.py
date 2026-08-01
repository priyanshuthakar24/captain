# See LICENSE file for full copyright and licensing details.

import base64
import os
import subprocess

from odoo import _
from odoo.exceptions import UserError


class GitService:
    """Reusable service layer for git repository operations."""

    def __init__(self, env):
        self.env = env

    def pull_repository(self, branch):
        """Pull the latest revision for a branch repository."""
        if not branch.repo_id:
            raise UserError(_('Please select a repository.'))
        if not branch.branch_path:
            raise UserError(_('Branch path is missing.'))
        if not os.path.isdir(branch.branch_path):
            raise UserError(_('Directory not found:\n%s') % branch.branch_path)

        user = self.env.user
        username = user.git_username
        token = user.git_pat
        if not username:
            raise UserError(_('GitHub Username is missing in your User Preferences.'))
        if not token:
            raise UserError(_('Please configure your Git Personal Access Token in your User Preferences.'))

        auth = base64.b64encode(f'{username}:{token}'.encode()).decode()
        result = subprocess.run(
            [
                'git',
                '-c',
                f'http.extraHeader=Authorization: Basic {auth}',
                'pull',
            ],
            cwd=branch.branch_path,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise UserError(_('Git Pull Failed\n\n%s') % result.stderr)

        output = result.stdout.strip() or _('Git pull completed successfully.')
        return output
