/** @odoo-module **/

import { Component } from "@odoo/owl";

export class InstancesTable extends Component {

    static template = "instance_management.InstancesTable";

    static props = {
        instances: Array,
    }

}