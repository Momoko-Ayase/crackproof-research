# Table of contents

* [CrackProof for Windows 内部机制](README.md)

## 文件结构 <a href="#file-structure" id="file-structure"></a>

* [概览](file-structure/file-format.md)
* [容器与加密头](file-structure/container-layout.md)
* [识别与构建家族](file-structure/recognition.md)
* [节数据与伴生文件](file-structure/companion-layout.md)

## 数据变换 <a href="#data-transforms" id="data-transforms"></a>

* [概览](data-transforms/data-transforms.md)
* [滚动密钥与旋转密码](data-transforms/rolling-and-rotation.md)
* [LFSR、字符串与页变换](data-transforms/lfsr-strings-pages.md)
* [校验和与密钥推进](data-transforms/checksums.md)
* [AES-CBC 层](data-transforms/aes.md)
* [Huffman 与 LZ 压缩](data-transforms/compression.md)
* [按构建定制的字节变换](data-transforms/bytecode-transform.md)

## 加载与 PE 修复 <a href="#loading-and-pe-repair" id="loading-and-pe-repair"></a>

* [加载与节恢复](loading-and-pe-repair/loading/README.md)
  * [阶段链与标记布局](loading-and-pe-repair/loading/stage-chain.md)
  * [PE32、DLL 与无标记布局](loading-and-pe-repair/loading/layout-variants.md)
  * [结构发现与验证](loading-and-pe-repair/loading/discovery-validation.md)
* [PE 重建](loading-and-pe-repair/pe-reconstruction/README.md)
  * [头、节与零填充范围](loading-and-pe-repair/pe-reconstruction/memory-image.md)
  * [导入、TLS 与导出](loading-and-pe-repair/pe-reconstruction/imports-tls-exports.md)
  * [重定位、页变换与 CLR 数据](loading-and-pe-repair/pe-reconstruction/relocations-managed.md)

## 运行时 <a href="#runtime" id="runtime"></a>

* [概览](runtime/runtime.md)
* [启动序列与状态报告](runtime/startup-status.md)
* [环境与反分析检查](runtime/environment-checks.md)
* [页保护与加载器代码](runtime/page-protection.md)
* [手动映射辅助模块](runtime/mapped-modules.md)
* [Htsysm 内核组件](runtime/kernel-components.md)

## 分析 <a href="#analysis" id="analysis"></a>

* [概览](analysis/analysis.md)
* [分析流程](analysis/workflow.md)
* [已观察到的局限](analysis/observed-limitations.md)
* [il2cpp 元数据混淆](analysis/il2cpp-metadata.md)
* [常量与偏移](analysis/constants.md)
