#!/usr/bin/env python3
"""Build a version-pinned Mangobar 0.2.2 with separate Limux patches."""
from pathlib import Path
import shutil
import subprocess
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path.home() / '.local/state/limux/bar-migration/sources/mangobar'
UPSTREAM_COMMIT = '84f25a77706c31b49b865d08bc5429ca61115971'  # 0.2.2
PATCHES = (ROOT / 'patches/mangobar/01-limux-t2-metrics.patch',
           ROOT / 'patches/mangobar/02-quiet-workspace-strip.patch')
OUT = ROOT / 'build/quiet-workspace-strip'


def prepare_source(destination, patches=PATCHES):
    if subprocess.run(['git', '-C', str(SOURCE), 'rev-parse', 'HEAD'],
                      check=True, capture_output=True, text=True).stdout.strip() != UPSTREAM_COMMIT:
        raise ValueError('retained Mangobar checkout is not pinned 0.2.2 commit')
    destination.mkdir(parents=True)
    with tempfile.TemporaryDirectory() as directory:
        archive = Path(directory) / 'mangobar.tar'
        subprocess.run(['git', '-C', str(SOURCE), 'archive', '--format=tar',
                        f'--output={archive}', UPSTREAM_COMMIT], check=True)
        with tarfile.open(archive) as tar:
            tar.extractall(destination, filter='data')
    for patch in patches:
        subprocess.run(['patch', '-p1', '--batch', '--fuzz=0', '-i', str(patch)],
                       cwd=destination, check=True, capture_output=True, text=True)
    return destination


def patched_sources():
    with tempfile.TemporaryDirectory() as directory:
        source = prepare_source(Path(directory) / 'source')
        return {name: (source / name).read_text()
                for name in ('style.h', 'style.c', 'mangobar.c', 'rtconfig.h', 'rtconfig.c')}


def build(patches=PATCHES, out=OUT):
    """Build from the pinned checkout plus `patches` in fixed paths under `out`,
    so the same inputs give the same binary for hash pinning."""
    copy, build_dir = out / 'mangobar-source', out / 'mangobar-build'
    if copy.exists():
        shutil.rmtree(copy)
    out.mkdir(parents=True, exist_ok=True)
    prepare_source(copy, patches)
    if not build_dir.exists():
        subprocess.run(['meson', 'setup', str(build_dir), str(copy)], check=True)
    subprocess.run(['ninja', '-C', str(build_dir)], check=True)
    return build_dir / 'mangobar'


if __name__ == '__main__':
    print(build())
