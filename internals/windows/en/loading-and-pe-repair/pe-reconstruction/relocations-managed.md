---
description: "Relocation policy, the final page transform, and the special handling required for managed images."
---

# Relocations, page transforms, and CLR data

## Relocations and the /FIXED split

Builds differ deliberately in whether the result may be rebased:

- **Older single-file EXE builds are `/FIXED`.** The shell discards the base-relocation table and clears `DllCharacteristics`; the image can only load at its preferred base. A faithful reconstruction mirrors this: `DataDirectory[5]` zeroed, `DllCharacteristics` zeroed.
- **DLLs (any layout) must stay relocatable.** A DLL is almost always mapped away from its preferred base; stripping its relocations makes it unloadable. Reconstruction keeps `DataDirectory[5]` and ensures `IMAGE_DLLCHARACTERISTICS_DYNAMIC_BASE` (`0x0040`) is set.
- **Marker-less and companion builds aren't `/FIXED`.** They carry real ASLR flags and a valid relocation table, and any rebase must relocate everything, including the restored TLS directory's pointers, which is why those relocations are appended during TLS restoration. The 32-bit family meets the same requirement differently: its DLLs keep the four TLS-field entries as neutralized `ABSOLUTE` slots that are re-armed to `HIGHLOW`, not appended (see [Imports, TLS, and exports](imports-tls-exports.md#tls-is-stripped-and-reinstalled-at-runtime)).

## The code-page scramble, ordered last

The [per-page scramble](../../data-transforms/lfsr-strings-pages.md#the-per-page-code-scramble) applies to `.text` after section recovery. Ordering constraints observed across families:

- **Marker layout:** scramble runs before the entry-point/data-directory restoration.
- **Marker-less layout:** scramble is deferred until after import-name decryption and is re-selected over the final bytes, and only runs when the entry point falls inside `.text`. Managed images restore their CLR metadata **after** the scramble, because the metadata region lives inside `.text` but isn't scrambled code: scrambling it would corrupt roughly one byte per 16 and produce an invalid COR20 signature.
- **32-bit:** the scramble is skipped entirely when the section is already plaintext (native DLLs), detected by comparing the `0xCC`-restoration score against the no-scramble baseline.

## CLR metadata and method bodies require different handling

Some managed layouts preserve the COR20 header (`cb == 0x48`), the BSJB metadata stream, and CLR resources verbatim in the protected file at their RVA-mapped file offsets. These ranges can be copied back after section recovery. In marker-less layouts they are restored after the page transform, because they may occupy addresses inside `.text` without being transformed code.

Managed **companion** DLLs keep these structures in the loader stub rather than the protected payload. The restore set is the COR20 header plus every non-empty range it references: the BSJB metadata (required), resources, the strong-name signature, the code-manager table, vtable fixups together with the slot arrays they name, the export-address jump table, and the managed native header. Method bodies are never part of the overlay; they come from the decrypted companion.

The preserved metadata does **not** include a plaintext copy of every IL method body. Method bodies reside in PE sections and remain subject to the section-data and page transforms used by that build. Filling an entire section from the protected file can therefore overwrite correctly recovered methods with transformed bytes. Restore the section contents first, then replace only the independently verified CLR ranges, never a whole section from the protected file or the stub.

If the recovered COR20 directory points to a header whose `cb` is zero and no valid preserved header is available, clear the directory. Passing an empty header to the CLR startup path produces a failure that can be mistaken for bad section recovery. Mixed-mode images also need their native-entrypoint flag preserved; a pure managed image can be identified separately from that case.

Unity il2cpp titles add a separate obfuscation outside the PE: method tokens inside `global-metadata.dat`. See [il2cpp metadata obfuscation](../../analysis/il2cpp-metadata.md).
