---
description: "Locate the 00 01 0e 00 schedule marker, recover the AES-256 key, and read header and container seeds."
icon: sliders
---

# Module configuration

Container decoding uses a configuration block (`Module9bConfig`) located via the four-byte schedule marker `00 01 0e 00` (little-endian flags `0x0100`, AES-256 round count `14`). A decoder module must contain this marker exactly once; the module is rejected if the marker is missing or duplicated, `schedule_size` is outside `{0, 0xF4}`, or the round-key array is truncated.

## Full vs embedded layout

{% tabs %}
{% tab title="Full module (0x9B and 0xE3..0xE8)" %}
Interpreter modules `0xE3`..`0xE8` and restoration module `0x9B` carry the complete layout around `marker`:

| Offset from `marker` | Size | Field | Role |
| --- | --- | --- | --- |
| `-0x08` | 4 | `header_seed` | Decrypts the `0x5C`-byte `0x9D` `ProtectedDescriptor` |
| `-0x04` | 4 | `schedule_size` | `0xF4` when the schedule is populated (or `0`) |
| `+0x00` | 4 | `marker` | `00 01 0e 00` (`0x0100`, 14 rounds) |
| `+0x04` | `0xF0` | `round_keys[0..14]` | 15 × 16-byte AES-256 decryption round keys (each 32-bit word byte-reversed) |
| `+0x100` | 4 | `container_seed` | Seeds both `ContainerHeader` decoding and the per-segment rolling word cipher |
| `+0x240` | 4 | `skip_aes` | Non-zero disables the AES-256-CBC pass for all containers decoded with this config |
{% endtab %}

{% tab title="Embedded Stage 2 decoder (0xE2)" %}
The shorter decoder embedded inside the root Stage 2 image (`0xE2`) ends before `+0x100` and `+0x240`:

| Offset from `marker` | Size | Field | Role |
| --- | --- | --- | --- |
| `-0x08` | 4 | `container_seed` | Used directly as the container header and segment-cipher seed |
| `-0x04` | 4 | `schedule_size` | `0xF4` (or `0`) |
| `+0x00` | 4 | `marker` | `00 01 0e 00` |
| `+0x04` | `0xF0` | `round_keys[0..14]` | 15 × 16-byte byte-reversed decryption round keys |

Because `+0x240` is absent in this truncated layout, `skip_aes` defaults to `false` (individual container headers can still set their own per-container AES skip byte).
{% endtab %}
{% endtabs %}

## AES-256 key recovery

The 15 round keys at `marker + 0x04` are stored in AES decryption order with every 4-byte word byte-reversed. Reversing each word restores standard round-key byte order, and the original 32-byte AES-256 encryption key is reconstructed from the last two round keys:

```text
aes256_key = round_keys[14] || MixColumns(round_keys[13])
```

`MixColumns` inverts the `InvMixColumns` transform applied to interior decryption round keys in the Equivalent Inverse Cipher schedule.
