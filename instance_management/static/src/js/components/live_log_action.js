/** @odoo-module **/

import { registry } from "@web/core/registry";
import { LiveLogDialog } from "./live_log_dialog";

registry.category("actions").add("captain_live_log", (env, action) => {

    env.services.dialog.add(LiveLogDialog, {
        instanceId: action.params.instanceId,
        instanceName: action.params.instanceName,
    });

});