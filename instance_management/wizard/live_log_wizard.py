# -*- coding: utf-8 -*-

from odoo import api, fields, models


class LiveLogWizard(models.TransientModel):
    _name = "instance.live.log.wizard"
    _description = "Live Log Viewer"

    instance_id = fields.Many2one(
        "instance.instance",
        string="Instance",
        required=True,
        readonly=True,
    )

    log_text = fields.Text(
        string="Logs",
        readonly=True,
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)

        instance = self.env["instance.instance"].browse(
            self.env.context.get("default_instance_id")
        )

        if instance:
            res["instance_id"] = instance.id
            res["log_text"] = instance.get_latest_logs()

        return res