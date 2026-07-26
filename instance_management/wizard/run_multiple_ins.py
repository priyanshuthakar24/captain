# See LICENSE file for full copyright and licensing details.

from odoo import api, models


class RunMultipleIns(models.TransientModel):
    _name = 'run.multiple.ins'
    _description = "Run Multiple Instance"

    @api.model
    def get_ins(self, data):
        # get the active id and model from context
        active_ids = data.get('active_ids')
        active_model = data.get('active_model')
        if active_model == 'instance.instance' and active_ids:
            return self.env[active_model].browse(active_ids)
        return self.env['instance.instance']

    def start(self):
        ins_rec = self.get_ins(self._context)
        for rec in ins_rec:
            rec.start_server()
        return True

    def stop(self):
        ins_rec = self.get_ins(self._context)
        for rec in ins_rec:
            rec.stop_server()
        return True

    def restart(self):
        ins_rec = self.get_ins(self._context)
        for rec in ins_rec:
            rec.restart_server()
        return True
