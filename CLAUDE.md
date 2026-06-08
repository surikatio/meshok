# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Desktop automation tool for posting auction lots on [meshok.net](https://meshok.net) via their REST API. The user fills in lot parameters, selects image URLs from an Excel file, and the app posts one lot per image with a configurable delay between them.

Entry point is `main.py`. All settings (accounts, delivery prices, Excel filename) are configured inside the app UI — no config file needed.

## Running the App

```powershell
python main.py

# Install dependencies
pip install requests openpyxl flet

# Run tests
python -m pytest tests/ -v

# Build standalone exe (no Flutter required)
.venv\Scripts\flet pack main.py --name "Avto-lot" --icon icon.ico --product-name "Авто-лот" --distpath dist
```

после завершения запуска закрывать программу

All data paths (`шаблоны/`, `история/`, `settings.json`, `log.txt`, Excel file) are resolved relative to the exe directory (when frozen) or project root (when running from source) via `core/paths.py`.

## Project Structure

```
main.py                  # Flet entry point, logging setup
core/
    paths.py             # get_app_dir() — resolves base dir for exe vs source
    settings.py          # AppSettings dataclass, save/load to settings.json
    templates.py         # LotData dataclass + CRUD for шаблоны/
    excel_loader.py      # load_url_list() — non-blocking Excel read
    validator.py         # validate_lot_data() → list[str] of errors
    history.py           # save_history() → история/
    api.py               # make_lot() — POST to meshok.net API
    meshok_api.py        # MeshokAPI class (vendored from meshokteam/sAPI-py)
ui/
    lot_form.py          # LotFormView — main form screen
    progress_view.py     # ProgressView — posting loop + live log + stop button
    settings_view.py     # SettingsView — accounts, Excel file, delivery prices
    template_dialog.py   # show_save_template_dialog()
tests/
    conftest.py          # app_dirs fixture: patches module-level path constants
    test_api.py
    test_excel_loader.py
    test_history.py
    test_settings.py
    test_templates.py
    test_validator.py
dist/
    Avto-lot.exe         # built exe (not in git)
main.pyz                 # legacy tkinter app, kept for reference
```

## Architecture

| Layer | What it does |
|---|---|
| Startup | `load_settings()` → passes `AppSettings` through all views |
| UI (LotFormView) | Form fields, template menu, settings gear, Excel status + refresh |
| Settings (SettingsView) | Add/delete accounts (name→token), Excel filename, delivery prices |
| Validation | `validate_lot_data()` checks all fields before posting |
| API (`make_lot()`) | `MeshokAPI(token).listItem(params)` → POST to meshok |
| Loop (ProgressView) | Iterates url_list, posts one lot per row, stop button, ok/err counter |

## Settings

Stored in `settings.json` (next to exe, excluded from git — contains Bearer tokens):

```json
{
  "accounts": {"Имя": "bearer_token"},
  "table_name": "ссылки на картинки.xlsx",
  "prolong": "0",
  "local_delivery_price": "100",
  "country_delivery_price": "100",
  "world_delivery_price": "500"
}
```

Account selection: user picks a name in the form dropdown → `accounts[name]` → Bearer token for API.

## Template Format

Templates are stored as single-line `;`-separated `.txt` files in `шаблоны/`:

```
name;category_id;tags;description;price;date;sleep_time;longevity[;autoprod[;account]]
```

- `date`: `YYYY-MM-DD HH:MM:SS` or `0` for "now" (replaced with `datetime.now()` at run time)
- `longevity`: one of `3, 5, 7, 10, 14, 21` (days)
- `autoprod`: `0`=N, `1`=Y (maps to meshok `antisniper` param)
- `account`: display name key from settings accounts dict
- `шаблоны/last.txt` — auto-saved on every run, loaded as default on next launch

History saves to `история/{name}-{timestamp}.txt` on each run (before posting starts).

## meshok.net API

- Library: `core/meshok_api.py` — vendored from [meshokteam/sAPI-py](https://github.com/meshokteam/sAPI-py)
- Endpoint: `POST https://api.meshok.net/sAPIv1/listItem`
- Auth: `Authorization: Bearer {token}`
- Hardcoded params: `city=58`, `saleType=Auction`, `delivery=WORLD`, `payment=BANK,CARD,PAYPAL`, `condition=NA`
- `pictures` — comma-separated URLs string; one Excel row = one lot, each column = one photo URL
  - Row with 3 columns → 1 lot with 3 photos; row with 1 column → 1 lot with 1 photo
- Tags: spaces stripped around commas only, not inside tag words
- Successful response: `{'success': 1, 'result': {'id': '...', 'endDateTime': '...'}, 'cost': 10, 'balance': ...}`
- Error code `-2` in response = image URL rejected (hotlinking blocked)

## Posting Loop (ProgressView)

- First lot posted at the time specified in the form; each subsequent lot shifted by `sleep_time` seconds
- Fixed 1-second sleep between API requests (rate-limit protection, independent of `sleep_time`)
- Stop button sets `self._stop = True`, loop exits after current lot finishes
- Final message shows count of successful vs failed lots

## Building exe

```powershell
.venv\Scripts\flet pack main.py --name "Avto-lot" --icon icon.ico --product-name "Авто-лот" --distpath dist
```

Result: `dist\Avto-lot.exe` (~61 MB, standalone, no Python required).
User needs to place the Excel file next to the exe. `шаблоны/`, `история/`, `settings.json`, `log.txt` are created automatically next to the exe on first run.

## Logging

- Written to `log.txt` next to exe (and to stderr when running from source)
- Configured in `main.py` with both `FileHandler` and `StreamHandler`

## Known Issues

- **Image error -2** — postimg.cc blocks hotlinking; need alternative image hosting or direct upload

## Flet Version Notes

- Flet 0.85.2 — use `ft.run()` not deprecated `ft.app()`
- `FilePicker` in this version cannot be passed `on_result` in constructor — set as attribute after construction (currently not used)
- Do not call `page.update()` inside `View.__init__()` before the view is appended to `page.views`
- All background thread UI updates via `self._pg.update()` are safe after mounting

## Git Workflow

- After modifying any file — commit and push to GitHub (`git push origin main`)
- After reverting any file — also revert the corresponding commit on GitHub (`git revert` or `git push --force` only if explicitly requested)

## Allowed Tools
- Bash(gh:*)
- Bash(gh issue:*)
- Bash(gh pr:*)
- Bash(gh repo:*)
