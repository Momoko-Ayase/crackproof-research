---
description: "WPF front-end that builds arare protect command lines from a job list."
---

# GUI

WPF front-end for the Arare CLI. It builds `arare protect` invocations from a job list, shows the exact command before running it, and executes jobs sequentially with optional post-protect verification.

Requires the .NET 10 SDK, the same SDK used by the managed tools.

```powershell
dotnet build gui/ArareGui.slnx -c Release
dotnet run --project gui/Arare.Gui
```

Keep `Arare.Gui.exe` beside `arare.exe`. The GUI looks for `arare.exe` beside itself, then on `PATH`. A different location can be picked from the status bar.

Positional command-line arguments pre-add files and folders:

```powershell
Arare.Gui.exe app.exe game_folder\
```

Folders are scanned as the folder picker does: the root plus any `Managed` or `Plugins` directories up to three levels deep.

## Behavior

- Each job row owns its protection profile. The suggested profile comes from the PE: x86 maps to `pe32`, x64 to `pe64-modern`, AnyCPU managed images to `pe32`. `legacy-dll` is only a valid choice for 64-bit DLLs.
- Output defaults to `.\arare-protected\` next to each input, or one chosen output folder with filenames preserved.
- Environment checks, page encryption, and scribble follow the CLI's per module-type defaults, including the CLI's rule that `disk-integrity` replaces `clean-code`. The checkbox shows the resolved state for the selected row; overriding an option marks it and offers a reset.
- The command preview always reflects exactly what will run. It virtualizes, so a folder of thousands of files stays responsive.
- Protect runs jobs sequentially and can be cancelled between files. With Check encoding after protect enabled, each output is checked with `arare verify`. That decoder check does not launch the program.
- Settings live in `Arare.Gui.settings.json` next to the executable. The job list is not persisted.

## Tests

```powershell
dotnet run --project gui/Arare.Gui.SmokeTests
```

Covers PE classification, command construction, the override/default model, preview generation, validation, the protect/verify flow against a fake backend, the close-during-run handshake, folder scanning rules, and settings persistence.

AGPL-3.0-only, matching the CLI.
