#!/usr/bin/python
#
# Copyright (c) 2016 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#


### BEGIN INIT INFO
# Provides:          ceph/mgr RESTful API plugin
# Required-Start:    $ceph
# Required-Stop:     $ceph
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: Ceph MGR RESTful API plugin
# Description:       Ceph MGR RESTful API plugin
### END INIT INFO

import argparse
import errno
import fcntl
import inspect
import json
import logging
import os
import shutil
import socket
import subprocess
import sys

import daemon
import requests


class Config(object):
    """
    Configuration options controlling ceph-mgr restful plugin
    service wrapper. In the future we may want to load them
    from a configuration file (like /etc/ceph/mgr-restful-plugin.conf )
    """
    def __init__(self):
        self.service_name = 'mgr-restful-plugin'
        self.pgrep_pattern = os.path.join(
            '/etc/init.d/', self.service_name)
        self.log_level = logging.INFO
        self.log_dir = '/var/log'
        self.ceph_mgr_daemon = '/usr/bin/ceph-mgr'
        self.ceph_mgr_cluster = 'ceph'
        self.ceph_mgr_rundir = '/var/run/ceph/mgr'
        self.service_socket = os.path.join(
            self.ceph_mgr_rundir,
            '{}.socket'.format(self.service_name))
        self.service_lock = os.path.join(
            self.ceph_mgr_rundir,
            '{}.lock'.format(self.service_name))
        self.service_pidfile = os.path.join(
            '/var/run/ceph',
            '{}.pid'.format(self.service_name))
        self.ceph_name = socket.gethostname()
        self.service_port = 5001
        self.timeout_seconds = 15
        self.cluster_retry_sec = 15

    @staticmethod
    def load():
        return Config()

CONFIG = Config.load()
LOG = None

def setup_logging(name=None, cleanup_handlers=False):
    global LOG
    if not name:
        name = CONFIG.service_name
    LOG = logging.getLogger(name)
    LOG.setLevel(CONFIG.log_level)
    if cleanup_handlers:
        try:
            for handler in LOG.handlers:
                if isinstance(handler, logging.StreamHandler):
                    handler.flush()
                if isinstance(handler, logging.FileHandler):
                    handler.close()
            LOG.handlers = []
        except Exception:
            pass
    elif LOG.handlers:
        return
    handler = logging.FileHandler(
        os.path.join(CONFIG.log_dir,
                     '{}.log'.format(CONFIG.service_name)))
    handler.setFormatter(
        logging.Formatter('%(asctime)s %(process)s %(levelname)s %(name)s %(message)s'))
    LOG.addHandler(handler)


class ServiceException(Exception):
    message = "generic ceph mgr service exception"

    def __init__(self, *args, **kwargs):
        if "message" not in kwargs:
            try:
                message = self.message.format(*args, **kwargs)
            except Exception:   # noqa
                message = '{}, args:{}, kwargs: {}'.format(
                    self.message, args, kwargs)
        else:
            message = kwargs["message"]
        super(ServiceException, self).__init__(message)


class ServiceMonitorAlreadyStarted(ServiceException):
    message = ('Service monitor already started')


class ServiceMonitorLockFailed(ServiceException):
    message = ('Unable to lock service monitor: '
               'reason={reason}')


class ServiceMonitorNoSocket(ServiceException):
    message = ('Unable to create monitor socket: '
               'reason={reason}')


class ServiceMonitorBindFailed(ServiceException):
    message = ('Failed to bind monitor socket: '
               'path={path}, reason={reason}')


