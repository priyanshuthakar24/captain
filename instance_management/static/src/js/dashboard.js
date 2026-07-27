/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component } from "@odoo/owl";

import { Header } from "./components/header";
import { Stats } from "./components/stats";
import { StatCard } from "./components/stat_card";
import { ChartPlaceholder } from "./components/chart_placeholder";
import { RecentActivity } from "./components/recent_activity";
import { InstancesTable } from "./components/instances_table";


export class CaptainDashboard extends Component {

    static components = {
        Header,
        Stats,
        ChartPlaceholder,
        RecentActivity,
        InstancesTable,
    };

}

CaptainDashboard.template = "instance_management.CaptainDashboard";

registry.category("actions").add(
    "instance_management.dashboard",
    CaptainDashboard
);  