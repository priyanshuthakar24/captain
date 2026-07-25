# See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ModuleIndustry(models.Model):
    _name = 'module.industry'
    _description = "Module Industry"

    name = fields.Char()


class ModuleInfo(models.Model):
    _name = 'module.info'
    _description = "Module Info"

    name = fields.Char()
    tech_name = fields.Char("Technical Name")
    info = fields.Text("Module Info")
    industry_id = fields.Many2one('module.industry', "Industry")
    responsibles = fields.Many2many('res.users', string="Responsibles")
    avail_versions = fields.Char("Available versions")
    instance_ids = fields.One2many('instance.info', 'module_id', string="Instances")
