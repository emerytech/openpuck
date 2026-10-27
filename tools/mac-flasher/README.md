# OpenPuck Flasher

A small macOS app to flash the **Couchside OpenPuck fork** onto nRF52840
UF2-bootloader boards (nice!nano etc.) when fulfilling Etsy puck orders — no
phone, no Couchside box needed. It does exactly what the box does: copy a
verified `.uf2` onto the board's bootloader volume.

## Install

**Homebrew (recommended):**

```bash
brew install --cask emerytech/tap/openpuck-flasher
```

**Direct download:** grab `OpenPuck-Flasher.dmg` from the
[latest release](https://github.com/emerytech/homebrew-tap/releases/latest)
and drag it to Applications.

The app is Developer-ID signed and notarized, so it opens without Gatekeeper
warnings. Releases are hosted in the
[emerytech/homebrew-tap](https://github.com/emerytech/homebrew-tap) repo.

## Use

1. Launch the app.
2. Put a board in DFU: **double-tap reset** (or short **RST–GND** twice, within ~0.5s).
   A `NICENANO` drive mounts and the app shows **Board ready**.
3. Click **Flash** — or flip **Auto-flash (batch)** on and just keep plugging boards;
   each one flashes on its own, and the session counter ticks up.

The board reboots itself as a **Steam Controller Puck** and the drive disappears —
that's success. Unplug, insert the next.

## Firmware

- **Pinned 0.9.40** (default) — `OpenPuck-0.9.40-standard.uf2`, sha256-verified before
  every write. Downloaded once from the fork release and cached in
  `~/Library/Application Support/OpenPuck Flasher/`.
- **Latest fork** — the newest `*-standard.uf2` from `emerytech/openpuck` releases
  (size + UF2 magic checked).
- **Local file** — pick your own `.uf2` (handy when testing a new fork build before
  pinning it).

Every path verifies the file is a real UF2 of sane size before a single byte is written.

## Build from source

```bash
./build.sh            # build + ad-hoc sign (local dev / testing)
./build.sh --sign     # build + Developer ID sign + notarize + staple,
                      # then emit OpenPuck-Flasher.zip (for the cask) and
                      # OpenPuck-Flasher.dmg (for direct download)
```

Requires the Xcode command-line tools (`xcrun swiftc`). Targets macOS 13+.
The app icon is generated at build time by `src/makeicon.swift` — no external art.

`--sign` defaults to `TEAM_ID=XK6QP975ZQ` and the `axe` notarytool keychain
profile; override either via env vars or a `.env` beside `build.sh`. Store a
notary profile once with:

```bash
xcrun notarytool store-credentials "axe" \
  --apple-id you@example.com --team-id XK6QP975ZQ --password xxxx-xxxx-xxxx-xxxx
```

### Cutting a release

1. Bump `appVersion` in `src/main.swift`.
2. `./build.sh --sign` — note the printed `OpenPuck-Flasher.zip` sha256.
3. In [emerytech/homebrew-tap](https://github.com/emerytech/homebrew-tap): bump
   `version` + `sha256` in `Casks/openpuck-flasher.rb`, then
   `gh release create openpuck-flasher-v<version> build/OpenPuck-Flasher.{zip,dmg}`.

## Source of the firmware

OpenPuck is a separate AGPL-3.0 project (safijari, forked by EmeryTech). This app only
downloads a released build and copies it to the board; it embeds no OpenPuck source.
Fork + releases: https://github.com/emerytech/openpuck
