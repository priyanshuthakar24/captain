from odoo import _, fields, models

class InstanceInfo(models.Model):
    _name = 'instance.info'
    _description = "Instance Info"

    version = fields.Char(string='Version')
    instance_id = fields.Many2one('instance.instance', string="Instance")
    module_id = fields.Many2one('module.info', string="Module")