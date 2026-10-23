# Trinity Seven Offline

A patch that makes **トリニティセブン 夢幻図書館と第7の太陽** (*Trinity Seven: Phantasm Library & Seventh Sol*, Android, version 7.7) playable again without the original Poppin Games servers, which were shut down.

The game server now runs **inside the app itself**. No PC, no second app and no internet connection needed.

> **Legal notice.** Non-profit preservation project, not affiliated with Avex Technologies, Poppin Games Japan or KADOKAWA. This repository **does not distribute the APK or any game files**, only the tools that patch a copy you already own. Trinity Seven © Kenji Saito, Akinari Nao / KADOKAWA.
>
> The code in this repository is under the [MIT](LICENSE) license. It does not cover the game, which remains the property of its rights holders.

---

## Version 0.9

### What works

- Opening, terms of service, intro story and the full tutorial (the first character, Lilith, is granted by the tutorial itself).
- Auto battle, taps, bosses, story unlocks, Magic Training and offline progress.
- Gifts and news (empty), data backup and restore ("Data Backup" / "Change Device").
- All of it in **airplane mode**.

### Changes from the original game

#### 1. Servers redirected to the device itself
The game had three hardcoded addresses: `app-tri.poppin-games.com` (API) and two CloudFront hosts (files and pages). All are offline, and without them the game stopped at the error screen 「予期しないエラーが発生しました」.
`patch_apk.py` rewrites the **54 strings** holding those addresses inside `global-metadata.dat`, replacing them with `http://127.0.0.1:8080`.

#### 2. Server embedded in the APK
A Java `ContentProvider` (`com.t7stub.StubProvider`, in `classes4.dex`) starts an HTTP server on `127.0.0.1:8080` when the app opens, before Unity. It replaces the original API:

| Route | Response |
|---|---|
| `version_index`, `closing_get`, `user_generateId`, `time_index` | accepted version, server open, ID `100000001`, device time |
| `ban_get`, `news_get`, `present_index`, `saveRefresh_index`, `assetBundle_index`, `article_index`, `cropro_getCampaigns`, `bbs_get`, `question_*`, `storyMaker_*List`, `ranking_getTournament`, `ranking_getTeamRankList` | `[]` (empty list, the format the game expects) |
| `text_index` | share text |
| `savedata/index.php` | real backup (see item 4) |
| `/release/...` | simple HTML page for Help, Terms, Privacy and Credits |
| anything else | `{}` |

The game data (characters, enemies, stages, tutorial) is already inside the APK; nothing is downloaded.

#### 3. Fix for the enemy that would not die and the tutorial that would not start
On devices whose language uses a **decimal comma** (Portuguese, Spanish, French, German...), `EnemyManager.UpdateHpBar` calls `Single.Parse`, which throws. The enemy is never marked as existing: the HP bar stays empty, no damage is applied, taps turn into balls on the board and the tutorial dialogs never continue.
The embedded server forces the **ja-JP** culture (`Locale.setDefault`, which also uses a decimal point) when the app opens and again before the Unity Activity, because Android reapplies the system language at that point.
The forced language is Japanese by default, with the original texts. `build.py --lang en` forces `Locale.US` instead, and the interface, terms and chapter titles appear in English.

#### 4. Backup and restore working
The "Data Backup" button generates an ID and a device-transfer code; "Change Device" restores with them. The original protocol (`EasySaveHelper`) was reimplemented: `upload`, `download` and `delete`, with an empty reply for success and `05` for not found.
Before this version the server answered `{}`, which the game read as **success**. A restore would have written `{}` as the save and wiped the local data.
The backup is stored in `Android/data/com.avex.trinityseven/files/savedata/`.

#### 5. Video rewards without ads
`AdManager.IsVideoSkip` now returns `true`. This is the "skip ads" mode the game used to sell: every "watch video" button (video box, login bonus, mining, prestage, rematch, Story Maker) grants the reward immediately, without loading AdMob.

#### 6. Works without internet
`NetworkHelper.IsCanConnectNetwork` now returns `true`, since the server is local. In airplane mode this unlocks the title-screen backup, the automatic backup and the clock check done when collecting rewards (for example Magic Training). Before, all of them showed "Cannot connect to the network".

#### 7. Signature
The APK is re-signed with its own (debug) key, so it cannot be installed over the Play Store version.

### Known limitations

