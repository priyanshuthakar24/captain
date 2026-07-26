# See LICENSE file for full copyright and licensing details.

{
    'name': 'Captain',
    'summary': 'Manage, monitor and operate multiple Odoo environments from a single interface.',
    'version': '19.0.1.0.0',
    'author': 'Priyanshu Thakar',
    'maintainer': 'Priyanshu Thakar',
    'website': 'https://github.com/priyanshuthakar24/captain',
    'category': 'Administration',
    'license': 'LGPL-3',
    'description': """
Captain
========

Captain is an open-source platform for managing multiple Odoo
development, staging, and production environments from a single interface.

Features
--------
* Manage multiple Odoo instances.
* Start, stop, and restart Odoo services.
* Monitor instance status and process information.
* Download and inspect instance log files.
* Manage multiple Odoo versions.
* Configure ports, configuration files, and log directories.
* Control user access to instances.
* Developer-friendly environment management.

Configuration
-------------
Configure the required System Parameters for:

* Odoo version directories
* Configuration file directory
* Log file directory
* Service management
    """,
    'depends': [
        'mail',
    ],
    'data': [
        'data/instance_data.xml',
        'security/instance_security.xml',
        'security/ir.model.access.csv',
        'wizard/import_instance_views.xml',
        'views/res_company_view.xml',
        'views/config_parameter_view.xml',
        'views/res_users_view.xml',
        'views/instance_view.xml',
        
    ],
    'images': [
        'static/description/banner.png',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}