#!/usr/bin/env bash
# Rebuild only librime and its merged plugins against checksum-pinned dependencies.
set -euo pipefail
abi=${1:?ABI required}
deps=$(realpath "${2:?Pinned prebuilt checkout required}")
work=$(realpath -m "${3:?Build output required}")
repo=$(git rev-parse --show-toplevel)
ndk=${ANDROID_NDK_ROOT:?Android NDK required}
cmake_bin=${CMAKE_BIN:-cmake}
case "$abi" in armeabi-v7a|arm64-v8a|x86|x86_64) ;; *) exit 2 ;; esac
mkdir -p "$work"
python3 "$repo/scripts/prepare-librime.py" "$work/sources"
prefix="$work/product/librime/$abi"
roots=""
for dependency in boost glog yaml-cpp leveldb marisa opencc lua; do
  test -d "$deps/$dependency/$abi"
  roots+="${roots:+;}$deps/$dependency/$abi"
done
"$cmake_bin" -S "$work/sources/librime" -B "$work/cmake" -G Ninja \
  -DCMAKE_TOOLCHAIN_FILE="$ndk/build/cmake/android.toolchain.cmake" \
  -DANDROID_ABI="$abi" -DANDROID_PLATFORM=23 -DANDROID_STL=c++_shared \
  -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX="$prefix" \
  -DBUILD_SHARED_LIBS=OFF -DBUILD_STATIC=ON -DBUILD_TEST=OFF -DBUILD_TOOLS=OFF \
  -DALSO_LOG_TO_STDERR=ON -DCMAKE_FIND_ROOT_PATH="$roots" \
  "-DCMAKE_CXX_FLAGS=-ffile-prefix-map=$repo=. -DBOOST_ALL_NO_EMBEDDED_GDB_SCRIPTS"
"$cmake_bin" --build "$work/cmake" --target rime-static --parallel 2
"$cmake_bin" --install "$work/cmake"
"$ndk/toolchains/llvm/prebuilt/linux-x86_64/bin/llvm-strip" --strip-unneeded "$prefix/lib/librime.a"
rm -rf "$prefix/lib/pkgconfig" "$prefix/bin"
python3 - "$work" "$prefix" "$deps" "$abi" <<'PY'
import hashlib,json,subprocess,sys
from pathlib import Path
work,prefix,deps=map(Path,sys.argv[1:4]);abi=sys.argv[4]
hash_file=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
record=json.loads((work/'sources/source-manifest.json').read_text())
record.update({'abi':abi,'dependency_prebuilt_commit':subprocess.check_output(['git','-C',str(deps),'rev-parse','HEAD'],text=True).strip(),
    'platform':23,'ndk':'28.0.13004108','cmake':'3.31.6','cxx_standard':17,
    'archive_sha256':hash_file(prefix/'lib/librime.a'),
    'rime_api_sha256':hash_file(prefix/'include/rime_api.h'),
    'boost_version_header_sha256':hash_file(deps/'boost/include/boost/version.hpp')})
record['dependency_archives_sha256']={d:hash_file(deps/d/abi/'lib'/('lib'+('lua_static' if d=='lua' else d)+'.a'))
 for d in ['glog','yaml-cpp','leveldb','marisa','opencc','lua']}
text=(prefix/'include/rime_api.h').read_text()
assert 'get_input_tabs' in text and 'free_input_tabs' in text
out=prefix/'share/rime/source-manifest.json';out.parent.mkdir(parents=True,exist_ok=True)
out.write_text(json.dumps(record,indent=2)+'\n')
PY
