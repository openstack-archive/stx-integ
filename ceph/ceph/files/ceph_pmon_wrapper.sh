#!/bin/bash
#
# Copyright (c) 2015-2016 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#
# This script is a helper wrapper for pmon monitoring of ceph
# processes. The "/etc/init.d/ceph" script does not know if ceph is
# running on the node. For example when the node is locked, ceph
# processes are not running. In that case we do not want pmond to
# monitor these processes.
#
# The script "/etc/services.d/<node>/ceph.sh" will create the file
# "/var/run/.ceph_started" when ceph is running and remove it when
# is not.
#
# The script also extracts  one or more ceph process names  that are
# reported as 'not running' or 'dead' or 'failed'  by '/etc/intit.d/ceph status'
# and writes the names to a text file: /tmp/ceph_status_failure.txt for
# pmond to access. The pmond adds the text to logs and alarms. Example of text
# samples written to file by this script are:
#   'osd.1'
#   'osd.1, osd.2'
#   'mon.storage-0'
#   'mon.storage-0, osd.2'
#
# Moreover, for processes that are reported as 'hung' by '/etc/intit.d/ceph status'
# the script will try increase their logging to 'debug' for a configurable interval.
# With logging increased it will outputs a few stack traces then, at the end of this
# interval, it dumps its stack core and kills it.
#
# Return values;
# zero -   /etc/init.d/ceph returned success or ceph is not running on the node
# non-zero /etc/init.d/ceph returned a failure or invalid syntax
#

source /usr/bin/tsconfig

CEPH_SCRIPT="/etc/init.d/ceph"
CEPH_FILE="$VOLATILE_PATH/.ceph_started"
CEPH_RESTARTING_FILE="$VOLATILE_PATH/.ceph_restarting"
CEPH_GET_STATUS_FILE="$VOLATILE_PATH/.ceph_getting_status"
CEPH_STATUS_FAILURE_TEXT_FILE="/tmp/ceph_status_failure.txt"

BINDIR=/usr/bin
SBINDIR=/usr/sbin
LIBDIR=/usr/lib64/ceph
ETCDIR=/etc/ceph
COREDIR=/var/lib/systemd/coredump
source $LIBDIR/ceph_common.sh

LOG_PATH=/var/log/ceph
LOG_FILE=$LOG_PATH/ceph-process-states.log
LOG_LEVEL=NORMAL  # DEBUG
verbose=0

DATA_PATH=$VOLATILE_PATH/ceph_hang    # folder where we keep state information
mkdir -p $DATA_PATH                   # make sure folder exists

MONITORING_INTERVAL=15
TRACE_LOOP_INTERVAL=5
GET_STATUS_TIMEOUT=120

WAIT_FOR_CMD=1

RC=0

wait_for_status ()
{
    timeout=$GET_STATUS_TIMEOUT  # wait for status no more than $timeout seconds
    while [ -f ${CEPH_GET_STATUS_FILE} ] && [ $timeout -gt 0 ]
    do
       sleep 1
       let timeout-=1
    done
    if [ $timeout -eq 0 ]
    then
        wlog "-" "WARN" "Getting status takes more than ${GET_STATUS_TIMEOUT}s, continuing"
        rm -f $CEPH_GET_STATUS_FILE
    fi
}

start ()
{
    if [ -f ${CEPH_FILE} ]
    then
        wait_for_status
        ${CEPH_SCRIPT} start
        RC=$?
    else
        # Ceph is not running on this node, return success
        exit 0
    fi
}

restart ()
{
    if [ -f ${CEPH_FILE} ]
    then
        wait_for_status
        touch $CEPH_RESTARTING_FILE
        ${CEPH_SCRIPT} restart
        rm -f $CEPH_RESTARTING_FILE
    else
        # Ceph is not running on this node, return success
        exit 0
    fi

}

