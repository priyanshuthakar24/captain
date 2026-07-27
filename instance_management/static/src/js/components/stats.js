/** @odoo-module **/

import { Component } from "@odoo/owl";
import { StatCard } from "./stat_card";

export class Stats extends Component {

    static components = {
        StatCard,
    };

}

Stats.template = "instance_management.Stats";