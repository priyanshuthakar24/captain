/** @odoo-module **/

import { Component, onMounted, onWillUnmount, useState } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";
import { useService } from "@web/core/utils/hooks";

export class LiveLogDialog extends Component {
    static template = "instance_management.LiveLogDialog";
    static components = { Dialog };

    static props = {
        instanceId: Number,
        instanceName: String,
        close: Function,
    };

    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.state = useState({
            logs: "",
            offset: 0,
            firstLoad: true,
            autoRefresh: true,
        });

        this.timer = null;

        onMounted(async () => {
            await this.loadLogs();

            this.timer = setInterval(async () => {
                if (this.state.autoRefresh) {
                    await this.loadLogs();
                }
            }, 2000);
        });

        onWillUnmount(() => {
            if (this.timer) {
                clearInterval(this.timer);
            }
        });
    }

    async loadLogs() {

        const logContainer = document.getElementById("captain_live_log");

        let shouldScroll = true;

        if (logContainer) {
            shouldScroll =
                logContainer.scrollTop + logContainer.clientHeight >=
                logContainer.scrollHeight - 20;
        }

        if (this.loading) {
            return;
        }

        this.loading = true;

        try {

            const isFirstLoad = this.state.firstLoad;

            const result = await this.orm.call(
                "instance.instance",
                "get_live_logs",
                [
                    [this.props.instanceId],
                    this.state.offset,
                ]
            );

            if (isFirstLoad) {
                this.state.logs = result.logs;
                this.state.firstLoad = false;
            } else if (result.logs) {
                this.state.logs += result.logs;
            }

            // Keep only last 1000 lines
            const lines = this.state.logs.split("\n");

            if (lines.length > 1000) {
                this.state.logs = lines.slice(-1000).join("\n");
            }

            this.state.offset = result.offset;

            setTimeout(() => {

                const logContainer = document.getElementById("captain_live_log");

                if (!logContainer) {
                    return;
                }

                if (isFirstLoad) {
                    logContainer.scrollTop = logContainer.scrollHeight;
                    return;
                }

                if (shouldScroll) {
                    logContainer.scrollTop = logContainer.scrollHeight;
                }

            }, 50);

        } catch (err) {

            console.error("Failed to load logs:", err);

        } finally {

            this.loading = false;

        }

    }

    toggleRefresh() {
        this.state.autoRefresh = !this.state.autoRefresh;
        console.log('refresh clicked')
        this.notification.add(
            this.state.autoRefresh
                ? "Live refresh resumed."
                : "Live refresh paused.",
            {
                type: this.state.autoRefresh ? "success" : "warning",
            }
        );

    }

    async copyLogs() {
        try {
            if (navigator.clipboard && window.isSecureContext) {
                await navigator.clipboard.writeText(this.state.logs);
            } else {
                const textArea = document.createElement("textarea");
                textArea.value = this.state.logs;

                textArea.style.position = "fixed";
                textArea.style.left = "-9999px";

                document.body.appendChild(textArea);

                textArea.focus();
                textArea.select();

                document.execCommand("copy");

                document.body.removeChild(textArea);
            }

            this.notification?.add("Logs copied!", {
                type: "success",
            });

        } catch (e) {
            this.notification.add(
                "Unable to copy logs.",
                {
                    type: "danger",
                }
            );
        }
    }
    clearLogs() {

        this.state.logs = "";

    }
    downloadLogs() {

        const blob = new Blob(
            [this.state.logs],
            {
                type: "text/plain",
            }
        );

        const url = URL.createObjectURL(blob);

        const a = document.createElement("a");

        a.href = url;
        a.download = `${this.props.instanceName}.log`;

        a.click();

        URL.revokeObjectURL(url);

    }
    async refreshLogs() {

        this.state.logs = "";
        this.state.offset = 0;
        this.state.firstLoad = true;

        await this.loadLogs();

    }
}