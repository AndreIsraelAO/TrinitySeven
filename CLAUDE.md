# Conventions for this repository

- **Language:** all documentation (README, HANDOFF, issue templates, code comments, script messages) is written in English. The only non-English text allowed is game content that must stay as is (for example the Japanese share text and the game's own strings).
- **Commits:** every commit message is written in English, in the imperative mood and with a short subject (for example "Add --lang option to build.py"). Do not add `Co-Authored-By` trailers or any other attribution line to commits.
- **Never commit** APKs, extracted game assets, Il2CppDumper output, `build/`, `tools/`, `work/`, `out/` or screenshots. See `.gitignore`.
- **Build and test:** `python build.py <original-apk> [--lang ja|en]` builds the APK; `python -I server/test_stub.py <base-url>` tests the servers. The RVAs in `server/patch_lib.py` are valid for version 7.7 only.
- **Docs to keep in sync:** when behavior changes, update `README.md` (user-facing) and `HANDOFF.md` (technical notes) in the same commit.
