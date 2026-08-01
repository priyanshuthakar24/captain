# See LICENSE file for full copyright and licensing details.

import os


PID_FILE_DIRECTORY = '/var/run/'


def get_instance_pid_path(instance_name):
    """Return the pid file path for an instance."""
    return os.path.join(PID_FILE_DIRECTORY, f'{instance_name}.pid')


def ensure_config_file(config_path, instance_name, server_config):
    """Create a server config file if it does not exist yet."""
    config_file = os.path.join(config_path, f'{instance_name}.conf')
    if not os.path.isfile(config_file):
        with open(config_file, 'w', encoding='utf-8') as file:
            file.write(server_config or '')
    return config_file


def write_server_config(config_path, instance_name, server_config):
    """Update an existing server config file if it exists."""
    config_file = os.path.join(config_path, f'{instance_name}.conf')
    if os.path.isfile(config_file):
        with open(config_file, 'w', encoding='utf-8') as file:
            file.write(server_config or '')
    return config_file


def ensure_log_file(log_path, instance_name):
    """Ensure a log file exists for an instance."""
    log_file = os.path.join(log_path, f'{instance_name}.log')
    if not os.path.isfile(log_file):
        open(log_file, 'a', encoding='utf-8').close()
    return log_file


def read_log_tail(log_file, size=15000):
    """Return the last chunk of a log file."""
    with open(log_file, 'r', encoding='utf-8', errors='ignore') as file_handle:
        file_handle.seek(0, 2)
        file_size = file_handle.tell()
        file_handle.seek(max(file_size - size, 0), 0)
        return ''.join(file_handle.readlines())
