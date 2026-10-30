# T2 hardware integration: MacBookPro15,1

Run `~/.local/bin/setup-t2-hardware` as liam in Foot, without prefixing sudo.
It requires normal desktop/session access, sudo, and internet access.
It does not reboot, play sounds, unmute speakers, raise audio volume, or
change the bootloader, kernel, T2 drivers, Wi-Fi, keyboard layout, trackpad,
display scaling, or Waybar. It adds XF86 controls to MangoWM.

Observed before setup:
- DMI: MacBookPro15,1; Intel i7-8850H; AppleT2x4 audio.
- Kernel: 7.2.11-arch1-Watanare-T2-1-t2; required IOMMU/pm_async parameters present.
- PipeWire and WirePlumber installed; host runtime state inaccessible to Codex.
- Missing: pipewire-alsa, pipewire-pulse, rtkit, brightnessctl, tiny-dfr, alsa-utils.
- apple-t2-audio-config provides x4 UCM routing; no speaker DSP found.
- Keyboard LED apple::kbd_backlight reads 0/512.
- Screen backlight gmux_backlight; Touch Bar backlight appletb_backlight.
- hid_appletb_kbd/hid_appletb_bl and t2bce audio/USB modules loaded.
- Existing Touch Bar input device advertises media keys; no Mango XF86 bindings.

Setup and safety:
- Backups in ~/.local/state/t2-hardware-setup/backup-*; initial backup-path file
  identifies the backup before Codex edits. Runtime backups include system paths.
- Speakers are quarantined before audio service changes. Dependency/build/setup
  failure retains or restores the quarantine.
- Uses installed ALSA routing without overwriting it or renaming sound cards.
- Fetches model 15_1 data from lemmyg/t2-apple-audio-dsp. Does not execute its
  installer. Checks the graph's model, plugin set, limiter, channel order, and FIRs.
- Installs repository LSP LV2 plugins. Builds Bankstown 1.1.0 (pinned commit) and
  only SWH's LV2 fast-lookahead limiter as the desktop user into ~/.lv2.
- SWH and DSP snapshots are pinned to the inspected commits, recorded in source-commits.log and retained
  under sources. They are not automatically updated on subsequent runs.
- The graph has per-model FIRs, compression and limiting, but upstream describes
  it as experimental. This is not independently verified thermal/excursion
  protection. Speakers must remain silent pending runtime review and permission.
- The raw output remains volume-locked. All four model-specific convolver outputs
  have an explicit zero-gain gate. The DSP input uses normal mute/volume handling
  and is set to 0% and muted. t2-speaker-mute.service reapplies these settings at
  audio/session startup. The speakers-locked marker blocks volume-up/unmute keys.
  Removing that marker alone does not remove the zero-gain gates.
- No speaker-unlock command is provided. Ask for a review of verification.log
  before authorizing any audible test. Keep locks in place across reboot.
- PipeWire services/sockets and WirePlumber use systemd user startup; RTKit is
  D-Bus activated. tiny-dfr uses its packaged device-activation rules/static unit
  or enablement if the installed unit supports it. No custom driver reloads. The setup retriggers only the Touch Bar display USB
  device to apply the packaged tiny-dfr mode rule, and refreshes backlight aliases.
- tiny-dfr media layer defaults on, vendor key contents retained. A cold session
  or later user-initiated reboot may be needed as noted by the T2 wiki.
- Keyboard LED set to 50%; Mango exec_once reapplies it on compositor startup.
- Screen brightness is not changed during setup. Media controls explicitly use
  gmux_backlight. Only the keyboard LED and gmux brightness file receive a narrow
  liam ownership rule if ordinary brightnessctl access needs it. No input group
  membership or blanket device permissions are granted.

Verification:
`~/.local/bin/verify-t2-hardware` is silent and read-only. Setup runs it itself.
Logs: ~/.local/state/t2-hardware-setup/{setup,verification}.log and pipewire-graph.json.
It reports package versions, active/enabled services, sinks, default sink, DSP
mute state, links, brightness devices, available media players and recent journals.
A missing service/DSP sink or unverified mute gives a failing exit status; setup
then restores speaker quarantine. No MPRIS players is reported as pending testing.
Physical key response, speaker sound quality, and post-reboot startup cannot be
confirmed from static checks. Audio gain/unmute and audible playback need permission.

Primary references:
- https://wiki.t2linux.org/guides/audio-config/
- https://wiki.t2linux.org/guides/postinstall/
- https://github.com/lemmyg/t2-apple-audio-dsp
- https://github.com/AsahiLinux/tiny-dfr
- https://github.com/chadmed/bankstown
- https://github.com/swh/lv2

After installation, `~/.local/bin/finish-t2-audio` applies and checks user-level
DSP/mute repairs without package installation or hardware/driver changes.
The DSP now matches the observed `alsa.card_name`, not a missing driver property.

Daily-use activation after the successful left/right listening test:
`~/.local/bin/enable-t2-speakers` backs up the current user configuration, enables
the original 15_1 model graph, removes temporary silence gates, and initializes
the hidden raw speaker route at nominal unity. The DSP remains the default sink
and begins at 25% muted. The existing startup mute service initializes this path
after audio startup. Headphone routing is left unchanged when active.
The speakers-enabled marker distinguishes daily-use verification from quarantine.
Old setup/repair entry points perform verification once daily audio is enabled.
Backups and activation diagnostics remain under ~/.local/state/t2-hardware-setup/.
