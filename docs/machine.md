# Limux machine files

`machine/` keeps a tracked copy of the hand-maintained files this MacBookPro15,1 depends on, at their real paths: `machine/home/` mirrors `$HOME`, `machine/system/` mirrors `/`. The live files stay canonical; the repository copy is how they are reviewed, backed up and restored. `machine/packages.txt` is the explicit package list (`pacman -Qqe`).

`scripts/machine.py` owns the list:

```sh
python3 scripts/machine.py status    # read-only: files, packages, enabled units
python3 scripts/machine.py capture   # copy changed live files into machine/, then review `git diff`
python3 scripts/machine.py restore   # fresh install: copy missing files back
```

After editing a tracked live file, run `capture`, review the diff and commit. `restore` never replaces a file that differs from the repository or a symlink; it reports it for review. It does not run `sudo`: it prints one `sudo install` line per missing system file.

## What is tracked

| Area | Files |
| --- | --- |
| Desktop | MangoWM `config.conf` (shortcuts, gestures, display, startup), Foot `foot.ini`, Mako `config`, Rofi `config.rasi`, `mimeapps.list` |
| Bar | `limux-bar`, the old `install-limux-mangobar` with its patch, `wifi-status.py` |
| Helpers | `mango-notifications`, `mango-screenshot`, `limux-night-light`, `t2-hardware-control` |
| T2 audio | WirePlumber DSP rule, both PipeWire speaker graphs, `t2-speaker-mute.service`, the setup, enable, verify and test scripts and `~/.local/share/t2-hardware-setup/` |
| System | `/etc/default/grub` (T2 kernel parameters), `/etc/pacman.conf` (`arch-mact2` repository), `linux-t2` mkinitcpio preset, tiny-dfr and t2fanrd configs, backlight udev rule, Touch Bar recovery script and service |

Not tracked, by design:

- **Generated Rhapsody outputs** (GTK stylesheet and icons, Foot `rhapsody.ini`, Mako `rhapsody`, Rofi theme, Thunar shortcuts, Mangobar config and CSS, launcher entries). Their activation scripts recreate them from tokens; see [architecture](architecture.md).
- **Private data**: `~/.config/limux/commands.toml` (snippets; recreate from `examples/commands.toml`) and `~/.config/limux/location` (one line, `<latitude> <longitude>` rounded to a city, read by `limux-night-light`).
- **Machine-specific or rebuilt**: `/etc/fstab`, user/group files, mirror lists, the Mangobar binaries (rebuilt from the pinned 0.2.2 source and `patches/mangobar/`), LV2 plugins in `~/.lv2` and the DSP filter data in `/usr/share/t2linux-audio/15_1` (rebuilt from pinned upstream commits by `setup-t2-hardware`).
- **Backups and logs** under `~/.local/state`.

Several files name the user `liam` in absolute paths, so a restore assumes the same user name.

## Restoring onto a fresh install

1. Install Arch with the T2 kernel per the t2linux guide, then restore `/etc/pacman.conf` and install `machine/packages.txt` (`grep -vx apple-bcm-firmware machine/packages.txt | sudo pacman -S --needed -`). `apple-bcm-firmware` is a foreign package (Wi-Fi firmware), installed separately per the t2linux guide.
2. `python3 scripts/machine.py restore`, then run the printed `sudo install` lines. Regenerate GRUB (`sudo grub-mkconfig -o /boot/grub/grub.cfg`) and the initramfs (`sudo mkinitcpio -P`), and reload udev rules.
3. Enable the system units `NetworkManager`, `bluetooth`, `t2fanrd`, `tiny-dfr`, `systemd-resolved` and `limux-touchbar-recover`; turn on the firewall with `sudo python3 scripts/firewall.py activate` (it writes `/etc/nftables.conf` and enables `nftables`); and the user units `pipewire`, `pipewire-pulse`, `wireplumber` (and their sockets) and `t2-speaker-mute`.
4. Rebuild the speaker DSP: `setup-t2-hardware`, which keeps the speakers locked, then `enable-t2-speakers` after the listening test. Rebuild the bar: `install-limux-mangobar` clones the pinned Mangobar 0.2.2 source and builds the patched base, and `scripts/quiet-mangobar-build.py` builds the Quiet Strip from the same source. The bar activation scripts pin this machine's binaries by hash, and builds are not byte-reproducible, so a new machine needs those pins reviewed and updated; this is not automated yet.
5. Activate the Rhapsody outputs in the order the [README](../README.md) lists them.
6. `python3 scripts/machine.py status` should report that the machine matches.
