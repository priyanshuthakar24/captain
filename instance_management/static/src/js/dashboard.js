/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, useState, onWillStart } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

import { Header } from "./components/header";
import { Stats } from "./components/stats";
import { ChartPlaceholder } from "./components/chart_placeholder";
import { RecentActivity } from "./components/recent_activity";
import { InstancesTable } from "./components/instances_table";

export class CaptainDashboard extends Component {

    static template = "instance_management.CaptainDashboard";

    static components = {
        Header,
        Stats,
        ChartPlaceholder,
        RecentActivity,
        InstancesTable,
    };

    setup() {

        this.orm = useService("orm");

        this.state = useState({
            total_instances: 0,
            running_instances: 0,
            stopped_instances: 0,
            databases: 0,
            recent_instances: [],
        });

        onWillStart(async () => {
            await this.loadDashboard();
        });

    }

    async loadDashboard() {

       const data = await this.orm.call(
        "instance.instance",
        "get_dashboard_data",
        []
    );

    Object.assign(this.state, data);

    }

}

registry.category("actions").add(
    "instance_management.dashboard",
    CaptainDashboard
);