log_and_kill_hung_procs ()
{
    # Log info about the hung processes and then kill them; later on pmon will restart them
    local names=$1
    for name in $names;
    do
        type=`echo $name | cut -c 1-3`   # e.g. 'mon', if $item is 'mon1'
        id=`echo $name | cut -c 4- | sed 's/^\\.//'`
        get_conf run_dir "/var/run/ceph" "run dir"
        get_conf pid_file "$run_dir/$type.$id.pid" "pid file"
        pid=$(cat $pid_file)
        wlog $name "INFO" "Dealing with hung process (pid:$pid)"

        # monitoring interval
        wlog $name "INFO" "Increasing log level"
        execute_ceph_cmd ret $name "ceph daemon $name config set debug_$type 20/20"
        monitoring=$MONITORING_INTERVAL
        while [ $monitoring -gt 0 ]
        do
            if [ $(($monitoring % $TRACE_LOOP_INTERVAL)) -eq 0 ]; then
                date=$(date "+%Y-%m-%d_%H-%M-%S")
                log_file="$LOG_PATH/hang_trace_${name}_${pid}_${date}.log"
                wlog $name "INFO" "Dumping stack trace to: $log_file"
                $(pstack $pid >$log_file) &
            fi
            let monitoring-=1
            sleep 1
        done

        core_file="$COREDIR/core.ceph-${type}.${UID}.$(cat /etc/machine-id).${pid}.$(date +%s%N)"
        wlog $name "INFO" "Dumping core to: $core_file"
        gcore -o $core_file $pid &>/dev/null
        mv ${core_file}.$pid ${core_file}
        wlog $name "INFO" "Archiving core file (in background)"
        $(xz -z $core_file -T 8) &
        wlog $name "INFO" "Killing process, it will be restarted by pmon..."
        kill -KILL $pid &>/dev/null
        rm -f $pid_file # process is dead, core dump is archiving, preparing for restart
    done
}

status ()
{
    if [ -f ${CEPH_RESTARTING_FILE} ]
    then
        # Ceph is restarting, we don't report state changes on the first pass
       rm -f ${CEPH_RESTARTING_FILE}
       exit 0
    fi
    if [ -f ${CEPH_FILE} ]
    then
        # Make sure the script does not 'exit' between here and the 'rm -f' below
        # or the checkpoint file will be left behind
        touch -f ${CEPH_GET_STATUS_FILE}
        result=`${CEPH_SCRIPT} status`
        RC=$?
        if [ "$RC" -ne 0 ]; then
            erred_procs=`echo "$result" | sort | uniq | awk ' /not running|dead|failed/ {printf "%s ", $1}' | sed 's/://g' | sed 's/, $//g'`
            hung_procs=`echo "$result" | sort | uniq | awk ' /hung/ {printf "%s ", $1}' | sed 's/://g' | sed 's/, $//g'`
            invalid=0
            host=`hostname`
            for i in $(echo $erred_procs $hung_procs)
            do
               if [[ "$i" =~ osd.?[0-9]?[0-9]|mon.$host ]]; then
                  continue
               else
                  invalid=1
               fi
            done

            log_and_kill_hung_procs $hung_procs

            hung_procs_text=""
            for i in $(echo $hung_procs)
            do
                hung_procs_text+="$i(process hung) "
            done

            rm -f $CEPH_STATUS_FAILURE_TEXT_FILE
            if [ $invalid -eq 0 ]; then
                text=""
                for i in $erred_procs
                do
                    text+="$i, "
                done
                for i in $hung_procs
                do
                    text+="$i (process hang), "
                done
                echo "$text" | tr -d '\n' > $CEPH_STATUS_FAILURE_TEXT_FILE
            else
               echo "$host: '${CEPH_SCRIPT} status' result contains invalid process names: $erred_procs"
               echo "undetermined_osd" > $CEPH_STATUS_FAILURE_TEXT_FILE
            fi
        fi
        rm -f ${CEPH_GET_STATUS_FILE}
    else
        # Ceph is not running on this node, return success
        exit 0
    fi
}


case "$1" in
    start)
        start
        ;;
    restart)
        restart
        ;;
    status)
        status
        ;;
    *)
        echo "Usage: $0 {start|restart|status}"
        exit 1
        ;;
esac

exit $RC