class ServiceMonitor(object):
    def __init__(self):
        LOG.info('setup service monitor')
        self.plugin_started = False
        self.service_url = None

        LOG.info('take service lock')
        try:
            os.makedirs(os.path.dirname(CONFIG.service_lock))
        except OSError:
            pass
        self.lock_file = open(CONFIG.service_lock, 'w')
        try:
            fcntl.flock(self.lock_file.fileno(),
                        fcntl.LOCK_EX | fcntl.LOCK_NB)
        except (IOError, OSError) as e:
            if e.errno == errno.EAGAIN:
                raise ServiceMonitorAlreadyStarted()
            else:
                raise ServiceMonitorLockFailed(reason=str(e))

        LOG.info('create service socket')
        try:
            self.socket = socket.socket(
                socket.AF_UNIX, socket.SOCK_STREAM)
        except socket.error as e:
            raise ServiceMonitorNoSocket(reason=e)

        LOG.info('remove existing service socket files (if any)')
        try:
            os.unlink(CONFIG.service_socket)
        except OSError:
            pass

        LOG.info('bind service socket: path=%s',
                 CONFIG.service_socket)
        try:
            self.socket.bind(CONFIG.service_socket)
        except socket.error as e:
            raise ServiceMonitorBindFailed(
                path=CONFIG.service_socket, reason=e)

        LOG.info('set service socket timeout')
        self.socket.settimeout(1)

        LOG.info('clear service state machine')
        self.state = None
        self.skip_ticks = None

    def run(self):
        LOG.info('create service pid file')
        with open(CONFIG.service_pidfile, 'w') as pid_file:
            pid_file.write(str(os.getpid()))
        LOG.info('start service monitor loop')
        try:
            self.socket.listen(1)
            self.reset_monitor()
            while True:
                self.step_monitor()
                try:
                    client, _ = self.socket.accept()
                    try:
                        request = client.recv(1024)
                        LOG.debug('received client request=%s', request)
                    except socket.timeout:
                        LOG.warning('timeout waiting for client request')
                        client.close()
                        continue
                    if request == 'status':
                        status = self.status()
                        if (not status.startswith('OK')
                                and not self.state):
                            LOG.info('starting automatic recovery. '
                                     'status=%s', status)
                            self.reset_monitor()
                        try:
                            client.sendall(status)
                        except socket.error as e:
                            LOG.warning('failed to report status. '
                                        'status=%s, reason=%s', status, e)
                    if request == 'stop':
                        self.stop()
                        try:
                            client.sendall('OK')
                        except socket.error as e:
                            LOG.warning('failed to report status. '
                                        'status=%s, reason=%s', status, e)
                        LOG.info('exit service monitor loop')
                        return
                except socket.timeout:
                    pass
        finally:
            self.socket.close()
            self.socket = None

    def reset_monitor(self):
        self.state = self.state_wait_cluster_available
        self.skip_ticks = 0

    def step_monitor(self):
        # LOG.info('monitor service tick. '
        #          'state={}, skip_ticks={}'.format(
        #              self.state, self.skip_ticks))
        if not self.state:
            return
        if self.skip_ticks:
            self.skip_ticks -= 1
            return
        self.state, self.skip_ticks = self.state()

    def state_wait_cluster_available(self):
        LOG.info('wait until cluster is available')
        try:
            _ = subprocess.check_output(
                ['/usr/bin/ceph', 'fsid',
                 '--connect-timeout', str(CONFIG.timeout_seconds)],
                stderr=subprocess.STDOUT,
                shell=False)
        except subprocess.CalledProcessError as err:
            LOG.info('monitor: ceph fsid failed (cluster unavailable). '
                     'reason=%s, out=%s', err, err.output)
            return (self.state_wait_cluster_available,
                    CONFIG.cluster_retry_sec)
        return (self.state_stop_running_ceph_mgr, 0)

    def state_stop_running_ceph_mgr(self):
        LOG.info('stop running ceph-mgr (if any)')
        _ = subprocess.call(['/usr/bin/pkill', '-f',
                             CONFIG.ceph_mgr_daemon])
        return (self.state_get_ceph_mgr_auth, 0)

    def state_cleanup_ceph_mgr_auth(self):
        LOG.info('cleanup ceph auth for ceph-mgr')
        try:
            _ = subprocess.check_output(
                ['/usr/bin/ceph', 'auth', 'del',
                 'mgr.{}'.format(CONFIG.ceph_name),
                 '--connect-timeout', str(CONFIG.timeout_seconds)],
                stderr=subprocess.STDOUT,
                shell=False)
        except subprocess.CalledProcessError as err:
            LOG.info('monitor: ceph auth del failed. '
                     'reason=%s, out=%s', err, err.output)
            return (self.state_wait_cluster_available,
                    CONFIG.cluster_retry_sec)
        shutil.rmtree(CONFIG.ceph_mgr_rundir, ignore_errors=True)
        return (self.state_create_ceph_mgr_auth, 0)

    def state_get_ceph_mgr_auth(self):
        path = '{}/ceph-{}'.format(CONFIG.ceph_mgr_rundir,
                                   CONFIG.ceph_name)
        LOG.info('create directory structure: path=%s', path)
        try:
            os.makedirs(path)
        except OSError as e:
            LOG.info('monitor: failed to create directory structure. '
                     'path=%s, reason=%s', path, e)
            # continue running (path may already exist)
        LOG.info('check ceph-mgr auth')
        try:
            _ = subprocess.check_output(
                ['/usr/bin/ceph', 'auth', 'get',
                 'mgr.{}'.format(CONFIG.ceph_name),
                 '-o', '{}/ceph-{}/keyring'.format(
                     CONFIG.ceph_mgr_rundir,
                     CONFIG.ceph_name),
                 '--connect-timeout', str(CONFIG.timeout_seconds)],
                stderr=subprocess.STDOUT,
                shell=False)
        except subprocess.CalledProcessError as err:
            LOG.info('missing ceph-mgr auth. '
                     'reason=%s, out=%s', err, err.output)
            return (self.state_create_ceph_mgr_auth,
                    CONFIG.cluster_retry_sec)
        return (self.state_start_ceph_mgr_daemon, 0)

    def state_create_ceph_mgr_auth(self):
        LOG.info('create ceph-mgr auth')
        try:
            _ = subprocess.check_output(
                ['/usr/bin/ceph', 'auth', 'get-or-create',
                 'mgr.{}'.format(CONFIG.ceph_name),
                 'mon', 'allow *', 'osd', 'allow *',
                 '--connect-timeout', str(CONFIG.timeout_seconds)],
                stderr=subprocess.STDOUT,
                shell=False)
        except subprocess.CalledProcessError as err:
            LOG.info('monitor: failed to create ceph-mgr auth. '
                     'reason=%s, out=%s', err, err.output)
            return (self.state_wait_cluster_available,
                    CONFIG.cluster_retry_sec)
        return (self.state_get_ceph_mgr_auth, 0)

    def state_start_ceph_mgr_daemon(self):
        LOG.info('start ceph-mgr daemon')
        try:
            _ = subprocess.check_output(
                [CONFIG.ceph_mgr_daemon,
                 '--cluster', CONFIG.ceph_mgr_cluster,
                 '--id', CONFIG.ceph_name],
                close_fds=True,
                stderr=subprocess.STDOUT,
                shell=False)
        except subprocess.CalledProcessError as err:
            LOG.warning('monitor: failed to start ceph-mgr. '
                        'reason=%s, out=%s', err, err.output)
            return (self.state_wait_cluster_available,
                    CONFIG.cluster_retry_sec)
        return (self.state_check_restful_plugin_service, 10)

    def state_check_restful_plugin_service(self):
        LOG.info('check restful plugin')
        try:
            out = subprocess.check_output(
                ['/usr/bin/ceph', 'mgr', 'services',
                 '--format', 'json',
                 '--connect-timeout', str(CONFIG.timeout_seconds)],
                stderr=subprocess.STDOUT,
                shell=False)
        except subprocess.CalledProcessError as err:
            LOG.warning('unable to get ceph-mgr services. '
                        'reason=%s, out=%s', err, err.output)
            return (self.state_cleanup_ceph_mgr_auth,
                    CONFIG.cluster_retry_sec)
        try:
            services = json.loads(out)
        except ValueError:
            LOG.error('unable to parse services info. '
                      'data=%s', out)
            return (None, 0)
        try:
            self.service_url = services['restful']
        except (KeyError, TypeError):
            LOG.info('restful plugin not found')
            self.service_url = None
            return (self.state_enable_restful_plugin, 0)
        return (self.state_ping_restful_plugin, 0)

    def state_enable_restful_plugin(self):
        LOG.info('enable restful plugin')
        try:
            _ = subprocess.check_output(
                ['/usr/bin/ceph', 'mgr',
                 'module', 'enable', 'restful',
                 '--connect-timeout', str(CONFIG.timeout_seconds)],
                stderr=subprocess.STDOUT,
                shell=False)
        except subprocess.CalledProcessError as err:
            LOG.warning('failed to enable restful plugin. '
                        'reason=%s, out=%s', err, err.output)
            return (self.state_cleanup_ceph_mgr_auth,
                    CONFIG.cluster_retry_sec)
        try:
            _ = subprocess.check_output(
                ['/usr/bin/ceph', 'config', 'set', 'mgr',
                 'mgr/restful/server_port', str(CONFIG.service_port),
                 '--connect-timeout', str(CONFIG.timeout_seconds)],
                stderr=subprocess.STDOUT,
                shell=False)
        except subprocess.CalledProcessError as err:
            LOG.error('failed to configure restful plugin '
                      'port. reason=%s, output=%s', err, err.output)
            return (self.state_wait_cluster_available,
                    CONFIG.cluster_retry_sec)
        try:
            _ = subprocess.check_output(
                ['/usr/bin/ceph', 'restful',
                 'create-key', 'admin',
                 '--connect-timeout', str(CONFIG.timeout_seconds)],
                stderr=subprocess.STDOUT,
                shell=False)
        except subprocess.CalledProcessError as err:
            LOG.error('failed to create restful admin key. '
                      'reason=%s, output=%s', err, err.output)
            subprocess.call(
                ['/usr/bin/ceph', 'mgr',
                 'module', 'disable', 'restful',
                 '--connect-timeout', str(CONFIG.timeout_seconds)],
                shell=False)
            return (self.state_wait_cluster_available,
                    CONFIG.cluster_retry_sec)
        try:
            _ = subprocess.check_output(
                ['/usr/bin/ceph', 'restful',
                 'create-self-signed-cert',
                 '--connect-timeout', str(CONFIG.timeout_seconds)],
                stderr=subprocess.STDOUT,
                shell=False)
        except subprocess.CalledProcessError as err:
            LOG.error('failed to create restful self-signed-cert. '
                      'reason=%s, output=%s', err, err.output)
            subprocess.call(
                ['/usr/bin/ceph', 'mgr',
                 'module', 'disable', 'restful',
                 '--connect-timeout', str(CONFIG.timeout_seconds)],
                shell=False)
            return (self.state_wait_cluster_available,
                    CONFIG.cluster_retry_sec)
        return (self.state_ping_restful_plugin, 0)

    def state_ping_restful_plugin(self):
        if not self.service_url:
            try:
                out = subprocess.check_output(
                    ['/usr/bin/ceph', 'mgr', 'services',
                     '--format', 'json',
                     '--connect-timeout', str(CONFIG.timeout_seconds)],
                    shell=False)
            except subprocess.CalledProcessError as err:
                LOG.warning('unable to get ceph-mgr services. '
                            'reason=%s', err)
                return (self.state_cleanup_ceph_mgr_auth,
                        CONFIG.cluster_retry_sec)
            try:
                services = json.loads(out)
            except ValueError as e:
                LOG.error('unable to parse services info. '
                          'data=%s', out)
                return (None, 0)
            try:
                self.service_url = services['restful']
            except (KeyError, TypeError) as e:
                LOG.info('restful plugin not found. '
                         'services=%s', services)
                self.service_url = None
                return (self.state_enable_restful_plugin, 5)
        requests.packages.urllib3.disable_warnings()
        LOG.info('restful plugin url=%s', self.service_url)
        try:
            response = requests.request(
                'GET', self.service_url,
                verify=False,
                timeout=CONFIG.timeout_seconds)
            LOG.info('get url=%s, response=%s',
                     self.service_url, response)
            if not response.ok:
                LOG.info('restful plugin is not ok. '
                         'response=%s', response)
                return (self.state_restart_restful_plugin, 5)
        except (requests.ConnectionError,
                requests.Timeout,
                requests.HTTPError) as e:
            LOG.error('restful request error. '
                      'reason=%s', e)
            return (self.state_restart_restful_plugin, 5)
        self.plugin_started = True
        return (None, 0)

    def state_restart_restful_plugin(self):
        try:
            _ = subprocess.check_output(
                ['/usr/bin/ceph', 'restful', 'restart',
                 '--connect-timeout', str(CONFIG.timeout_seconds)],
                shell=False)
        except subprocess.CalledProcessError as err:
            LOG.warning('unable to get ceph-mgr services. '
                        'reason=%s', err)
            return (self.state_wait_cluster_available,
                    CONFIG.cluster_retry_sec)
        return (self.state_ping_restful_plugin, 5)

    def status(self):
        if not self.plugin_started:
            if self.state:
                return 'OK.monitor.{}'.format(
                    self.state.__name__)
            return 'ERR.no_monitor'
        try:
            out = subprocess.check_output(
                ['/usr/bin/ceph', 'mgr', 'services',
                 '--format', 'json',
                 '--connect-timeout', str(CONFIG.timeout_seconds)],
                shell=False)
        except subprocess.CalledProcessError as err:
            LOG.warning('unable to get ceph-mgr services. '
                        'reason=%s', err)
            return 'ERR.service_unavailable'
        try:
            services = json.loads(out)
        except ValueError as e:
            LOG.error('unable to parse services info. '
                      'data=%s', out)
            return 'ERR.format_error'
        try:
            self.service_url = services['restful']
        except (KeyError, TypeError) as e:
            LOG.info('restful plugin not found. '
                     'services=%s', services)
            return 'ERR.missing_plugin'
        requests.packages.urllib3.disable_warnings()
        try:
            response = requests.request(
                'GET', self.service_url,
                verify=False,
                timeout=CONFIG.timeout_seconds)
            if not response.ok:
                LOG.info('restful plugin is not ok. '
                         'response=%s', response)
                return 'ERR.response_error'
        except (requests.ConnectionError,
                requests.Timeout,
                requests.HTTPError) as e:
            LOG.error('restful request error. '
                      'reason=%s', e)
            return 'ERR.request_error'
        return 'OK'

    def stop(self):
        LOG.info('stop service monitor')
        self.state = None
        self.skip_ticks = 0

        LOG.info('stop running ceph-mgr (if any)')
        _ = subprocess.call(['/usr/bin/pkill', '-f',
                             CONFIG.ceph_mgr_daemon])

    @staticmethod
    def _make_client_socket():
        sock = socket.socket(
            socket.AF_UNIX, socket.SOCK_STREAM)
        sock.settimeout(CONFIG.timeout_seconds)
        sock.connect(CONFIG.service_socket)
        return sock


    @staticmethod
    def request_status():
        try:
            sock = ServiceMonitor._make_client_socket()
            sock.sendall('status')
            status = sock.recv(1024)
            LOG.debug('status %s', status)
            return status.startswith('OK')
        except socket.error as e:
            LOG.error('status error: reason=%s', e)
            return False

    @staticmethod
    def request_stop():
        try:
            sock = ServiceMonitor._make_client_socket()
            sock.sendall('stop')
            _ = sock.recv(1024)
        except socket.error as e:
            LOG.error('stop error: reason=%s', e)
            return False
        return True


