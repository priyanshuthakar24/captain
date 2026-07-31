/** @odoo-module **/

import { Component, useRef, onMounted } from "@odoo/owl";

export class ChartPlaceholder extends Component {

    static template = "instance_management.ChartPlaceholder";

    static props = {
        state: Object,
    };

    setup() {

        this.chartCanvas = useRef("chartCanvas");

        onMounted(() => {

            const ctx = this.chartCanvas.el.getContext("2d");

            new Chart(ctx, {
                type: "doughnut",

                data: {
                    labels: ["Running", "Stopped"],

                    datasets: [{
                        data: [
                            this.props.state.running_instances,
                            this.props.state.stopped_instances,
                        ],

                        backgroundColor: [
                            "#22c55e",
                            "#ef4444",
                        ],

                        borderWidth: 0,
                    }],
                },

                options: {

                    responsive: true,

                    maintainAspectRatio: false,

                    plugins: {
                        legend: {
                            position: "bottom",
                        },
                    },
                },
            });

        });

    }

}