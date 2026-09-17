---
description: >-
  Independent technical research into CrackProof protection formats and runtime
  behavior.
layout:
  width: wide
  title:
    visible: true
  description:
    visible: true
  tableOfContents:
    visible: false
  outline:
    visible: false
  pagination:
    visible: false
  metadata:
    visible: false
  tags:
    visible: true
  actions:
    visible: false
---

# CrackProof Research

CrackProof® is a family of commercial binary-protection systems from HyperTech. This site records independently verified details of its file formats, data transforms, loaders, and runtime components.

The research currently covers Windows PE files and Android native libraries. Each platform has its own container format and restoration path, so their internals are documented separately.

<table data-view="cards"><thead><tr><th></th><th></th><th data-hidden data-card-target data-type="content-ref"></th></tr></thead><tbody><tr><td><strong>Windows internals</strong></td><td>Protected PE layout, transforms, staged loading, PE reconstruction, and runtime behavior.</td><td><a href="https://app.gitbook.com/s/PuKTEy2soDgSB3qfWACy/">CrackProof for Windows internals</a></td></tr><tr><td><strong>Android SO internals</strong></td><td>Protected AArch64 ELF layout, module streams, container decoding, ELF restoration, and IL2CPP metadata.</td><td><a href="https://app.gitbook.com/s/fcBZibCo72OSh5jVcKoo/">CrackProof for Android SO internals</a></td></tr><tr><td><strong>Verification &#x26; reference</strong></td><td>Executable test vectors and small reference implementations for the documented Windows transforms.</td><td><a href="https://app.gitbook.com/s/8S0xnfw9UP9A2yylicaA/">Verification &#x26; reference</a></td></tr><tr><td><strong>Senbei</strong></td><td>The project's own static unpacker for protected Windows PE files and Android shared libraries: usage, design, and development.</td><td><a href="https://app.gitbook.com/s/ul1YGOqMPNVceXYP7FFj/">Senbei</a></td></tr><tr><td><strong>Arare</strong></td><td>The project's own source-built Windows PE protector: usage, GUI, support, design, and development.</td><td><a href="https://app.gitbook.com/s/ePWLVFU0kRqnVPWx6nxD/">Arare</a></td></tr></tbody></table>

## Research boundaries

The pages describe observable structures and behavior. Names are taken from binaries, logs, established platform terminology, or a literal description of what a field does. A claim counts as format behavior only when more than one sample shows it, or when an internal consistency rule supports it.

Protected product names, deployment-specific driver names, and identifying sample details are omitted. The research pages don't name the implementation projects used to verify them; the Senbei and Arare sections separately document the project's own tools.

## Legal notice

Use this information only with binaries you own or are explicitly authorized to analyze. Laws and license terms governing circumvention vary by jurisdiction. This independent publication contains no vendor source code or keys, is not affiliated with HyperTech, and does not authorize redistribution of restored binaries.
