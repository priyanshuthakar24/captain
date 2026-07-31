/** @odoo-module **/

import { Component } from "@odoo/owl";
import { StatCard } from "./stat_card";

export class Stats extends Component {

    static template = "instance_management.Stats";

    static components = {
        StatCard,
    };
static props = {
    state: Object,
    openInstances: Function,
};
}