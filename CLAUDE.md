# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Desktop automation tool for posting auction lots on [meshok.net](https://meshok.net) via their REST API. The user fills in lot parameters, selects image URLs from an Excel file, and the app posts one lot per image with a configurable delay between them.

**Migration complete**: tkinter → [Flet](https://flet.dev). Entry point is `main.py`.

## Running the App

```powershell
# New Flet app (Sprint 1):
python main.py

# Legacy tkinter app (reference only):
python main.pyz

# Install dependencies
pip install requests openpyxl flet
```
после завершения запуска закрывать программу

The app must be launched from its own directory — it uses relative paths for `шаблоны/`, `история/`, `icon.ico`, and the Excel file.

## Project Structure (post Sprint 1)

```
main.py                  # Flet entry point
core/
    templates.py         # LotData dataclass + CRUD for шаблоны/
    excel_loader.py      # load_url_list() — non-blocking Excel read
    validator.py         # validate_lot_data() → list[str] of errors
    history.py           # save_history() → история/
    api.py               # make_lot() — POST to meshok.net API
ui/
    lot_form.py          # LotFormView — main form screen
    progress_view.py     # ProgressView — posting loop + live log
    template_dialog.py   # show_save_template_dialog()
auto_lot_сonfig.py       # config (note: кириллическая 'с' in filename — intentional)
main.pyz                 # legacy tkinter app, kept for reference
```

## Architecture

**Single-file app** (`main.pyz`) with a flat structure:

| Layer | What it does |
|---|---|
| Startup | Loads Excel → builds `url_list` of image URLs |
| UI (`start()`) | Renders the form, loads last template, wires menu |
| Validation (`clicked_save()`) | Validates all fields before posting |
| API (`make_lot()`) | POSTs to `https://api.meshok.net/sAPIv1/listItem` |
| Loop | Iterates `url_list`, calls `make_lot()` once per image with `sleep_time` delay |

**Config** (`auto_lot_config.py`):
- `accounts` — dict of display name → Bearer token
- `table_name` — Excel filename with image URLs (column A)
- `prolong` — auto-renewal count on failed auction
- `localDeliveryPrice`, `countryDeliveryPrice`, `worldDeliveryPrice`

## Template Format

Templates are stored as single-line `;`-separated `.txt` files in `шаблоны/`:

```
name;category_id;tags;description;price;date;sleep_time;longevity[;autoprod[;account]]
```

- `date`: `YYYY-MM-DD HH:MM:SS` or `0` for "now"
- `longevity`: one of `3, 5, 7, 10, 14, 21` (days)
- `autoprod`: `0`=N, `1`=Y (maps to meshok `antisniper` param)
- `account`: display name key from `accounts` dict
- `шаблоны/last.txt` — auto-saved on every run (used as default on next launch)

History saves to `история/{name}-{timestamp}.txt` on each run.

## meshok.net API

- Endpoint: `POST https://api.meshok.net/sAPIv1/listItem`
- Auth: `Authorization: Bearer {token}` (token = account value from config)
- Hardcoded params: `city=58`, `saleType=Auction`, `delivery=WORLD`, `payment=BANK,CARD,PAYPAL`, `condition=NA`
- `pictures` param takes comma-separated URLs — multiple images per lot supported
- Excel format: one row = one lot, each column = one image URL; empty cells ignored
- Error code `-2` in response means the image URL was rejected (hotlinking blocked on postimg.cc)

## Known Issues to Fix

1. **Image error -2** — postimg.cc blocks hotlinking; need alternative image hosting or direct upload (not fixed in Sprint 1)
2. ~~Template menu hardcoded to 20 items~~ — **fixed**: `list_templates()` is fully dynamic
3. ~~`stdout` redirected to `log.txt`~~ — **fixed**: uses `logging` module, no stdout redirect
4. ~~`exit(0)` after posting~~ — **fixed**: `ProgressView` navigates back to form on completion
5. ~~Excel loaded at module level~~ — **fixed**: `load_url_list()` called in background thread

## Flet Migration Notes

When migrating to Flet:
- Replace `tkinter.Tk()` → `ft.app(target=main)`
- Replace `Entry/Label/Button` → `ft.TextField/ft.Text/ft.ElevatedButton`
- Replace `Combobox` → `ft.Dropdown`
- Replace `Progressbar` → `ft.ProgressBar`
- Replace `messagebox` → `ft.AlertDialog`
- The posting loop blocks the UI thread — wrap in `asyncio` or run in a thread with `page.update()` calls
- `pyperclip` paste buttons can be replaced with Flet's built-in clipboard access

## Allowed Tools
- Bash(gh:*)
- Bash(gh issue:*)
- Bash(gh pr:*)
- Bash(gh repo:*)

