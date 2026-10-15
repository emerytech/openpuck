#!/usr/bin/env python3
"""Run production mapping persistence/migration against an in-memory filesystem."""
import os
from pathlib import Path
import shlex
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
FS = r'''
#pragma once
#include <algorithm>
#include <cstring>
#include <vector>
#include <cstdint>
#define FILE_O_READ 0
#define FILE_O_WRITE 1
struct MemoryFS {
    bool present = false;
    unsigned writes = 0;
    std::vector<uint8_t> bytes;
    void remove(const char *) { present = false; bytes.clear(); }
};
extern MemoryFS InternalFS;
namespace Adafruit_LittleFS_Namespace {
struct File {
    MemoryFS &fs;
    size_t pos = 0;
    explicit File(MemoryFS &f) : fs(f) {}
    bool open(const char *, int mode) {
        pos = 0;
        if (mode == FILE_O_WRITE) { fs.present = true; ++fs.writes; }
        return fs.present;
    }
    int read(uint8_t *out, size_t size) {
        size_t n = std::min(size, fs.bytes.size() - pos);
        if (n) std::memcpy(out, fs.bytes.data() + pos, n);
        pos += n;
        return static_cast<int>(n);
    }
    void write(const uint8_t *in, size_t n) {
        fs.bytes.insert(fs.bytes.end(), in, in + n);
    }
    void close() {}
};
}
'''
TEST = r'''
#include "lizard_map.h"
#include "Adafruit_LittleFS.h"
#include <cassert>
#include <iostream>
MemoryFS InternalFS;
void fixture(std::vector<uint8_t> bytes, bool present = true) {
    InternalFS = {present, 0, bytes};
    g_lizardMap.count = 17; // Detect stale state surviving a failed load.
}
int main() {
    for (int version : {1, 2}) {
        fixture({0xB1, static_cast<uint8_t>(version), 0});
        loadLizardMap();
        assert(g_lizardMap.count == 0);
        assert(InternalFS.writes == (version == 1 ? 1u : 0u));
        assert(InternalFS.bytes == std::vector<uint8_t>({0xB1, 2, 0}));
        loadLizardMap();
        assert(g_lizardMap.count == 0);
        assert(InternalFS.writes == (version == 1 ? 1u : 0u));
    }
    for (auto bytes : std::vector<std::vector<uint8_t>>{
        {}, {0xB1}, {0,2,0}, {0xB1,99,0}, {0xB1,2,33},
        {0xB1,1,1}, {0xB1,2,1}}) {
        fixture(bytes);
        loadLizardMap();
        assert(g_lizardMap.count > 0 && InternalFS.writes == 1);
    }
    fixture({}, false);
    loadLizardMap();
    assert(g_lizardMap.count > 0 && InternalFS.writes == 1);
    // One v1 keyboard binding: physical A plus virtual left-stick right;
    // virtual up as its hold condition. The old high nibble must move.
    fixture({0xB1,1,1, 1, 0,4,0,0,0,0,0,
             1,0,0,0x10, 0,0,0,0x80});
    loadLizardMap();
    assert(g_lizardMap.count == 1 && InternalFS.writes == 1);
    const auto migrated = g_lizardMap.bindings[0];
    assert(migrated.outType == 1 && migrated.outData[1] == 4);
    assert(migrated.trigMask == (1ULL | (1ULL << 32)));
    assert(migrated.holdMask == (1ULL << 35));
    loadLizardMap();
    assert(g_lizardMap.count == 1 && InternalFS.writes == 1);
    assert(std::memcmp(&migrated, &g_lizardMap.bindings[0], sizeof migrated) == 0);
    std::cout << "Mapping persistence: empty v1/v2, migration, reload, invalid and truncated files PASS\n";
}
'''
with tempfile.TemporaryDirectory(prefix="openpuck-map-") as name:
    tmp = Path(name)
    (tmp / "class/hid").mkdir(parents=True)
    (tmp / "Adafruit_LittleFS.h").write_text(FS)
    (tmp / "InternalFileSystem.h").write_text('#include "Adafruit_LittleFS.h"\n')
    keys = ('DELETE','O','ENTER','ESCAPE','PAGE_UP','PAGE_DOWN','TAB',
            'ARROW_UP','ARROW_DOWN','ARROW_LEFT','ARROW_RIGHT')
    (tmp / "class/hid/hid.h").write_text('\n'.join(
        f'#define HID_KEY_{key} {i+1}' for i, key in enumerate(keys)))
    (tmp / "test.cpp").write_text(TEST)
    exe = tmp / "test"
    subprocess.run(shlex.split(os.environ.get('CXX', 'c++')) + [
        '-std=c++17', '-Wall', '-Wextra', '-Werror',
        '-fsanitize=undefined', '-fsanitize-trap=undefined',
        '-I'+str(tmp), '-I'+str(ROOT/'OpenPuck'), str(tmp/'test.cpp'),
        str(ROOT/'OpenPuck/lizard_map.cpp'), '-o', str(exe)], check=True)
    subprocess.run([str(exe)], check=True)
