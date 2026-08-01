from odoo import _, fields, models

class RepoRepo(models.Model):
    _name = 'repo.repo'
    _description = "Repo"

    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code', required=True)
