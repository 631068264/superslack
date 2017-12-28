import sys
import requests
from supervisor import childutils
from base import util


class MESSAGE_STATUS(object):
    INFO = 'good'
    WARN = 'warning'
    ERROR = 'danger'

    NAME_DICT = {
        INFO: 'INFO',
        WARN: 'WARN',
        ERROR: 'ERROR',
    }


class EVENT_TYPE(object):
    PROCESS = 'process'
    SUPERVISOR = 'supervisor'


class SuperSlack(object):
    def __init__(self, webhook=None):
        self.webhook = webhook
        self.stdin = sys.stdin
        self.stdout = sys.stdout
        self.stderr = sys.stderr

        self.payload = None
        self.header = None

    def err(self, msg):
        self.stderr.write(msg + '\n')
        self.stderr.flush()

    def out(self, msg):
        self.stdout.write(msg + '\n')
        self.stdout.flush()

    def ok(self):
        childutils.listener.ok(self.stdout)

    def _parse_payload(self, payload):
        if payload:
            self.payload = dict([p.split(':') for p in payload.split(' ')])

    def _exist_key(self, key, msg):
        key_msg = ' %s={%s}' % (key, key)
        if key in self.payload:
            msg += key_msg.format(**self.payload)
        return msg

    def _exist_warn(self, to_state, msg):
        if self.payload.get('expected', None) == 0:
            msg += ' exit unexpectedly'
        if to_state == 'FATAL':
            msg += ' %s' % (to_state,)
        return msg

    def _state_level(self, to_state, envet_type):
        level = MESSAGE_STATUS.INFO
        if envet_type == EVENT_TYPE.PROCESS:
            if to_state == 'FATAL':
                level = MESSAGE_STATUS.ERROR
            elif self.payload.get('expected', None) == 0:
                level = MESSAGE_STATUS.WARN
        elif envet_type == EVENT_TYPE.SUPERVISOR:
            level = MESSAGE_STATUS.WARN
        return level

    def parse_process_state(self):
        to_state = self.header['eventname'].replace('PROCESS_STATE_', '')
        msg = 'Process {groupname}:{processname} {from_state} to {to_state}'
        msg = self._exist_key('tries', msg)
        msg = self._exist_key('pid', msg)
        msg = self._exist_warn(to_state, msg)
        state_level = self._state_level(to_state, EVENT_TYPE.PROCESS)
        return state_level, msg.format(to_state=to_state, **self.payload)

    def parse_supervisor_state(self):
        to_state = self.header['eventname'].replace('SUPERVISOR_STATE_CHANGE_', '')
        state_level = self._state_level(to_state, EVENT_TYPE.SUPERVISOR)
        msg = 'SUPERVISOR {to_state}'.format(to_state=to_state)
        return state_level, msg

    def send_slack(self, state_level, msg):
        if self.webhook is None:
            return

        ip = util.get_outer_ip()

        payload = {
            "color": state_level,
            "fields": [
                {
                    'title': '{} [{}]'.format(util.now(), ip),
                    'value': '{}     {}'.format(MESSAGE_STATUS.NAME_DICT[state_level], msg),
                }
            ]
        }
        try:
            requests.post(self.webhook, json=payload)
        except Exception:
            self.err(util.error_msg())

    def run(self):
        while True:
            self.header, payload = childutils.listener.wait(self.stdin, self.stdout)
            self._parse_payload(payload)
            if self.header['eventname'].startswith('PROCESS_STATE'):
                state_level, msg = self.parse_process_state()
            elif self.header['eventname'].startswith('SUPERVISOR_STATE'):
                state_level, msg = self.parse_supervisor_state()

            if state_level and msg:
                self.send_slack(state_level, msg)

            self.ok()


if __name__ == '__main__':
    webhook = None
    slack = SuperSlack(webhook)
    slack.run()

