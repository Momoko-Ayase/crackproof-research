---
description: "外部 global-metadata.dat 应用配对与内嵌 XOR 精简版 v24 元数据块。"
icon: table
---

# 存储布局

受保护的 Android IL2CPP 构建采用以下两种元数据存储形式之一：

| 变体 | 位置 | 解封后格式 |
| --- | --- | --- |
| 外部 `global-metadata.dat` | `assets/bin/Data/Managed/Metadata/`（或分包资源 APK）下的独立文件 | 带标准 `0xFAB11BAF` 文件头的版本 `24`（`v24.1`）、`29`、`31` 或 `39` |
| 内嵌精简 + XOR 数据块 | 还原后 `libil2cpp.so` 镜像内的 `0x2701F30` 字节数据块 | 探测双字 `[0x9732CA38, 0xBAC4374F]` 改写为 `[0xFAB11BAF, 24]` |

{% hint style="info" %}
第二阶段 `0x5C` 记录描述符中的 `metadata_offset` / `metadata_size` 字段指向的是保护壳模块自身的加载、重定位与导入元数据，而非 IL2CPP 的 `global-metadata.dat`。将外部 `v24.1` `global-metadata.dat` 与模块 `0x0C` 配对时，两个文件必须属于同一应用包（跨分包 APK 的 `AndroidManifest.xml` `package` 与 `versionCode`/`versionCodeMajor` 一致，或位于同一 `<root>/lib/<abi>/` 与 `<root>/assets/` 目录树下）。
{% endhint %}

## 内嵌精简 + XOR 变体

早期一种版本 `24` 打包变体不在 `assets/` 下提供 `global-metadata.dat`，而是将一个 `0x2701F30` 字节的 XOR 掩码数据块嵌入还原后 `.so` 的数据节中：

* **结构：** 开头为 `0x100` 字节头部（64 个小端 `u32` 字，每个头部字对应一个独立的 32 位 XOR 密钥），后跟 256 个长度不规则的正文分段（每段对应一个 32 位 XOR 密钥，按双字逐一异或）。
* **头部探测与修补：** 用 `[0x39184C70, 0xD901AFD4]` 异或前两个双字，可得到字节序反转的特征值对 `[0x9732CA38, 0xBAC4374F]`。依次应用 64 个头部密钥与 256 个分段密钥后，再将前两个双字改写为 `[0xFAB11BAF, 24]`，即可得到有效的精简版 v24 元数据文件。
* **密钥推导现状：** 运行时，元数据加载器会动态生成这 320 个 `u32` 密钥；目前尚未从 `.so` 中逆向出静态推导该密钥流的完整逻辑。同一产品线的后续构建已改用带种子 `MethodDef` 置换的外部 `global-metadata.dat` 文件。
