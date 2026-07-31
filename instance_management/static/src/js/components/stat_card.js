/** @odoo-module **/

import { Component } from "@odoo/owl";

export class StatCard extends Component {

    static template = "instance_management.StatCard";

    static props = {
        title: String,
        value: Number,
        subtitle: String,
        icon: String,
        color: String,
        onClick: { type: Function, optional: true },
    };
}