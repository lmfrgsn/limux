#!/usr/bin/env bash
# Build as the logged-in user. Install only the two missing LV2 bundles locally.
set -euo pipefail
state="${XDG_STATE_HOME:-$HOME/.local/state}/t2-hardware-setup"
build="$state/sources"
mkdir -p "$build" "$HOME/.lv2"
clone_once() {
    local name="$1" url="$2" ref="$3"
    if [[ ! -d "$build/$name/.git" ]]; then
        git clone --depth 1 --branch "$ref" "$url" "$build/$name"
    fi
    git -C "$build/$name" diff --exit-code
    if [[ -n "${4:-}" ]]; then
        [[ "$(git -C "$build/$name" rev-parse HEAD)" == "$4" ]] || {
            echo "Source revision changed for $name; review required." >&2
            return 1
        }
    fi
    git -C "$build/$name" rev-parse HEAD >> "$state/source-commits.log"
}
if ! lv2ls | grep -Fx 'https://chadmed.au/bankstown' >/dev/null; then
    clone_once bankstown https://github.com/chadmed/bankstown.git 1.1.0
    [[ "$(git -C "$build/bankstown" rev-parse HEAD)" == e9829c9bccf5ed73768135c0ddd506f5a6690f9e ]]
    (cd "$build/bankstown"; cargo build --release --locked)
    dest="$HOME/.lv2/bankstown.lv2"
    if [[ -e "$dest" ]]; then cp -a "$dest" "$state/current-backup/"; fi
    mkdir -p "$dest"
    install -m755 "$build/bankstown/target/release/libbankstown.so" "$dest/bankstown.so"
    install -m644 "$build/bankstown/"{manifest,bankstown}.ttl "$dest/"
fi
if ! lv2ls | grep -Fx 'http://plugin.org.uk/swh-plugins/fastLookaheadLimiter' >/dev/null; then
    clone_once swh-lv2 https://github.com/swh/lv2.git master e5f8356c773fe5995f183fe28758b93912aa8901
    # Build only the needed limiter; never run a downloaded installer as root.
    (cd "$build/swh-lv2"; make plugins/fast_lookahead_limiter-swh.lv2/plugin.so)
    src="$build/swh-lv2/plugins/fast_lookahead_limiter-swh.lv2"
    dest="$HOME/.lv2/fast_lookahead_limiter-swh.lv2"
    if [[ -e "$dest" ]]; then cp -a "$dest" "$state/current-backup/"; fi
    mkdir -p "$dest"
    install -m755 "$src/plugin-Linux.so" "$dest/"
    install -m644 "$src/"*.ttl "$dest/"
fi
clone_once t2-apple-audio-dsp https://github.com/lemmyg/t2-apple-audio-dsp.git master 1895a70350e9444a78c63be20830b4813c5eb0f6
for uri in https://chadmed.au/bankstown \
    http://lsp-plug.in/plugins/lv2/compressor_stereo \
    http://lsp-plug.in/plugins/lv2/loud_comp_mono \
    http://plugin.org.uk/swh-plugins/fastLookaheadLimiter; do
    lv2info "$uri" >/dev/null
done
