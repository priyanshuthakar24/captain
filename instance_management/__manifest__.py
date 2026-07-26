# See LICENSE file for full copyright and licensing details.

{
    'name': 'Odoo Instance Management',
    'version': '19.0.1.0.0',
    'author': 'Priyanshu Thakar',
    'category': 'Others',
    'license': 'LGPL-3',
    'description': """
Odoo Instance Management.
====================================

    * Ability to start/stop/restart an instance.
    * Ability to check the status of the instance either it is running or stopped.
    * Ability to download the log file of an instance.
    * Ability to check the current running instance and its process id.

    Note:- You have to configure system parameter for odoo versions daemon,.conf directory and .log directory.
    """,
    'depends': ['mail'],
    'data': [
        'data/instance_data.xml',
        'security/instance_security.xml',
        'security/ir.model.access.csv',
        #'wizard/download_log_view.xml',
        #'wizard/running_port_view.xml',
        #'wizard/run_multiple_ins.xml',
        'views/res_company_view.xml',
        'views/config_parameter_view.xml',
        'views/res_users_view.xml',
        'views/instance_view.xml',
        #'views/module_info_views.xml',
        #'wizard/check_idle_instance.xml'
    ],
    'installable': True,
    'auto_install': False,
}
