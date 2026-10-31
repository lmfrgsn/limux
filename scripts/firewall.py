#!/usr/bin/env python3
"""Limux firewall: nftables blocks every incoming connection this laptop did not
start. Outgoing traffic and replies to it are unaffected.

  check     validate the ruleset in a private network namespace (no root needed)
  activate  (sudo) install /etc/nftables.conf and enable nftables now and at boot
  verify    the installed ruleset matches and nftables is enabled and running
  rollback  (sudo) stop and disable nftables and restore Arch's default file

Differences from Arch's default ruleset: SSH is not let in (no SSH server runs),
and DHCPv6 replies from the local link are, so IPv6 addresses still arrive.
"""
import argparse
import hashlib
import os
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
LIVE = Path('/etc/nftables.conf')
DEFAULT = ROOT/'themes/recovery/nftables-arch-default.conf'
DEFAULT_SHA256 = 'fa2f984794025339cf2d26d329f9b0bf83a39b9fa310d06b4cc40a0c1b0c8f46'
RULESET = '''#!/usr/bin/nft -f
# Limux firewall (~/limux/scripts/firewall.py). Blocks every incoming connection
# this laptop did not start; outgoing traffic and its replies are unaffected.

destroy table inet filter
table inet filter {
  chain input {
    type filter hook input priority filter
    policy drop

    ct state invalid drop comment "early drop of invalid connections"
    ct state {established, related} accept comment "allow replies to this laptop's connections"
    iif lo accept comment "allow from loopback"
    meta l4proto { icmp, icmpv6 } accept comment "allow icmp"
    ip6 saddr fe80::/10 udp dport dhcpv6-client accept comment "allow DHCPv6 replies"
    pkttype host limit rate 5/second counter reject with icmpx type admin-prohibited
    counter
  }
  chain forward {
    type filter hook forward priority filter
    policy drop
  }
}
'''


def digest(data):
    return hashlib.sha256(data).hexdigest()


def run(*args, **kw):
    return subprocess.run(args, check=True, capture_output=True, text=True, timeout=20, **kw)


def default_bytes():
    data = DEFAULT.read_bytes()
    if digest(data) != DEFAULT_SHA256:
        raise RuntimeError('the recovery copy of the Arch default ruleset failed its integrity check')
    return data


def validate(text):
    with tempfile.NamedTemporaryFile('w', suffix='.nft') as stream:
        stream.write(text)
        stream.flush()
        if os.geteuid() == 0:
            run('nft', '-c', '-f', stream.name)
        else:
            run('unshare', '-rn', 'nft', '-c', '-f', stream.name)


def file_state():
    data = LIVE.read_bytes()
    if data == RULESET.encode():
        return 'active'
    if data == default_bytes():
        return 'original'
    raise RuntimeError(f'{LIVE} has edits Limux did not make; inspect it')


def service(state):
    return subprocess.run(['systemctl', state, 'nftables'], capture_output=True, text=True).stdout.strip()


def loaded():
    """Arch's nftables unit loads the file and exits (no RemainAfterExit), so it reads
    inactive while the rules are in force. Loaded means it ran this boot and succeeded."""
    show = dict(line.split('=', 1) for line in subprocess.run(
        ['systemctl', 'show', 'nftables', '-p', 'Result', '-p', 'ExecMainStatus', '-p', 'ExecMainStartTimestampMonotonic'],
        capture_output=True, text=True).stdout.splitlines() if '=' in line)
    return (show.get('Result') == 'success' and show.get('ExecMainStatus') == '0'
            and int(show.get('ExecMainStartTimestampMonotonic') or 0) > 0)


def unload():
    """The unit has no stop step, so disabling it leaves the rules in force; remove the table."""
    subprocess.run(['nft', 'destroy', 'table', 'inet', 'filter'], capture_output=True)


def require_root():
    if os.geteuid() != 0:
        raise RuntimeError('this needs root: run it with sudo')


def write(data):
    fd, name = tempfile.mkstemp(prefix='.limux-', dir=LIVE.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            os.fchmod(stream.fileno(), 0o644)
            stream.write(data)
        os.replace(name, LIVE)
    finally:
        Path(name).unlink(missing_ok=True)


def activate():
    require_root()
    before = file_state()
    validate(RULESET)
    try:
        if before != 'active':
            write(RULESET.encode())
        run('systemctl', 'enable', '--now', 'nftables')
        run('systemctl', 'restart', 'nftables')  # load this file even if nftables was already running
        if 'table inet filter' not in run('nft', 'list', 'ruleset').stdout:
            raise RuntimeError('the ruleset did not load')
    except BaseException:
        subprocess.run(['systemctl', 'disable', '--now', 'nftables'], capture_output=True)
        unload()
        if before == 'original':
            write(default_bytes())
        raise
    print('Firewall on: incoming connections are blocked, now and after every restart.')


def rollback():
    require_root()
    file_state()
    run('systemctl', 'disable', '--now', 'nftables')
    unload()
    write(default_bytes())
    print("Firewall off and Arch's default /etc/nftables.conf restored.")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('action', choices=['check', 'activate', 'verify', 'rollback'])
    action = parser.parse_args().action
    if action == 'check':
        validate(RULESET)
        print(f'Ruleset valid. {LIVE}: {file_state()}; nftables {service("is-enabled")}, '
              f'{"loaded" if loaded() else "not loaded"} this boot.')
    elif action == 'verify':
        state, enabled, running = file_state(), service('is-enabled'), loaded()
        print(f'Firewall: ruleset {state}, nftables {enabled}, {"loaded" if running else "not loaded"} this boot.')
        if (state, enabled, running) != ('active', 'enabled', True):
            raise SystemExit(1)
    else:
        activate() if action == 'activate' else rollback()


if __name__ == '__main__':
    try:
        main()
    except (OSError, RuntimeError, subprocess.SubprocessError) as exc:
        raise SystemExit(f'Firewall: {exc}')
