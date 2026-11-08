#!/usr/bin/env python3
"""Inspect or restart only one user's selected Poki remote helper."""
import argparse
import os
from pathlib import Path
import re
import signal
import subprocess


def matching_pids(output, executable, config, uid):
    result = []
    # ps prints paths containing spaces without quoting. Match the complete prefix
    # and require the remaining argument to be the private Unix socket path.
    prefix = f"{executable} --remote-server {config} "
    for line in output.splitlines():
        fields = line.strip().split(None, 2)
        if len(fields) != 3:
            continue
        pid, owner, command = fields
        if not pid.isdigit() or owner != str(uid) or not command.startswith(prefix):
            continue
        socket = command[len(prefix):]
        if re.fullmatch(rf"/tmp/poki-remote-{uid}/[0-9a-f]{{24}}\.sock", socket):
            result.append(int(pid))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('device')
    parser.add_argument('--restart', action='store_true')
    parser.add_argument('--poki-root', type=Path, default=Path.home() / 'coding/poki')
    parser.add_argument('--state-dir', type=Path, default=Path(os.environ.get(
        'POKI_MCP_STATE_DIR', str(Path.home() / 'Library/Application Support/PokiMCP'))))
    args = parser.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9-]+', args.device):
        parser.error('Invalid device identifier')
    executable = args.poki_root.resolve() / 'build/poki-native'
    config = args.state_dir.resolve() / 'remote' / args.device / 'config.json'
    if not executable.is_file() or not config.is_file():
        parser.error('Native helper or selected remote configuration is missing')
    output = subprocess.check_output(['ps', '-axo', 'pid=,uid=,command='], text=True)
    pids = matching_pids(output, executable, config, os.getuid())
    if not args.restart:
        print(f'{len(pids)} matching remote helper(s); no changes made.')
        return
    for pid in pids:
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
    print(f'Stopped {len(pids)} matching helper(s). The next Poki call recreates the connection.')


if __name__ == '__main__':
    main()
