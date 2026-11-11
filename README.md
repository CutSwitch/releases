# CutSwitch releases

Official CutSwitch macOS installers, release notes and automatic update feeds.
Published files are available in [GitHub Releases](https://github.com/CutSwitch/releases/releases).

This is the distribution project. Application fixes and the release pipeline
live in the private `CutSwitch/cutswitch-app` repository. The `cutswitch-release`
launcher below delegates to that pipeline on the owner's configured release Mac;
it does not contain signing credentials or publish anything by itself.

## Use the release Mac

On the configured release Mac, open this Codex project and run:

```sh
./cutswitch-release doctor
```

The launcher reads the owner-only local configuration at
`~/Library/Application Support/CutSwitchRelease/config.json`. Its `app_repo`
entry points to the private application checkout. Configure that host once using
`docs/automation/RELEASE_MAC_WORKFLOW.md` in the private checkout. Do not add the
configuration, signing files or build artifacts to this repository.

The workflow's current command help is available with:

```sh
./cutswitch-release --help
```

Preparation and publication planning leave the current live installer and feed
unchanged. A new release still requires its affected-workflow and install/update
checks, the attended Apple/Sparkle steps and a separate owner promotion decision.
Keep the existing updater identity, increment the internal build and retain
previous immutable release assets.

For signing or resuming a pending notarization, use the exact frozen owner
command emitted by preparation. It remains bound to that candidate even if the
private control checkout later updates. Unknown uploads or interrupted local
mutations require inspection; a generic rerun is not a recovery instruction.

## Work from another computer

Connect to this same release Mac using Codex remote access. Run the project and
commands on the release host so its existing tools and Keychain identities stay
there. The host must be awake, online and reachable. Pair each other computer
privately through the app's Connections settings; availability and exact labels
can vary. SSH projects are another supported connection method after the owner
has configured and approved SSH access. See the
[official remote-connection instructions](https://learn.chatgpt.com/docs/remote-connections).

When additional fixes are pushed from another computer, explicitly synchronize
the private checkout and prepare a new source-pinned candidate. An existing
candidate is never silently rebuilt from a newer `main`. Publishing a Sparkle
feed alone does not update the website's separately configured installer link.

Local dispatcher checks require only Python and Git, and make no network,
signing or publication requests:

```sh
python3 -B -m unittest test_dispatcher.py
```
