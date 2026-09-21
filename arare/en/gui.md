---
description: "WPF front-end that builds arare protect command lines from a job list."
---

# GUI

WPF front-end for the Arare CLI. It builds `arare protect` invocations from a job list, shows the exact command before running it, and executes jobs sequentially with optional post-protect verification.

Building requires the .NET 10 SDK, the same SDK used by the managed tools. Packaged GUI binaries require the .NET 10 Desktop Runtime for the package architecture. The native CLI doesn't need .NET unless it packs managed inputs.

```powershell
dotnet build gui/ArareGui.slnx -c Release
dotnet run --project gui/Arare.Gui
```

Keep `Arare.Gui.exe` beside `arare.exe`. The GUI looks for `arare.exe` beside itself, then on `PATH`. If detection fails, select **Locate…** in the status bar to choose a different location.

Positional command-line arguments pre-add files and folders:

```powershell
Arare.Gui.exe app.exe game_folder\
```

With subfolder scanning disabled, the folder picker scans the root and recursively scans any `Managed` or `Plugins` directories found up to three levels deep. Enabling subfolder scanning includes the whole selected tree.

## Behavior

- Each job row owns its protection profile. The suggested profile comes from the PE: x86 maps to `pe32`, x64 to `pe64-modern`, AnyCPU managed images to `pe32`. `legacy-dll` is only a valid choice for 64-bit DLLs.
- Output defaults to `.\arare-protected\` next to each input, or one chosen output folder with filenames preserved.
- Jobs with duplicate output paths or outputs that overlap any queued input are rejected. This includes companion files and applies even with **Replace existing outputs** enabled. Use separate output folders for inputs that share a filename.
- Environment checks, page encryption, and scribble follow the CLI's per module-type defaults, including the CLI's rule that `disk-integrity` replaces `clean-code`. The checkbox shows the resolved state for the selected row; overriding an option marks it and offers a reset.
- The command preview shows the selected CLI path and protection arguments. **Copy as .ps1** exports PowerShell commands with literal arguments, creates output directories, includes the selected post-protect verification, and stops on a nonzero CLI exit code.
- **Protect** runs jobs sequentially. **Cancel** lets the current protection and optional verification finish, then stops the remaining jobs. Closing during a run asks for confirmation and waits for that file to finish.
- With **Check encoding after protect** enabled, each output is checked with `arare verify`. That decoder check doesn't launch the program.
- Settings live in `Arare.Gui.settings.json` next to the executable. The job list is not persisted.

## Tests

```powershell
dotnet run --project gui/Arare.Gui.SmokeTests
```

Covers PE classification, command construction, the override/default model, preview generation, validation, the protect/verify flow against a fake backend, the close-during-run handshake, folder scanning rules, and settings persistence.

AGPL-3.0-only, matching the CLI.
