# CutSwitch release project

This public repository contains CutSwitch distribution assets and a dispatcher.
Private application source and release implementation live in
`CutSwitch/cutswitch-app`. Keep those responsibilities separate.

- Start with `./cutswitch-release doctor` on the configured release Mac. The
  dispatcher locates the private checkout using the owner's local
  `~/Library/Application Support/CutSwitchRelease/config.json`; that file must
  never be committed here.
- Fix application bugs in the private app repository, following its AGENTS.md
  and repository-memory workflow. Do not copy private source, sessions,
  credentials, private logs, signing identities or customer material here.
- Keep the configured release-control checkout clean. Use a separate private
  development worktree for source edits and repository-memory records. Never
  create private `docs/memory/` records in this public repository.
- Synchronize explicitly, inspect incoming changes and pin an exact source
  commit. When another computer pushes more work, synchronize again and create
  a new release plan. Existing prepared or built candidates keep their original
  source identity.
- Preparation, builds, doctor checks and publication plans do not authorize a
  live release. Keep the current download, stable feed and website pointer
  unchanged unless the owner explicitly authorizes promotion of the verified
  candidate. Never overwrite a versioned asset with different bytes.
- Apple distribution signing, notarization and Sparkle signing remain
  human-attended steps on the release Mac. Handle protected dialogs privately.
  Preserve the existing Sparkle identity; do not generate replacement keys.
  Use the candidate's prepare-emitted frozen owner command when continuing an
  existing candidate after control-tool updates. Poll only a saved known notary
  ID; ambiguous upload or interrupted local-mutation intents require inspection.
- Route Codex-owned Xcode builds/tests through the app repository's
  `scripts/cutswitch/xcode_local_automation.sh`. A compile, synthetic test or
  signature check does not prove native installation or automatic updating.
- Record current candidate-specific affected-workflow and install/update/
  restart proof before promotion. Use a QA channel first; verify served asset
  bytes before promoting the stable feed. Website downloads use a separate
  configured installer URL and need their own verified handoff.
- Keep build caches and release artifacts on the configured release-host
  storage, outside this public checkout. Reuse unchanged checksum-pinned
  runtimes and the approved Effects package.
- Follow `docs/automation/RELEASE_MAC_WORKFLOW.md` in the private app checkout
  for the current command contract. Old one-use signing handoffs and old
  README version examples are historical context, not a new release authority.
