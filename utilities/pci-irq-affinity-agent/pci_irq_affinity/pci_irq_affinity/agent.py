#
# Copyright (c) 2019 StarlingX.
#
# SPDX-License-Identifier: Apache-2.0
#

# vim: tabstop=4 shiftwidth=4 softtabstop=4

# All Rights Reserved.
#

""" Pci interrupt affinity agent daemon entry"""

import six
import json
import sys
import signal
import re
import eventlet

from nfv_common import timers
from nfv_common import selobj
from nfv_common.helpers import Object
from nfv_common.helpers import Constants
from nfv_common.helpers import Constant
from nfv_common.helpers import Singleton
from nfv_common.helpers import coroutine

from config import CONF
from config import sysconfig
from nova_provider import novaClient
from affinity import pciIrqAffinity
from Log import LOG
import rpc_listener
import instance

stay_on = True

NOVA_SERVER_STATE_CHANGE = Constant('nova-server-state-change')
NOVA_SERVER_DELETE = Constant('nova-server-delete')
NOVA_SERVER_CREATE = Constant('nova-server-create')
NOVA_SERVER_RESIZE = Constant('nova-server-resize')

PROCESS_TICK_INTERVAL_IN_MS = 500
PROCESS_TICK_MAX_DELAY_IN_MS = 2000
PROCESS_TICK_DELAY_DEBOUNCE_IN_MS = 2000
INITIAL_PCI_IRQ_AUDIT_DELAY = 5

class EventType:
    CREATE = 'compute.instance.create.end'
    DELETE = 'compute.instance.delete.end'
    RESIZE = 'compute.instance.resize.confirm.end'

def process_signal_handler(signum, frame):
    """
    Process Signal Handler
    """
    global stay_on

    if signum in [signal.SIGTERM, signal.SIGINT, signal.SIGTSTP]:
        stay_on = False
    else:
        LOG.info("Ignoring signal" % signum)

def get_inst(instance_uuid, callback):
    # get instance info from nova
    inst = novaClient.get_instance(instance_uuid)
    if inst is not None:
        LOG.debug("inst:%s" % inst)
        callback(inst)

def query_instance_callback(inst):
    LOG.debug("query inst:%s" % inst)
    pciIrqAffinity.affine_pci_dev_instance(inst)

def rpc_message_filter(message, msg_type):
    """
    Filter OpenStack Nova RPC messages for specific event type
    """
    payload = None

    event_type = message.get('event_type', "")
    if event_type == msg_type:
        payload = message.get('payload', {})
    else:
        oslo_version = message.get('oslo.version', "")
        if oslo_version in ["2.0"]:
            oslo_message = json.loads(message.get('oslo.message', None))
            if oslo_message is not None:
                event_type = oslo_message.get('event_type', "")
                if event_type == msg_type:
                    payload = oslo_message.get('payload', {})
        else:
            LOG.error("oslo version is not 2.0!")
    LOG.debug("Msg filter:msg_type=%s" % event_type)
    if payload is not None:
        LOG.debug(payload)
        server_uuid = payload.get('instance_id', None)

        LOG.debug("%s: server_uuid=%s." % (event_type, server_uuid))

        if server_uuid is not None:
            inst = dict()
            inst['server_uuid'] = server_uuid
            return inst

    return None

def rpc_message_server_create_filter(message):
    return rpc_message_filter(message, EventType.CREATE)

def rpc_message_server_delete_filter(message):
    return rpc_message_filter(message, EventType.DELETE)

def rpc_message_server_resize_filter(message):
    return rpc_message_filter(message, EventType.RESIZE)

def instance_delete_handler(message):
    """
    Instance delete handler
    """
    instance_uuid = message.get('server_uuid', None)
    LOG.debug("enter del handler")
    if instance_uuid is not None:
        LOG.info("instance_deleted: uuid=%s." % instance_uuid)
        pciIrqAffinity.reset_irq_affinity(instance_uuid)

