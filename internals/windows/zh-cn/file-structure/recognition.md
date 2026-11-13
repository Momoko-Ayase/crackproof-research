---
description: "基于文件内容的 KONN 识别、原生与托管 PE32/PE32+ 分类及各布局维度。"
icon: fingerprint
---

# 识别与构建类型

## 基于内容的识别与模块分类

满足以下两个条件的文件即匹配外层容器特征：

1. 文件长度至少为 `4128` 字节（`0x1020`），且 `e_lfanew`（`u32@0x3C`）指向合法的 `PE\0\0` 签名。
2. 对文件偏移 `4096` 处执行 `header_kdf` 后得到 `info[1] == 0x4E4E4F4B`（`KONN`）。

通过这两项检查即可锁定候选容器；完整校验还需核实 `info` 各区间未越界、阶段描述符有效，并通过各阶段校验和或试探解压验证。

识别出容器后，可根据标准 PE 头部字段将目标划分为四种模块类型：

* `IMAGE_FILE_HEADER.Characteristics & 0x2000`（`IMAGE_FILE_DLL`）区分 DLL 与 EXE。
* 数据目录第 `14` 项（`IMAGE_DIRECTORY_ENTRY_COM_DESCRIPTOR`；数据目录数组在 PE32 可选头部 `+96` 处起始，在 PE32+ 中为 `+112`）区分托管（.NET）程序集与原生二进制文件。

| `IMAGE_FILE_DLL` | CLR RVA（`DD[14]`） | 模块类型 |
| --- | --- | --- |
| `0` | `0` | `native-exe` |
| `0` | 非零 | `managed-exe` |
| 非零 | `0` | `native-dll` |
| 非零 | 非零 | `managed-dll` |

托管 EXE 与原生 EXE 共用相同的 EXE 壳容器。

```python
MAGIC_KONN = 0x4E4E4F4B  # the shell stamp

def detect(file_data):
    """Return ("native-exe" | "managed-exe" | "native-dll" | "managed-dll",
    magic) for a protected file, or None when the file is not protected by
    this scheme."""
    if len(file_data) < 4128:
        return None
    pe_off = get_u32(file_data, 0x3C)
    if file_data[pe_off:pe_off + 4] != b"PE\0\0":
        return None
    info = header_kdf(file_data)
    if info[1] != MAGIC_KONN:
        return None

    characteristics = get_u16(file_data, pe_off + 4 + 18)   # IMAGE_FILE_HEADER
    is_dll = bool(characteristics & 0x2000)                 # IMAGE_FILE_DLL

    # COM descriptor (CLR) data directory: managed vs native, EXE and DLL alike.
    # Data directories start at optional-header +96 on PE32, +112 on PE32+.
    opt_magic = get_u16(file_data, pe_off + 24)             # 0x10B / 0x20B
    dd_base = 112 if opt_magic == 0x20B else 96
    clr_rva = get_u32(file_data, pe_off + 24 + dd_base + 14 * 8)
    managed = bool(clr_rva)

    if is_dll:
        return ("managed-dll" if managed else "native-dll", info[1])
    return ("managed-exe" if managed else "native-exe", info[1])
```

{% hint style="info" %}
读取数据目录前务必先检查可选头部魔数（`0x10B` 或 `0x20B`）：`DD[14]` 在 PE32 中位于 `pe + 0xE8`，在 PE32+ 中位于 `pe + 0xF8`。若读错偏移，可能把 32 位原生二进制文件误判为托管程序集。
{% endhint %}

## 已观测到的布局维度

加壳后的 Windows 文件在以下四个结构维度上存在差异（实际仅出现特定组合：专用 DLL 容器仅见于 64 位有标记构建，外部伴生文件仅用于采用 EXE 壳结构的 PE32+ 构建）：

* **位数：** PE32+（`0x20B`，64 位）与 PE32（`0x10B`，32 位）共用 `header_kdf` 及核心加解密原语，但采用各自独立的配置表、阶段数量以及导入表与头部重建规则（其中 PE32 还细分为标准壳与紧凑壳两种变体）。
* **模块类型：** `native-exe`、`managed-exe`、`native-dll` 与 `managed-dll`。即便托管构建在磁盘上保留了明文 `COR20` 头部与 `BSJB` 元数据根，其 IL 方法体依然存放在加密压缩的节载荷内部。
* **64 位配置定位方式：**
  * **有标记布局（经典）：** Stage 5 内含字面特征串 `70 6D 00 00 63 6D 00 00`（`"pm\0\0cm\0\0"`）和 `00 00 00 40 01 00 00 00`（`0x40000000, 1`），各描述符表指针位于相对该标记的固定偏移处。
  * **无标记布局（新版）：** 移除了上述两处特征标记；Stage 5 内的指针槽位与字节码存根需通过 LFSR 扫描、`trial_byte_rotate2` 地址范围探测、`fileCS` 距离打分以及试探解压联合定位。
* **DLL 容器样式：**
  * **专用 DLL 布局：** 仅用于 64 位 DLL（`0x20B`）的容器，其配置表固定起始于 `info[6] + 5592`（`0x15D8`）。
  * **EXE 同构壳：** 使用与 EXE 相同的多阶段壳保护 32 位或 64 位 DLL，并支持拆分为[外部伴生文件（`._`）](companion-layout.md)。
