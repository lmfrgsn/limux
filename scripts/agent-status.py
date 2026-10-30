#!/usr/bin/env python3
"""Limux agent status: what each Codex and Claude Code session is doing, for the bar.

  hook <agent>   called by the agent's hooks with the event JSON on stdin
  render         rewrite the bar texts from the live sessions (drops dead ones)
  focus <agent>  focus the terminal window of that agent's most urgent session
  status         print the sessions as JSON

Sessions live only in $XDG_RUNTIME_DIR/limux/agents; nothing is written to disk.
Functional Limux content, not theme: glyphs and colours come from the bar config.
"""
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time

AGENTS = {'codex': 'Codex', 'claude': 'Claude'}
# Most urgent first; an agent shows its most urgent live session.
PRIORITY = ('error', 'input', 'working', 'idle')
WORKING = {'UserPromptSubmit', 'PreToolUse', 'PostToolUse', 'PostToolUseFailure', 'PostToolBatch',
           'SubagentStart', 'PreCompact', 'PostCompact'}
IDLE = {'SessionStart', 'Stop', 'Interrupt'}
# Claude Code notification types that mean the agent is waiting for the user.
INPUT_NOTIFICATIONS = {'permission_prompt', 'agent_needs_input', 'elicitation_dialog', 'elicitation_url_dialog'}
# Bar module texts: one module per colour, so an absent state takes no space.
SLOTS = ('icon', 'icon-input', 'icon-error', 'name', 'name-input')
# Tabler Icons 3.49.0 code points, matching themes/rhapsody.toml [bar_status].
GLYPHS = {'working': '', 'input': '', 'idle': '', 'error': ''}
SIGNAL = 8


def runtime():
    base = os.environ.get('XDG_RUNTIME_DIR')
    if not base:
        raise RuntimeError('XDG_RUNTIME_DIR is not set; run inside the desktop session')
    return Path(base)/'limux/agents'


def state_for(event):
    """Map one hook event to a state, 'end' for session end, or None to ignore."""
    name = event.get('hook_event_name')
    if name == 'SessionEnd':
        return 'end'
    if name == 'StopFailure':
        return 'error'
    if name == 'PermissionRequest':
        return 'input'
    if name == 'Notification':
        kind = event.get('notification_type') or event.get('matcher')
        return 'input' if kind in INPUT_NOTIFICATIONS else None
    if name in WORKING:
        return 'working'
    if name in IDLE:
        return 'idle'
    return None


def agent_pid(agent, start=None):
    """The agent's own process: the nearest ancestor whose name is the agent's."""
    pid = start or os.getppid()
    while pid > 1:
        try:
            comm = Path(f'/proc/{pid}/comm').read_text().strip()
            stat = Path(f'/proc/{pid}/stat').read_text()
        except OSError:
            return None
        if comm == agent:
            return pid
        pid = int(stat.rsplit(')', 1)[1].split()[1])
    return None


