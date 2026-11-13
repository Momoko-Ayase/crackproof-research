---
description: "Independent technical research into CrackProof protection formats and runtime behavior."
icon: house
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

CrackProof® is a family of commercial binary-protection systems from HyperTech. This site documents independently verified details of its file formats, data transforms, staged loaders, and runtime components.

The research covers Windows PE files and Android AArch64 shared libraries. Each platform uses a distinct container format and restoration pipeline, so their internals are documented in separate sections.

<table data-view="cards"><thead><tr><th width="48"></th><th></th><th></th><th data-hidden data-card-target data-type="content-ref"></th></tr></thead><tbody><tr><td><i class="fa-desktop"></i></td><td><strong>Windows internals</strong></td><td>Protected PE layout, ciphers, staged loading, PE reconstruction, and runtime checks.</td><td><a href="https://app.gitbook.com/s/PuKTEy2soDgSB3qfWACy/">CrackProof for Windows internals</a></td></tr><tr><td><i class="fa-mobile-screen-button"></i></td><td><strong>Android SO internals</strong></td><td>Protected AArch64 ELF layout, nested module streams, container decoding, ELF restoration, and IL2CPP metadata.</td><td><a href="https://app.gitbook.com/s/fcBZibCo72OSh5jVcKoo/">CrackProof for Android SO internals</a></td></tr><tr><td><i class="fa-code"></i></td><td><strong>Verification &amp; reference</strong></td><td>Executable test vectors, runnable Python implementations, and anonymized debug logs for the Windows transforms.</td><td><a href="https://app.gitbook.com/s/8S0xnfw9UP9A2yylicaA/">Verification &amp; reference</a></td></tr><tr><td><i class="fa-screwdriver-wrench"></i></td><td><strong>Senbei</strong></td><td>Static unpacker for protected Windows PE files, Android shared libraries, and IL2CPP metadata: CLI, desktop GUI, design, and development.</td><td><a href="https://app.gitbook.com/s/ul1YGOqMPNVceXYP7FFj/">Senbei</a></td></tr><tr><td><i class="fa-shield-halved"></i></td><td><strong>Arare</strong></td><td>Source-built Windows PE protector reproducing observed layout families: CLI, GUI, support matrix, design, and development.</td><td><a href="https://app.gitbook.com/s/ePWLVFU0kRqnVPWx6nxD/">Arare</a></td></tr></tbody></table>

## Research scope

Every documented rule comes from observable binary structures and runtime behavior. Field and component names follow strings in the binaries, debug log output, standard platform specifications, or literal descriptions of what the bytes do. A behavior is generalized as part of the format when multiple samples share it or when an internal consistency check enforces it.

Protected product names, deployment-specific driver filenames, and sample-identifying paths are omitted throughout the research sections. Senbei and Arare are documented separately in their own product sections.

{% hint style="warning" %}
**Legal notice.** Use this material only with binaries you own or are explicitly authorized to analyze. Laws and license agreements governing circumvention of technological protection measures vary by jurisdiction. This independent publication contains no vendor source code or keys, has no affiliation with HyperTech, and does not authorize redistributing restored binaries.
{% endhint %}
