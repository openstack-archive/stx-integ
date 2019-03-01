#
# Copyright (c) 2019 StarlingX.
#
# SPDX-License-Identifier: Apache-2.0
#

# vim: tabstop=4 shiftwidth=4 softtabstop=4

# All Rights Reserved.
#

""" Define NovaProvider class"""

import keyring
from novaclient import client
from keystoneauth1 import loading
from keystoneauth1 import session
from Log import LOG
from config import sysconfig
import instance

class NovaProvider:

    def __init__(self):
        self._creds = self._get_keystone_creds()
        self._auth = self._get_auth(self._creds)
        self._hostname = self.get_hostname()

    def get_hostname(self):
        try:
            with open("/etc/hostname") as f:
                return f.readline().strip()
        except IOError:
            LOG.error('failed to get host name')

    def _get_keystone_creds(self):
        creds = {}
        keyStoneSession = 'openstack_keystone_authtoken'
        options = ['username', 'user_domain_name', 'auth_url', 'project_name',
                   'project_domain_name', 'keyring_service']

        try:
            for option in options:
                creds[option] = sysconfig.get(keyStoneSession, option)

            creds['password'] = keyring.get_password(creds.pop('keyring_service'),
                                                     creds['username'])
        except Exception as e:
            LOG.error("Could not get keystone creds configuration! Err=%s" % e)
            creds = None

        return creds

    def _get_auth(self, creds):

        if creds is not None:
            loader = loading.get_plugin_loader('password')
            auth = loader.load_from_options(**creds)
            return auth
        return None

    def get_nova(self):
        try:
            sess = session.Session(auth=self._auth)
            nova = client.Client('2.1', session=sess)
            return nova
        except Exception as e:
            LOG.warning("Failed to connect to nova!")
            raise Exception("could not connect nova!")

    def get_instance(self, uuid):
        try:
            nova = self.get_nova()
            server = nova.servers.get(uuid)
            flavor_info = nova.flavors.get(server.flavor["id"])
            extra_spec = flavor_info.get_keys()
            hostname = getattr(server, 'OS-EXT-SRV-ATTR:host')
        except Exception as e:
            LOG.warning("Could not get instance=%s from Nova! error=%s" % (uuid, e))
            return None

        LOG.info('GET VM:%s in node:%s' % (server.name, hostname))

        if hostname == self._hostname:
            inst = instance.instance(uuid, server.name, extra_spec)
            inst.create(server)
            return inst
        else:
            LOG.info('The VM is not in current host!')
            return None

    def get_instances(self, filters):
        instances = set()
        try:
            nova = self.get_nova()
            LOG.info(self._hostname)
            filters['host'] = self._hostname
            servers = nova.servers.list(detailed=False, search_opts=filters)
        except Exception as e:
            LOG.warning("Failed to get instances from Nova! error=%s" % e)
            return instances

        LOG.info("get active servers in current node!")
        for server in servers:
            LOG.debug(server.id)
            inst = self.get_instance(server.id)
            if inst is not None:
                instances.update([inst])

        return instances
