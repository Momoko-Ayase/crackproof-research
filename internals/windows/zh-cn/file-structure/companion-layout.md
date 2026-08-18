---
description: 如何定位节载荷，以及 stub 可执行文件如何引用外置伴生文件。
---

# 节数据与伴生文件

## 在文件中定位节数据

加载器表内的节内容描述符存储的偏移，相对于一个本身以补码编码在文件偏移 `0x1080` 处的基址：

```
section_data_file_base = (~u32@0x1080) + 0x1000      (32-bit wrapping)
```

因此描述符的 `src` 字段映射到文件偏移 `src + section_data_file_base`。同一公式出现在所有构建家族中（在加载器代码里既称 `rebase` 又称 `compress_data_offset`）。

## 外置伴生体布局（`._` 文件）

某些构建——目前仅在 il2cpp 作品上观察到——把受保护模块拆成一对文件：

* **`Foo.dll`**——磁盘上的瘦**加载器 stub**。其代码节被裁剪到只剩一页（即 CrackProof 加载器本体），但其头部与 `.rdata` 是完整明文。
* **`Foo.dll._`**——全加密的**伴生体**，持有真正的 payload。它不含任何明文 PE 结构（熵 ≈ 8 比特/字节）。

伴生体逐字节等于 stub 自 CrackProof 头部（偏移 4096）起的 payload 区。运行时加载器映射 `Foo.dll._` 并对其执行常规解包；实际运行的模块实际上就是拼接体 `stub[..4096] ++ companion`。

配对关系由 32 字节精确匹配确认：`stub[4096..4128] == companion[0..32]`。这 32 字节覆盖加密 info 头（密钥表与 magic），因此匹配即证明该伴生体就是此 stub 的 payload，而非无关文件。

stub 以明文保留的内容对后续重建很重要：

* **导出目录**（伴生体在此处解密为密文；加载器运行时从 stub 的副本重建导出）。
* **TLS 目录**——`IMAGE_TLS_DIRECTORY` 结构体、其原始数据模板与数据目录项，这些都被保护层从加密 payload 中剥离（见 [PE 重建](../loading-and-pe-repair/pe-reconstruction/)）。
* 真实的 `DllCharacteristics` 字段与基址重定位表——伴生模块**不是** `/FIXED`，与较旧的单文件构建不同。

关于此文件对在启动时如何加载，见[运行时行为](../runtime/runtime.md)；关于缺失部分如何被还原进重建映像，见 [PE 重建](../loading-and-pe-repair/pe-reconstruction/)。
