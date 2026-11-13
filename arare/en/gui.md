---
description: "WPF desktop front-end for building, previewing, and running batch arare protect and verify jobs."
icon: window-maximize
---

# GUI

`Arare.Gui.exe` is a Windows Presentation Foundation (WPF) front-end that builds `arare protect` command lines from a job queue, previews the exact CLI invocation, and runs sequential protection with optional post-protect decoding checks.

## Building and launching

Building requires the .NET 10 SDK; running a packaged GUI build requires the matching .NET 10 Desktop Runtime.

```powershell
dotnet build gui/ArareGui.slnx -c Release
dotnet run --project gui/Arare.Gui -c Release
```

Place `Arare.Gui.exe` in the same folder as `arare.exe` (or keep `arare.exe` on `PATH`), or select **Locate…** in the status bar to pick another binary. Startup arguments can pre-populate files and folders:

```powershell
Arare.Gui.exe app.exe game_folder\
```

* **Folder picker:** with subfolder recursion off, scans the selected folder plus any `Managed` or `Plugins` subdirectories up to three levels deep; enabling subfolder recursion walks the entire tree.
* **Positional folder arguments:** always use the non-recursive scan (`root` plus `Managed`/`Plugins` up to depth 3) regardless of the saved subfolder checkbox.

## Queue, overrides, and verification

* **Per-row profiles:** suggested automatically from the PE header (`x86` -> `pe32`, `x64` -> `pe64-modern`, `AnyCPU` managed -> `pe32`; `legacy-dll` is restricted to 64-bit DLLs).
* **Output paths and collision checks:** output defaults to `.\arare-protected\` beside each input (or a single chosen folder). Duplicate output paths or any output (including `._` companions) that would overwrite a queued input are blocked before execution, even when **Replace existing outputs** is checked.
* **Resolved option state:** checkboxes for environment checks, page encryption, scribble, and the **ErrLog** mailslot report (`--errlog`) display the effective default for the selected module kind (including `disk-integrity` superseding `clean-code`), mark per-row overrides, and provide a one-click reset. `--antidebug-av` is not exposed in the GUI and follows the CLI's per-module default (`on` for EXEs, `off` for DLLs).
* **Script export and execution:** **Copy as .ps1** exports literal PowerShell invocations that create output directories, run `arare protect` (plus optional `arare verify`), and stop on non-zero exit codes. **Protect 1 file** / **Protect N files** runs the queue sequentially; **Cancel** finishes the active item before stopping.
* **Standalone verification:** **Verify existing…** runs `arare verify` across candidate profiles for an already-protected file without launching it; enabling **Check encoding after protect** runs `arare verify` automatically after each job.
* **Persistence:** UI preferences are saved to `Arare.Gui.settings.json` beside the executable; the job queue itself is session-only.

## Smoke tests

```powershell
dotnet run --project gui/Arare.Gui.SmokeTests -c Release
```

The suite exercises PE classification, CLI argument generation, per-module default/override resolution, `.ps1` script generation, path-collision validation, protect/verify state transitions against a mock backend, close-during-run confirmation, folder-scanning depth rules, and settings persistence. Licensed under `AGPL-3.0-only`.
