"""Offline patches for libil2cpp.so (arm64-v8a, il2cpp v27 build of Trinity Seven 7.7): RVA == file offset.
Each patched method is a bool getter rewritten to `return true`. The armv7 lib is not patched."""

RETURN_TRUE = bytes.fromhex("20008052c0035fd6")  # mov w0, #1 ; ret

# RVA -> (method, first 8 original bytes)
PATCHES = {
    # The game's own paid "skip video ads" state: IsVideoAdReady/ShowVideoAd then report success at once,
    # so every video reward (ad box, login bonus, mining, prestage, revenge, story maker) works without AdMob.
    0xE321F4: ("AdManager.IsVideoSkip", "f30f1ef8fd7b01a9"),
    # Asks Android for internet; the backend is local now, so it is always reachable. Unblocks the title backup,
    # AutoBackup and CheatManager's server-clock checks (Magic Training claim) in airplane mode.
    0xEF483C: ("NetworkHelper.IsCanConnectNetwork", "fd7bbfa9fd030091"),
}

def patch(lib: bytearray) -> None:
    for rva, (name, orig) in PATCHES.items():
        assert bytes(lib[rva:rva + 8]) == bytes.fromhex(orig), f"unexpected libil2cpp.so build at {name}"
        lib[rva:rva + 8] = RETURN_TRUE
