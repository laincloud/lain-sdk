# LAIN SDK

[![Build Status](https://travis-ci.org/laincloud/lain-sdk.svg?branch=master)](https://travis-ci.org/laincloud/lain-sdk)
[![codecov](https://codecov.io/gh/laincloud/lain-sdk/branch/master/graph/badge.svg)](https://codecov.io/gh/laincloud/lain-sdk)
[![MIT license](https://img.shields.io/github/license/mashape/apistatus.svg)](https://opensource.org/licenses/MIT)

LAIN SDK 在 LAIN 集群中用于对 lain.yaml 的解析，包含 python parser 和 lua parser。

在 LAIN 中使用的为 python parser，提供给 [LAIN CLI](https://github.com/laincloud/lain-cli) 与 [console](https://github.com/laincloud/console) 使用。

目前 SDK 支持的 lain.yaml 格式可以查看 [LAIN White Paper](https://laincloud.gitbooks.io/white-paper/content/usermanual/lainyaml.html)。

## 打包上传到 PyPI

### 依赖

```
pip install twine  # 上传工具
pip install wheel  # 打包工具
```

### 打包上传

```
rm -rf dist/  # 清空以前的构建
python setup.py sdist  # 打包源代码
python setup.py bdist_wheel  # 构建 wheel
twine upload dist/*  # 上传
```
