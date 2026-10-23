# Technical notes (Trinity Seven 7.7, `com.avex.trinityseven`)

Unity 2020.3.42, IL2CPP, arm64 + armv7. Analysis done with [Il2CppDumper](https://github.com/Perfare/Il2CppDumper) (`dump.cs`, `script.json`, `stringliteral.json`) and capstone/keystone. RVAs below are for version 7.7 only.

## Backend
- Hosts hardcoded in `Define`: `https://app-tri.poppin-games.com/` (API, `name_action` style) and two CloudFront hosts (asset bundles, `asset_info.json`). All dead. Without a server the game shows 「予期しないエラー」 and stops.
- Responses are plain JSON via `NetworkHelper.GetJson<T>` (GET) / `Post` (WWWForm). Shapes: `version_index`→`{min_version,store_url}`, `closing_get`→`{closed}`, `user_generateId`→`{user_id}`, list routes→`[]`, `time_index`→unix seconds as text.
- Game data (masters, enemy art, tutorial prefabs) is inside the APK (`assets/bin/Data/<hash>`), not downloaded. Empty `assetBundle_index` is fine.
- 50 `app-tri` endpoints exist. Every `GetJson<List<T>>`/`GetJsonArray` route answers `[]` (`LIST_ROUTES` in `stub_server.py`, same `case` list in `StubProvider.java`). Still `{}`: object endpoints (question filter, support rank, `storyMaker_getFromCode`, team score, cropro rewards) and unknown shapes (`ranking_getRankListAndSelfRank`, `team_getJoinTeamNo`).

## Locale bug (enemy never dies, tutorial never starts)
il2cpp takes `CultureInfo.CurrentCulture` from JNI `java.util.Locale.getDefault()`. Under a comma-decimal locale (pt-BR, es, fr, de...), `EnemyManager.UpdateHpBar` (0xC2088C) formats a BigInteger and calls `Single.Parse`, which throws. That aborts `EnemyManager.SetView`, so `CreateNewEnemy` never sets `isEnemyExist` (0xD8). `OnDamageHit` then drops all damage, the HP bar stays empty and tutorial dialogs never chain.

Fix: `StubProvider` calls `Locale.setDefault(Locale.JAPAN)` in `onCreate` and again in `onActivityPreCreated/onActivityCreated`, because Android reapplies the system locale on activity launch. ja-JP uses a decimal point and keeps the UI Japanese. Verified on the emulator under system pt-BR: Japanese text, tutorial, Lilith granted, enemies die, boss tutorial reached. The first fight needs the deck filled via 自動編成, otherwise damage is 0.

## Tutorial
`SpecialDialogMasterTableAsset` has rows `tuto_introduction`, `tuto_servant` (reward `servant` id 1 = Lilith), `tuto_swipe`, `tuto_tap`, `tuto_get_magus_1/2`. The tutorial grants Lilith itself; no native servant patch is needed.

## Backup (`savedata/index.php`)
Protocol from `EasySaveHelper`: POST fields `tag` (user id), `password`, `mode` = upload|download|delete, `filename`=`__tmp_esbu__`, binary `data` (multipart on upload, urlencoded otherwise). Reply: empty = success, `05` = not found, `04` = unknown. A reply of `{}` counts as success and a restore would write `{}` as the save and run `SaveWrapper.DeleteAll`, so the stub must never answer that. Storage key: sha1(`tag\0password`). Embedded server: `Android/data/com.avex.trinityseven/files/savedata/` (wiped on uninstall). The game also enforces a 1-day cooldown after a backup or restore.

## Native patches (`libil2cpp.so`, arm64 only)
`server/patch_lib.py` rewrites two bool getters to `return true` and checks the original bytes first:
- `AdManager.IsVideoSkip` (0xE321F4): the game's own paid "skip video ads" state, so video rewards need no AdMob. Not yet exercised on screen (the features unlock later in progression).
- `NetworkHelper.IsCanConnectNetwork` (0xEF483C): the backend is local, so always reachable. Verified in airplane mode.

## Language choice at build time
The forced `Locale` decides the game language: `Locale.JAPAN` keeps the Japanese UI, `Locale.US` gives English (title, buttons, terms, chapter titles verified on the emulator; story dialogue not checked). Both use a decimal point, so the locale bug stays fixed. `build.py --lang ja|en` substitutes the locale in a copy of `StubProvider.java` before compiling (default `ja`; the flag is `ja`, not `jp`, to match the language code). Idea: pick the language on the device instead of at build time, for example a setting read by `StubProvider` before it calls `Locale.setDefault`, so one APK serves both.

## Save data
`Android/data/com.avex.trinityseven/files/es2/` (Easy Save, mostly encrypted; `STAGE_DATA` readable base64 BinaryFormatter). Servant ownership key: `SERVANT_LV_SAVE_KEY_<id>`.

## Testing notes
- Emulator: Android 11 (API 30) google_apis x86_64 with arm64 translation. Fresh data: `adb shell pm clear`.
- MIUI blocks `pm clear` and `adb install` of fresh installs (`INSTALL_FAILED_VERIFICATION_FAILURE`); copy the APK to `Download/` and install by tapping.
- `python -I server/test_stub.py <base-url>` checks both stubs (route formats, backup flow, same route list). Reach the embedded one with `adb forward tcp:8095 tcp:8080`.

## Ideas
Remove banner ads (`IsBannerSkip`, `IsInstSkip`); free store purchases; patch armv7; public backup folder; local ranking/tournament; local Story Maker.
