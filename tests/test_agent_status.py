import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('agent_status', ROOT/'scripts/agent-status.py')
a = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)


def event(name, session='s1', **extra):
    return {'hook_event_name': name, 'session_id': session, 'cwd': '/tmp', **extra}


class AgentStatusTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.pid = os.getpid()  # a live process stands in for the agent

    def tearDown(self):
        self.tmp.cleanup()

    def apply(self, agent, *events):
        for e in events:
            a.record(agent, e, self.dir, pid=self.pid)
        a.render(self.dir)
        return {k: (self.dir/'bar'/k).read_text() for k in a.texts([])}

    def test_events_map_to_states(self):
        self.assertEqual(a.state_for(event('UserPromptSubmit')), 'working')
        self.assertEqual(a.state_for(event('PreToolUse')), 'working')
        self.assertEqual(a.state_for(event('PermissionRequest')), 'input')
        self.assertEqual(a.state_for(event('Notification', notification_type='permission_prompt')), 'input')
        self.assertIsNone(a.state_for(event('Notification', notification_type='auth_success')))
        self.assertEqual(a.state_for(event('Stop')), 'idle')
        self.assertEqual(a.state_for(event('Interrupt')), 'idle')
        self.assertEqual(a.state_for(event('StopFailure')), 'error')
        self.assertEqual(a.state_for(event('SessionEnd')), 'end')
        self.assertIsNone(a.state_for(event('FileChanged')))

    def test_needs_input_uses_the_alert_modules_and_hides_the_rest(self):
        bar = self.apply('claude', event('UserPromptSubmit'), event('PermissionRequest'))
        self.assertEqual(bar['claude-icon-input'], a.GLYPHS['input'])
        self.assertEqual(bar['claude-name-input'], 'Claude')
        self.assertEqual(bar['claude-icon'], '')
        self.assertEqual(bar['claude-name'], '')
        self.assertTrue(all(v == '' for k, v in bar.items() if k.startswith('codex-')))

    def test_most_urgent_session_wins_and_count_shows(self):
        bar = self.apply('codex', event('PreToolUse', 'one'), event('Stop', 'two'))
        self.assertEqual(bar['codex-icon'], a.GLYPHS['working'])
        self.assertEqual(bar['codex-name'], 'Codex 2')
        bar = self.apply('codex', event('StopFailure', 'two'))
        self.assertEqual(bar['codex-icon-error'], a.GLYPHS['error'])
        self.assertEqual(bar['codex-icon'], '')

    def test_session_end_and_dead_agents_disappear(self):
        self.apply('claude', event('Stop'))
        bar = self.apply('claude', event('SessionEnd'))
        self.assertTrue(all(v == '' for v in bar.values()))
        a.record('codex', event('Stop', 'gone'), self.dir, pid=2**22 + 12345)
        a.render(self.dir)
        self.assertEqual((self.dir/'bar'/'codex-icon').read_text(), '')
        self.assertEqual(list((self.dir/'sessions').glob('codex-*')), [])

    def test_unchanged_state_is_not_rewritten_and_bad_input_is_refused(self):
        self.assertTrue(a.record('claude', event('PreToolUse'), self.dir, pid=self.pid))
        self.assertFalse(a.record('claude', event('PostToolUse'), self.dir, pid=self.pid))
        with self.assertRaises(ValueError):
            a.record('other', event('Stop'), self.dir, pid=self.pid)
        with self.assertRaises(ValueError):
            a.record('claude', event('Stop', session=''), self.dir)

    def test_session_ids_cannot_escape_the_runtime_directory(self):
        path = a.session_file(self.dir, 'claude', '../../etc/passwd')
        self.assertEqual(path.parent, self.dir/'sessions')

    def test_hook_never_fails_the_agent(self):
        with patch.object(a, 'runtime', return_value=self.dir), patch.object(a, 'refresh_bar'), \
                patch('sys.argv', ['agent-status.py', 'hook', 'claude']), \
                patch('sys.stdin.read', return_value='not json'), patch('sys.stderr'):
            a.main()

    def test_focus_walks_from_the_agent_to_its_window(self):
        a.record('claude', event('PermissionRequest'), self.dir, pid=self.pid)
        clients = {'clients': [{'id': 7, 'pid': os.getppid(), 'tags': [2]}]}
        calls = []

        def run(cmd, **kw):
            calls.append(cmd)
            return type('R', (), {'stdout': json.dumps(clients)})()
        with patch.object(a.subprocess, 'run', side_effect=run):
            self.assertTrue(a.focus('claude', self.dir))
        self.assertEqual(calls[-1], ['mmsg', 'dispatch', 'focusid client,7'])


    def test_only_bars_declaring_the_signal_are_signalled(self):
        config = self.dir/'config.jsonc'
        config.write_text('{"custom/agent-claude-icon": {"signal": 8}}')
        cmdline = b'mangobar\0-c\0' + str(config).encode() + b'\0-s\0x.css\0'
        with patch.object(a.Path, 'read_bytes', return_value=cmdline):
            self.assertTrue(a.listens(1, 8))
            self.assertFalse(a.listens(1, 9))
        live = self.dir/'live.jsonc'
        live.write_text('{"custom/wifi": {"interval": 5}}')
        with patch.object(a.Path, 'read_bytes', return_value=b'mangobar\0-c\0' + str(live).encode() + b'\0'):
            self.assertFalse(a.listens(1, 8))
        sent = []
        with patch.object(a.subprocess, 'run', return_value=type('R', (), {'stdout': '11 12'})()), \
                patch.object(a, 'listens', side_effect=lambda pid, n: pid == 12), \
                patch.object(a.os, 'kill', side_effect=lambda pid, sig: sent.append(pid)):
            a.refresh_bar()
        self.assertEqual(sent, [12])

if __name__ == '__main__':
    unittest.main()
