---
description: "识别受保护 PE 文件的结构检查，以及不同构建家族的布局。"
---

# 识别与构建家族

## 识别与分类

受保护文件基于内容识别，与文件名或扩展名无关。初步筛选条件是：

1. 至少 4128 字节长，且 `e_lfanew`（`u32@0x3C`）处有有效 `PE\0\0` 签名。
2. 对偏移 4096 应用 KDF 得到 `info[1] == KONN`。

这两项只能确定候选文件。接受具体布局前，还必须确认每个 `info` 范围都位于文件内，阶段记录与节记录边界有效，并且至少有一项后续校验和或解码成功。不能只凭 `KONN` 信任所有派生偏移。

分类使用常规 PE 字段。两个字段对每个候选都适用；EXE/DLL 与原生/托管相互独立：

- `IMAGE_FILE_HEADER.Characteristics & 0x2000`（`IMAGE_FILE_DLL`）区分 DLL 与 EXE。
- COM 描述符（CLR）数据目录——第 14 项，位于可选头 PE32 `+96` 或 PE32+ `+112` 处——区分托管（.NET）与原生。

四种组合是：

| `IMAGE_FILE_DLL` | CLR RVA | 种类 |
| --- | --- | --- |
| 未置位 | 0 | 原生 EXE |
| 未置位 | 非零 | 托管 EXE |
| 置位 | 0 | 原生 DLL |
| 置位 | 非零 | 托管 DLL |

托管 EXE 使用与原生 EXE 相同的 EXE 风格容器。分类只需要 CLR 目录这一处 PE 头差异，它不是第五种布局家族。

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
用错数据目录基址（96 与 112）会读错 dword，把 32 位原生映像误判为托管。必须先读可选头 magic。对 EXE 跳过 CLR 检查会把托管 EXE 并入原生 EXE。
{% endhint %}

## 构建家族

实际样本中观察到的受保护文件沿四条轴变化，各轴相互独立，所有组合都需要处理。

**位宽。** PE32+（可选头 magic `0x20B`，64 位）与 PE32（`0x10B`，32 位）容器共享头部/payload 层，但使用完全不同的配置布局、阶段结构与最终 PE 修补。

**对象种类。** 原生 EXE、托管 EXE、原生 DLL 与托管 DLL（见上文分类）。某些托管布局会在受保护文件中原样保留 COR20 头与 BSJB 元数据流。这不表示托管方法体是明文；方法体仍属于需要按正常流程恢复的节。

**配置布局。** 64 位加载器配置有两代：

- **标记布局**（较旧构建）在加载器最终阶段内嵌字节标记 `70 6D 00 00 63 6D 00 00`（`"pm\0\0cm\0\0"`——加载器的双字母子模块代码）与 `00 00 00 40 01 00 00 00`（一个 `0x40000000, 1` dword 对）。每张重要的表都位于这些标记的固定偏移处。
- **无标记布局**（较新构建，包括以 EXE 风格外壳包裹的 DLL）省略两个标记。表的位置要根据记录形态、嵌入式变换程序、指针范围，以及对压缩记录的试解码共同确定。

**DLL 打包方式。** DLL 有两种保护形态：

- **专用 DLL 布局**（较旧）：DLL 专属容器，其配置块位于固定偏移（`keys[6] + 5592`），无需扫描锚点。
- **EXE 风格外壳**（较新）：DLL 被套上与 EXE 相同的外壳布局。下面的外置伴生体拆分即属于这一家族。