class InitWrapper(object):
    def __init__(self):
        parser = argparse.ArgumentParser()
        actions = [m[0]
                   for m in inspect.getmembers(self)
                   if (inspect.ismethod(m[1])
                       and m[0] not in ['__init__', 'run'])]
        parser.add_argument(
            'action',
            choices=actions)
        self.args = parser.parse_args()

    def run(self):
        getattr(self, self.args.action)()

    def start(self):
        pipe = os.pipe()
        child = os.fork()
        if child == 0:
            os.close(pipe[0])
            with daemon.DaemonContext(files_preserve=[pipe[1]]):
                setup_logging(cleanup_handlers=True)
                try:
                    monitor = ServiceMonitor()
                    status = 'OK'
                except ServiceMonitorAlreadyStarted:
                    os.write(pipe[1], 'OK')
                    os.close(pipe[1])
                    return
                except Exception as e:
                    status = str(e)
                os.write(pipe[1], status)
                os.close(pipe[1])
                if status == 'OK':
                    try:
                        monitor.run()
                    except Exception as e:
                        LOG.exception('service monitor error: '
                                      'reason=%s', e)
        else:
            os.close(pipe[1])
            try:
                status = os.read(pipe[0], 1024)
                if status == 'OK':
                    sys.exit(0)
                else:
                    LOG.warning('Service monitor failed to start: '
                                'status=%s', status)
            except IOError as e:
                LOG.warning('Failed to read monitor status: '
                            'reason=%s', e)
            os.close(pipe[0])
            os.waitpid(child, 0)
            sys.exit(1)

    def stop(self):
        result = ServiceMonitor.request_stop()
        if not result:
            _ = subprocess.call(
                ['/usr/bin/pkill', '-f',
                 CONFIG.pgrep_pattern],
                shell=False)
            _ = subprocess.call(
                ['/usr/bin/pkill', '-f',
                 CONFIG.ceph_mgr_daemon],
                shell=False)

    def restart(self):
        self.stop()
        self.start()

    def force_reload(self):
        self.stop()
        self.start()

    def reload(self):
        self.stop()
        self.start()

    def status(self):
        status = ServiceMonitor.request_status()
        sys.exit(0 if status is True else 1)


def main():
    setup_logging(name='init-wrapper')
    InitWrapper().run()

if __name__ == '__main__':
    main()