def instance_create_handler(message):
    """
    Instance create handler
    """
    instance_uuid = message.get('server_uuid', None)
    LOG.debug("enter create handler")
    if instance_uuid is not None:
        LOG.info("instance_created: uuid=%s." % instance_uuid)
        eventlet.spawn(get_inst, instance_uuid, query_instance_callback).wait()
        #get_inst(instance_uuid, query_instance_callback)

def instance_resize_handler(message):
    """
    Instance resize handler
    """
    instance_uuid = message.get('server_uuid', None)
    LOG.debug("enter resize handler")
    if instance_uuid is not None:
        LOG.info("instance_resized: uuid=%s." % instance_uuid)
        eventlet.spawn(get_inst, instance_uuid, query_instance_callback).wait()

def get_rabbit_config():
    """
    Get rabbit config info from specific system config file.
    """

    rabbit_cfg = {}
    rabbit_session = 'DEFAULT'
    options = ['rabbit_host', 'rabbit_port', 'rabbit_userid', 'rabbit_password',
               'rabbit_virtual_host']
    try:
        for option in options:
            rabbit_cfg[option] = sysconfig.get(rabbit_session, option)
        LOG.info(rabbit_cfg)
    except Exception as e:
        LOG.error("Could not read all required rabbitmq configuration! Err=%s" % e)
        rabbit_cfg = {}

    return rabbit_cfg

def start_rabbitmq_client():
    """
    Start Rabbitmq client to listen instance notifications from Nova
    """
    cfg = get_rabbit_config()
    if not cfg:
        LOG.error("Failed to start rabbitmq client!")
        return

    _rpc_listener = rpc_listener.RPCListener(cfg['rabbit_host'], cfg['rabbit_port'],
                                             cfg['rabbit_userid'], cfg['rabbit_password'],
                                             cfg['rabbit_virtual_host'], "nova",
                                             "notifications.info",
                                             'pci_irq_affinity_queue')

    _rpc_listener.add_message_handler(
            NOVA_SERVER_CREATE,
            rpc_message_server_create_filter,
            instance_create_handler)

    _rpc_listener.add_message_handler(
            NOVA_SERVER_DELETE,
            rpc_message_server_delete_filter,
            instance_delete_handler)

    _rpc_listener.add_message_handler(
            NOVA_SERVER_RESIZE,
            rpc_message_server_resize_filter,
            instance_resize_handler)

    _rpc_listener.start()

    return _rpc_listener

@timers.interval_timer('audit_affinity', initial_delay_secs=INITIAL_PCI_IRQ_AUDIT_DELAY,
                       interval_secs=CONF.pci_affine_interval)
def _audit_affinity():
    while True:
        timer_id = (yield)
        LOG.info("Audit timer_id=%s." % timer_id)
        pciIrqAffinity.audit_pci_irq_affinity()

def audits_initialize():
    """
    Init periodic audit task for pci interrupt affinity check
    """
    timers.timers_register_interval_timers([_audit_affinity])

def audits_finalize():
    pass

def process_initialize():
    """
    Initialize selobj, timer and periodic audit
    """
    selobj.selobj_initialize()
    timers.timers_initialize(PROCESS_TICK_INTERVAL_IN_MS,
                             PROCESS_TICK_MAX_DELAY_IN_MS,
                             PROCESS_TICK_DELAY_DEBOUNCE_IN_MS)
    audits_initialize()

def process_finalize():
    """
    Finalize
    """
    timers.timers_finalize()
    selobj.selobj_finalize()
    audits_finalize()

def process_main():
    LOG.info("Enter PCI Affinity Agent")

    try:
        signal.signal(signal.SIGTSTP, process_signal_handler)

        process_initialize()
        rpc_listener = start_rabbitmq_client()

        while stay_on:
            selobj.selobj_dispatch(PROCESS_TICK_INTERVAL_IN_MS)
            timers.timers_schedule()
    except KeyboardInterrupt:
        LOG.info("keyboard Interrupt received.")
        pass

    except Exception as e:
        LOG.info("%s" % e)
        sys.exit(200)

    finally:
        LOG.error("proces_main finalized!!!")
        if rpc_listener is not None:
            rpc_listener.stop()
        process_finalize()

if __name__ == '__main__':
    process_main()