- **Fixed language** (Japanese or English, chosen when building the APK), regardless of the system language (a consequence of item 3).
- **Online features do not work:** ranking, tournament, teams, questions and answers, Story Maker sharing, purchases (Google Play Billing) and Google Play Games. They open empty or fail without crashing the game.
- **Native patches (items 5 and 6) are arm64 only.** On old 32-bit devices the game runs, but without those two.
- **The backup is deleted together with the app** (on uninstall or clearing data). To switch devices, copy the `savedata` folder to the new one (see below).
- **Original 1-day rule:** after a backup or restore, the game blocks a new backup for 24 h.
- **The user ID is always `100000001`.** It does not matter offline, but it rules out a server shared between players.
- **With internet, banner ads still appear** (AdMob test ads).
- **Tested** on the Android 11 emulator (API 30, x86_64 image with arm64 translation). Video rewards were checked in the code and in game memory, but not yet triggered on screen (they unlock later in the game).

---

## Installation

1. Uninstall the original Trinity Seven if it is installed (the signature is different).
2. Copy the generated APK to the phone and tap it to install. On Xiaomi/MIUI, installing through `adb` is usually blocked; install from the file manager.
3. On first launch, cancel the Google Play Games prompt.

### Switching devices

On the old device, make the backup from the title screen and write down the ID and code. From Android 11 on, the `Android/data` folder is only reachable from a PC:

```bash
adb pull /sdcard/Android/data/com.avex.trinityseven/files/savedata savedata-backup
```

Install on the new device, open the game once and push the folder:

```bash
adb push savedata-backup/. /sdcard/Android/data/com.avex.trinityseven/files/savedata/
```

Then use "Change Device" on the title screen with the ID and code.

---

## Building the APK

### Requirements

- Original APK `trinity-seven-7-7.apk` (version 7.7, versionCode 88). SHA-256:
  `13b3b9f2e9e127fc13fd3b636b376fdd66bddd356cb44e996caa3470b3ca958c`
- Python 3.9 or newer (standard library only)
- JDK 11 to 21 (`javac --release 8`)
- Android SDK: `platforms/android-30` and `build-tools` (for `d8`)
- [apktool](https://apktool.org/) 3.0.3 and [uber-apk-signer](https://github.com/patrickfav/uber-apk-signer) 1.3.0

### Steps

Put `apktool.jar` and `uber-apk-signer-1.3.0.jar` in this folder (or pass `--apktool` and `--signer`) and run:

```bash
python build.py trinity-seven-7-7.apk --sdk /path/to/android-sdk
```

The script checks the APK's SHA-256, installs the embedded server, applies the patches and signs. The final APK is `out/Trinity7-offline.apk`. `--lang en` builds the English version (`out/Trinity7-offline-en.apk`); the default is `ja`. `--host` changes the server address (see below).

### Server on the PC (optional)

To use a PC server instead of the embedded one (handy for debugging, since it logs every request), build the APK with `--host http://PC-IP:8080` and run:

```bash
python -I server/stub_server.py 8080
```

The new address can be at most 32 characters long (the length of `https://app-tri.poppin-games.com`). Backups are stored in `server/savedata/`.

### Tests

```bash
python -I server/test_stub.py http://127.0.0.1:8080
```

Tests either server over HTTP (routes, formats and a full backup cycle) and checks that the Python and Java servers list the same routes. To test the embedded server, open the game on the device and forward the port with `adb forward tcp:8080 tcp:8080`.

---

## Layout

| File | Purpose |
|---|---|
| `build.py` | builds the APK from the original (one command) |
| `server/embedded/com/t7stub/StubProvider.java` | server embedded in the APK and the language fix |
| `server/stub_server.py` | the same server in Python, to run on a PC |
| `server/patch_apk.py` | replaces the addresses in `global-metadata.dat` and applies `patch_lib.py` |
| `server/patch_lib.py` | patches to `libil2cpp.so` (arm64) |
| `server/test_stub.py` | tests for both servers |
| `HANDOFF.md` | reverse-engineering technical notes |
| `CLAUDE.md` | conventions for working on this repository |

The analysis was done with [Il2CppDumper](https://github.com/Perfare/Il2CppDumper) and capstone. The addresses (RVAs) in `patch_lib.py` are valid for version 7.7 only; the script checks the original bytes before changing anything and aborts if they do not match.

## Reporting problems

Use the [issue forms](../../issues/new/choose): include your phone model, Android version, system language, patch version and steps to reproduce. For a log, run `adb logcat -d > log.txt` right after the error and attach the file.