def alive(pid):
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def write_atomic(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix='.', dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as stream:
            stream.write(text)
        os.replace(name, path)
    finally:
        Path(name).unlink(missing_ok=True)


def session_file(directory, agent, session):
    safe = ''.join(ch for ch in str(session) if ch.isalnum() or ch in '-_')[:80]
    if not safe:
        raise ValueError('hook event has no usable session_id')
    return directory/'sessions'/f'{agent}-{safe}.json'


def record(agent, event, directory=None, pid=None):
    """Apply one hook event; return True when the visible state may have changed."""
    if agent not in AGENTS:
        raise ValueError(f'unknown agent: {agent}')
    directory = directory or runtime()
    state = state_for(event)
    if state is None:
        return False
    path = session_file(directory, agent, event.get('session_id', ''))
    if state == 'end':
        path.unlink(missing_ok=True)
        return True
    if path.exists():
        previous = json.loads(path.read_text())
        if previous.get('state') == state:
            return False
        pid = pid or previous.get('pid')
    pid = pid or agent_pid(agent)
    write_atomic(path, json.dumps({'agent': agent, 'session': event.get('session_id'), 'state': state,
                                   'pid': pid, 'cwd': event.get('cwd'), 'updated': time.time()}))
    return True


def sessions(directory=None):
    """Live sessions; files of exited agents are removed."""
    directory = directory or runtime()
    found = []
    for path in sorted((directory/'sessions').glob('*.json')):
        try:
            data = json.loads(path.read_text())
        except (OSError, ValueError):
            continue
        if data.get('pid') and not alive(data['pid']):
            path.unlink(missing_ok=True)
            continue
        found.append(data)
    return found


def summary(found):
    """{agent: (state, count)} for agents with at least one live session."""
    out = {}
    for agent in AGENTS:
        mine = [s for s in found if s['agent'] == agent and s.get('state') in PRIORITY]
        if mine:
            out[agent] = (min((s['state'] for s in mine), key=PRIORITY.index), len(mine))
    return out


def texts(found):
    """Text for every bar module slot, keyed '<agent>-<slot>'; '' hides the module."""
    out = {f'{agent}-{slot}': '' for agent in AGENTS for slot in SLOTS}
    for agent, (state, count) in summary(found).items():
        name = AGENTS[agent] + (f' {count}' if count > 1 else '')
        icon_slot = {'input': 'icon-input', 'error': 'icon-error'}.get(state, 'icon')
        out[f'{agent}-{icon_slot}'] = GLYPHS[state]
        out[f'{agent}-{"name-input" if state == "input" else "name"}'] = name
    return out


def render(directory=None):
    directory = directory or runtime()
    for key, text in texts(sessions(directory)).items():
        path = directory/'bar'/key
        if not path.exists() or path.read_text() != text:
            write_atomic(path, text)


def listens(pid, number):
    """True when this bar's config declares the refresh signal. An unhandled
    real-time signal would terminate a bar, so others are never signalled."""
    try:
        args = Path(f'/proc/{pid}/cmdline').read_bytes().split(b'\0')
        config = Path(args[args.index(b'-c') + 1].decode())
        return f'"signal": {number}' in config.read_text()
    except (OSError, ValueError, IndexError):
        return False


def refresh_bar(number=SIGNAL):
    """Ask this user's Mangobars that run the agent modules to refresh them now."""
    result = subprocess.run(['pgrep', '-u', str(os.getuid()), '-x', 'mangobar'], capture_output=True, text=True)
    for pid in result.stdout.split():
        if listens(int(pid), number):
            try:
                os.kill(int(pid), signal.SIGRTMIN + number)
            except ProcessLookupError:
                pass


def ancestors(pid):
    chain = []
    while pid and pid > 1:
        chain.append(pid)
        try:
            pid = int(Path(f'/proc/{pid}/stat').read_text().rsplit(')', 1)[1].split()[1])
        except OSError:
            break
    return chain


def focus(agent, directory=None):
    """Focus the MangoWM window that owns the agent's most urgent session."""
    mine = [s for s in sessions(directory) if s['agent'] == agent and s.get('pid')]
    if not mine:
        return False
    target = min(mine, key=lambda s: (PRIORITY.index(s['state']), -s.get('updated', 0)))
    clients = json.loads(subprocess.run(['mmsg', 'get', 'all-clients'], capture_output=True,
                                        text=True, check=True).stdout)['clients']
    by_pid = {c['pid']: c for c in clients}
    for pid in ancestors(target['pid']):
        if pid in by_pid:
            subprocess.run(['mmsg', 'dispatch', f'focusid client,{by_pid[pid]["id"]}'], check=True,
                           capture_output=True)
            return True
    return False


def main():
    action = sys.argv[1] if len(sys.argv) > 1 else 'status'
    if action == 'hook':
        agent = sys.argv[2] if len(sys.argv) > 2 else ''
        try:
            event = json.loads(sys.stdin.read() or '{}')
            if record(agent, event):
                render()
                refresh_bar()
        except Exception as exc:  # A status hook must never disturb the agent.
            print(f'Limux agent status: {exc}', file=sys.stderr)
        return
    if action == 'render':
        render()
        refresh_bar()
    elif action == 'focus':
        focus(sys.argv[2] if len(sys.argv) > 2 else '')
    elif action == 'status':
        print(json.dumps(sessions(), indent=2))
    else:
        raise SystemExit('Usage: agent-status.py hook <agent> | render | focus <agent> | status')


if __name__ == '__main__':
    main()
