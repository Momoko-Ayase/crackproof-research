---
description: "整理干净的 ELF64 节表、清零 e_entry、原子写入并校验恢复后的共享库。"
icon: file-export
---

# ELF 输出

`PT_LOAD` 加载段与动态链接表重建完毕后，ELF 收尾阶段会移除保护壳特有的结构，并重写文件尾部的非加载数据：

1. **移除 SHT_LOUSER 私有节**：删去末尾的私有节头，第一阶段与第二阶段载荷字节均不拷贝到输出文件中。
2. **将 e_entry 清零**：Android 共享库通过 `.init_array` 而非 `e_entry` 执行原生构造函数，因此将 `e_entry` 置为 `0`。
3. **重定位非 SHF_ALLOC 节**：保留下来的非加载节（如 `.shstrtab`）紧凑排列在所有可加载段（包括新追加的 `PF_R` `PT_LOAD` 段）末尾之后；校验 `.shstrtab` 合法性后，在文件最末尾写出更新后的 `Elf64_Shdr` 节表，并更新 `e_shoff` 与 `e_shnum`。
4. **原子写入并重新解析**：写入文件时先写出临时文件再执行原子替换，随后对输出文件重新执行完整 ELF 解析校验。

{% hint style="info" %}
**写后硬性校验与结构诊断。** 输出校验分为两级：
* **硬性错误**（直接中止恢复）：ELF64 小端序 AArch64 解析失败、`PT_LOAD` 文件区间超出输出文件长度、`.shstrtab` 格式损坏、残留 `SHT_LOUSER` 私有节、`e_entry` 非零，或 `.dynsym` / `.rela.dyn` / `.rela.plt` 表项数与重建表不一致。
* **跨表结构诊断**（作为告警上报）：参照动态链接器约束检查 `PT_LOAD` 对齐/同余/重叠、`DT_*` 标签与节表一致性、`DT_RELACOUNT` 前缀顺序、符号哈希桶边界、重定位目标地址与符号范围，以及 `.init_array` / `.fini_array` 函数指针有效性。
{% endhint %}
