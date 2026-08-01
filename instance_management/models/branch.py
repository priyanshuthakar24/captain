from odoo import _, api, fields, models
from ..services import GitService

class BranchBranch(models.Model):
    _name = 'branch.branch'
    _description = "Branch"
    _rec_name = 'branch_path'

    branch_path = fields.Char(string='Branch Path')
    repo_id = fields.Many2one('repo.repo', string='Repository')
    instance_id = fields.Many2one('instance.instance', string='Instance')

    def _get_git_service(self):
        return GitService(self.env)

    def get_revisions(self):
        outputs = []
        for rec in self:
            outputs.append(self._get_git_service().pull_repository(rec))

        message = outputs[-1] if outputs else _('Git pull completed successfully.')
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Git Pull"),
                "message": message,
                "type": "success",
                "sticky": True,
            },
        }