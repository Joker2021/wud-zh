# wud-zh maintenance

## Scope

This fork rebuilds the official WUD source at a fixed, published stable release, translates static Vue UI text into Simplified Chinese, validates translation placeholders, runs the upstream checks, and publishes a multi-architecture image after automated gates pass. It does not modify NAS containers.

## Safety and source

- Never expose `YOUDAO_APP_SECRET` or pass it to upstream code, Docker builds, or untrusted pull-request jobs.
- Never build from `main`, `latest`, or a moving branch. `upstream.lock.json` must contain the published release tag and resolved commit SHA.
- Never overwrite an existing immutable image version. A failed update must leave the last stable image tags unchanged.
- Publish jobs must serialize GHCR tag mutations, verify an existing immutable tag by manifest digest before resuming, and re-read `upstream.lock.json` from `main` immediately before moving `stable/latest`; an older queued build may publish its immutable version but must not roll aliases backward.
- WUD requires Docker API access to monitor a Docker host. A socket mounted `:ro` still grants powerful Docker API operations.
- Do not enable Docker or Docker Compose update triggers in the sample deployment.

## Workflow

1. Read `PROJECT_HANDOFF.md` and `docs/upstream-analysis.md`.
2. Check the actual published stable release and commit before translating.
3. Extract only static Vue template text and approved text attributes with the upstream Vue compiler parser. Do not translate identifiers, API keys, URLs, Docker references, or user data.
4. Reuse `translations/memory.json`; validate interpolation tokens before persisting any new translation.
5. Run upstream UI Jest tests against pristine English source first; current tests assert English UI literals. Then apply translations and run the production UI build plus project validation.
6. Review generated source, lock file, translation memory, coverage report, and workflow permissions when changing this automation.
7. Confirm image publication and manifest architectures after CI. Do not claim NAS runtime validation unless performed on that NAS.

The inherited upstream `ci.yml` workflow is disabled on this fork to prevent publishing an unrelated upstream image or deploying upstream documentation. Keep image builds behind the explicit `build-release.yml` dispatch from the successful translation workflow.

## References

- Upstream analysis and exact source boundaries: `docs/upstream-analysis.md`
- Translation API details: `docs/youdao-api.md`
- Build, restore, and release procedures: `docs/architecture.md`
