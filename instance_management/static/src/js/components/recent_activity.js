/** @odoo-module **/

import { Component } from "@odoo/owl";

export class RecentActivity extends Component {
    static template = "instance_management.RecentActivity";

    static props = {
        activities: Array,
    };
}