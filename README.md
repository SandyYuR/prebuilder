# prebuilder

Build static libraries for [fcitx5-android](https://github.com/fcitx5-android/fcitx5-android).

## 中州鹅引擎维护

中州鹅的核心功能现在直接维护在 [SandyYuR/librime 的 zhongzhou 分支](https://github.com/SandyYuR/librime/tree/zhongzhou)。
本仓库通过 gitlink 固定源码，只准备插件、编译、测试和记录来源，不再应用核心 librime 补丁。
原 9 项补丁的导入提交与摘要位于源码仓库的 `downstream/manifest.json`；插件补丁继续留在 `patches/`。

日常 push、PR 和默认手动任务仅构建 librime；历史整套依赖构建需显式选择 `everything`。
新流程：librime 源码 PR → 更新本仓库 gitlink → 四 ABI 与原生测试 → 审核 prebuilt 产物 PR → 更新输入法 gitlink 与设备验证。
不会自动跟踪移动分支或将未经审核的引擎产物发布到 prebuilt 默认分支。

```sh
git submodule update --init librime librime-lua librime-octagram librime-predict-leveldb
python3 scripts/verify-librime-source.py
python3 scripts/test-librime-source.py
# 在 GitHub Actions 选择 librime-only；本地需固定 NDK 与 CMake：
bash scripts/build-librime-only.sh arm64-v8a /path/to/pinned-prebuilt build/librime-arm64
```

## Build environment

Cabal is required to build this project.

### Android related

* Android Platform (API Level): `23`
* Android NDK: `28.0.13004108`
* CMake Version: `3.31.6`

both can be installed with `sdkmanager` command line tool.

### System dependencies

* `tar curl git`
* `ghc haskell-shake haskell-aeson-pretty cabal-install`: haskell stuff
* `cmake extra-cmake-modules ninja`: cmake stuff
* `python`: build dep of `opencc`
* `opencc`: for `opencc_dict`
* `gperf`: build dep of `libiconv`

## Libraries

* boost ([cmake build](https://github.com/boostorg/cmake)): [boostorg/boost](https://github.com/boostorg/boost)
* libuv: [libuv/libuv](https://github.com/libuv/libuv)
* libintl-lite: [j-jorge/libintl-lite](https://github.com/j-jorge/libintl-lite)
* fmt: [fmtlib/fmt](https://github.com/fmtlib/fmt)
* fcitx5: [fcitx/fcitx5](https://github.com/fcitx/fcitx5)
* zstd: [facebook/zstd](https://github.com/facebook/zstd)
* libime data: [fcitx/libime](https://github.com/fcitx/libime)
* libime-jyutping data: [fcitx/libime-jyutping](https://github.com/fcitx/libime-jyutping)
* lua (cmake build): [walterschell/Lua](https://github.com/walterschell/Lua)
* opencc: [BYVoid/OpenCC](https://github.com/BYVoid/OpenCC)
* anthy-unicode: [fujiwarat/anthy-unicode](https://github.com/fujiwarat/anthy-unicode)
* glog: [google/glog](https://github.com/google/glog)
* yaml-cpp: [jbeder/yaml-cpp](https://github.com/jbeder/yaml-cpp)
* leveldb: [google/leveldb](https://github.com/google/leveldb)
* marisa-trie: [s-yata/marisa-trie](https://github.com/s-yata/marisa-trie)
* librime: [SandyYuR/librime](https://github.com/SandyYuR/librime)（上游 [rime/librime](https://github.com/rime/librime)）
* librime-lua: [rime/librime-lua](https://github.com/hchunhui/librime-lua)
* librime-octagram: [rime/librime-octagram](https://github.com/lotem/librime-octagram)
* libhangul: [libhangul/libhangul](https://github.com/libhangul/libhangul)
* libchewing: [chewing/libchewing](https://github.com/chewing/libchewing)
* libthai: [tlwg/libthai](https://github.com/tlwg/libthai)
* libiconv: [GNU/libiconv](https://savannah.gnu.org/projects/libiconv)
