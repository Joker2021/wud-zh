# wud-zh maintenance

## Scope

This fork rebuilds the official WUD source at a fixed, published stable release, translates static Vue UI text plus an explicitly anchored allowlist of dynamic UI literals into Simplified Chinese, validates translation placeholders, runs the upstream checks, and publishes a multi-architecture image after automated gates pass. Dynamic anchors fail closed if their upstream source changes. The known display roles `admin`/`rw`/`ro` map to Chinese labels; unknown roles, usernames, provider types, configuration keys/values, and error details remain runtime data. Authorization continues to use the original role value. It does not modify NAS containers.

## Safety and source

- Never expose `YOUDAO_APP_SECRET` or pass it to upstream code, Docker builds, or untrusted pull-request jobs.
- Never build from `main`, `latest`, or a moving branch. `upstream.lock.json` must contain the published release tag and resolved commit SHA.
- Never overwrite an existing immutable image version. A failed update must leave the last stable image tags unchanged.
- Publish jobs must serialize GHCR tag mutations and re-read `upstream.lock.json` from `main` immediately before moving `stable/latest`; an older queued build may publish its immutable version but must not roll aliases backward.
- Image tags use `${VERSION}-zh.${REVISION}`; automated upstream builds use revision `1`. If an immutable version tag differs from a rebuilt candidate, never retag it. Reuse it only after verifying upstream version/commit labels, the project revision label, and linux/amd64 plus linux/arm64 manifests; promote aliases from the immutable version tag.
- Scheduled upstream checks reconcile publication by exact build run-name (`version` + upstream `commit` + Chinese revision): queued/running builds block duplicates, failed attempts retry up to three total, and unknown run or Release API state fails closed. During migration, an existing version Release with no exact-name run means complete; an exact-name failure still retries.
- WUD requires Docker API access to monitor a Docker host. A socket mounted `:ro` still grants powerful Docker API operations.
- Do not enable Docker or Docker Compose update triggers in the sample deployment.

## Workflow

1. Read `PROJECT_HANDOFF.md` and `docs/upstream-analysis.md`.
2. Check the actual published stable release and commit before translating.
3. Extract static Vue template text and approved text attributes with the upstream Vue compiler parser, plus only the source-anchored dynamic literals listed in `scripts/i18n.mjs`. Anchor mismatch or duplication must fail closed. Dynamic anchors cover navigation/config labels, logout/demo/copy fixed wording, count units, and boolean config labels; keep runtime values and error details intact. Do not translate identifiers, API keys, URLs, Docker references, or user data.
4. Reuse `translations/memory.json`; validate interpolation tokens before persisting any new translation.
5. Run upstream UI Jest tests against pristine English source first; current tests assert English UI literals. Then apply translations and run the production UI build plus project validation.
6. Review generated source, lock file, translation memory, coverage report, and workflow permissions when changing this automation.
7. Confirm image publication and manifest architectures after CI. Do not claim NAS runtime validation unless performed on that NAS.

The inherited upstream `ci.yml` workflow is disabled on this fork to prevent publishing an unrelated upstream image or deploying upstream documentation. Keep image builds behind the `check-upstream.yml` reconciliation, which dispatches `build-release.yml` with the exact version and upstream commit inputs and revision `1`. Manual dispatch requires the same inputs; higher revisions are reserved for explicit maintenance builds.

## References

- Upstream analysis and exact source boundaries: `docs/upstream-analysis.md`
- Translation API details: `docs/youdao-api.md`
- Build, restore, and release procedures: `docs/architecture.md`
