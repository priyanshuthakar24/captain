# -*- coding: utf-8 -*-

from odoo import _, api, fields, models
import configparser
import os

from odoo.exceptions import UserError

class ImportInstanceWizard(models.TransientModel):
    _name = "instance.import.wizard"
    _description = "Import Existing Odoo Instance"

    config_file = fields.Char(
        string="Configuration File",
        required=True,
        help="Absolute path of the Odoo configuration file."
    )

    instance_name = fields.Char(
        string="Instance Name",
        readonly=True,
    )

    version = fields.Char(
        string="Odoo Version",
        readonly=True,
    )

    database = fields.Char(
        string="Database",
        readonly=True,
    )

    http_port = fields.Integer(
        string="HTTP Port",
        readonly=True,
    )
    gevent_port = fields.Integer(
        string="Gevent Port",
        readonly=True,
    )

    addons_path = fields.Text(
        string="Addons Path",
        readonly=True,
    )

    logfile = fields.Char(
        string="Log File",
        readonly=True,
    )

    data_dir = fields.Char(
        string="Data Directory",
        readonly=True,
    )

    working_directory = fields.Char(
        string="Working Directory",
        readonly=True,
    )

    def action_load_configuration(self):
        self.ensure_one()

        config_path = self.config_file.strip()

        # Check file exists
        if not os.path.isfile(config_path):
            raise UserError(_("Configuration file not found:\n%s") % config_path)

        parser = configparser.ConfigParser()

        try:
            parser.read(config_path)
        except Exception as e:
            raise UserError(_("Unable to read configuration file.\n\n%s") % str(e))

        if not parser.has_section("options"):
            raise UserError(_("Invalid Odoo configuration file."))

        options = parser["options"]

        self.instance_name = (
            os.path.splitext(os.path.basename(config_path))[0]
        )

        self.database = options.get("dbfilter", "")

        self.http_port = int(options.get("http_port", 8069))
        self.gevent_port=int(options.get("gevent_port",8072))

        self.logfile = options.get("logfile", "")

        self.data_dir = options.get("data_dir", "")

        self.addons_path = options.get("addons_path", "")

        self.working_directory = self._get_working_directory(
            self.addons_path
        )

        self.version = self._detect_version(
            self.addons_path
        )

        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "view_mode": "form",
            "res_id": self.id,
            "target": "new",
        }

    def action_import(self):
        self.ensure_one()

        if not self.instance_name:
            raise UserError(_("Please load the configuration first."))

        instance_model = self.env["instance.instance"]

        existing = instance_model.search([
            ("config_file", "=", self.config_file)
        ], limit=1)

        if existing:
            raise UserError(_("This instance has already been imported."))

        instance = instance_model.create({
            "name": self.instance_name,
            "config_file": self.config_file,
            "working_directory": self.working_directory,
            "odoo_version":self.version,
            "db_name":self.database,
            "gevent_port":self.gevent_port,
            "http_port":self.http_port            
        })

        return {
            "type": "ir.actions.act_window",
            "res_model": "instance.instance",
            "res_id": instance.id,
            "view_mode": "form",
            "target": "current",
        }
    
    
    def _get_working_directory(self, addons_path):
        """
        Guess the Odoo workspace directory.
        """

        if not addons_path:
            return ""

        first_path = addons_path.split(",")[1].strip()

        current = os.path.abspath(first_path)

        while current != "/":

            if os.path.isfile(os.path.join(current, "odoo-bin")):
                return current

            current = os.path.dirname(current)

        return ""
    def _detect_version(self, addons_path):
        """
        Detect Odoo version from release.py
        """
        if not addons_path:
            return ""

        first_path = addons_path.split(",")[1].strip()
        current = os.path.abspath(first_path)
        while current != "/":

            release = os.path.join(
                current,
                "odoo",
                "release.py"
            )
            if os.path.isfile(release):

                namespace = {}

                with open(release, "r") as fp:
                    exec(fp.read(), namespace)

                version = namespace.get("version_info")

                if version:
                    return "%s.%s" % (
                        version[0],
                        version[1]
                    )

            current = os.path.dirname(current)
        return ""
    
    
    def action_refresh_configuration(self):
        for instance in self:
            values = instance._parse_config(instance.config_file)

            instance.write({
                "working_directory": values["working_directory"],
                "version": values["version"],
                "database": values["database"],
                "http_port": values["http_port"],
                "addons_path": values["addons_path"],
                "logfile": values["logfile"],
                "data_dir": values["data_dir"],
            })
            
    def _load_configuration(self):
        values = self._parse_config(self.config_file)

        self.write({
            "version": values["version"],
            "database": values["database"],
            "http_port": values["http_port"],
            "addons_path": values["addons_path"],
            "working_directory": values["working_directory"],
            "logfile": values["logfile"],
            "data_dir": values["data_dir"],
        })
    def _parse_config(self, config_path):
        """Parse an Odoo configuration file and return its values."""

        if not config_path:
            raise UserError(_("Configuration file is required."))

        config_path = os.path.abspath(config_path)

        if not os.path.isfile(config_path):
            raise UserError(
                _("Configuration file not found:\n%s") % config_path
            )

        parser = configparser.ConfigParser()

        try:
            parser.read(config_path)
        except Exception as e:
            raise UserError(
                _("Unable to read configuration file.\n\n%s") % str(e)
            )

        if not parser.has_section("options"):
            raise UserError(_("Invalid Odoo configuration file."))

        options = parser["options"]

        addons_path = options.get("addons_path", "")
        working_directory = self._get_working_directory(addons_path)
        version = self._detect_version(addons_path)

        return {
            "instance_name": os.path.splitext(
                os.path.basename(config_path)
            )[0],

            "config_file": config_path,

            "database": options.get("db_name", ""),

            "http_port": int(options.get("http_port", 8069)),

            "addons_path": addons_path,

            "logfile": options.get("logfile", ""),

            "data_dir": options.get("data_dir", ""),

            "working_directory": working_directory,

            "version": version,

            "proxy_mode": options.getboolean(
                "proxy_mode",
                fallback=False,
            ),

            "workers": int(
                options.get("workers", 0)
            ),

            "limit_memory_hard": int(
                options.get("limit_memory_hard", 0)
            ),

            "limit_memory_soft": int(
                options.get("limit_memory_soft", 0)
            ),

            "limit_time_cpu": int(
                options.get("limit_time_cpu", 0)
            ),

            "limit_time_real": int(
                options.get("limit_time_real", 0)
            ),

            "max_cron_threads": int(
                options.get("max_cron_threads", 0)
            ),
        }