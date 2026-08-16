---
description: "How protected Windows files are laid out, recognized, and divided between a stub and optional companion data."
---

# Protected file structure

The Windows format keeps a valid PE-facing outer image but places the original image and loader data in a separate address-oriented container. The first step in analysis is to distinguish that container from ordinary overlay data and to identify which layout family is present.

| Topic | What it establishes |
|---|---|
| [Container and encrypted header](container-layout.md) | The large offset ranges, the eight-dword `info` table, and its key derivation |
| [Recognition and build families](recognition.md) | Evidence used to classify PE32, PE32+, EXE, DLL, native, and CLR cases |
| [Section data and companion files](companion-layout.md) | How section records map into the payload and how external `._` data is joined to a stub |
