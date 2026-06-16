# EZProxy Stanza Sync

Monitors updates to EZproxy stanza files published on the OCUL website, scoped to the stanzas actively used by Lakehead University Library.

OCUL maintains over 1,000 EZproxy stanzas; this tool tracks only the subset in use, improving efficiency and avoiding unnecessary load on the OCUL site.

---

## Setup

### 1. Install uv

Install [uv](https://github.com/astral-sh/uv) (Python environment manager), then restart your terminal.

### 2. Set up the Python environment

```bash
git clone https://github.com/lu-library/ezproxy-stanza-sync
cd ezproxy-stanza-sync
uv sync
```

`uv sync` will install Python 3.10 (if not already present), create a virtual environment, and install all required packages.

### 3. (Optional) Enable email notifications

Email notifications are disabled by default. To enable them, uncomment the `update_email` and `error_email` calls in `src/main.py` and `src/update_stanza.py`.

Then configure credentials via environment variables:

```bash
# Add to ~/.bashrc or ~/.profile
export EMAIL_SENDER="your_email@gmail.com"
export EMAIL_RECEIVER="receiver_email@gmail.com"
export EMAIL_PASSWORD="your_app_password"

source ~/.bashrc
```

> A Gmail App Password can be generated after enabling 2-step verification on your Google account.

### 4. Run the tool

**Option A — Terminal (CLI):**

```bash
cd /path/to/ezproxy-stanza-sync
uv run -m src.cli stanza sync
```

**Option B — GUI (packaged app):**

Build the application:

```bash
pyinstaller --onedir --windowed --name EZproxy-Config gui-import.py
```

After building:

- **macOS:** Place the `/data` folder in the same directory as `EZproxy-Config.app`.
- **Windows:** Place the `/data` folder in the same directory as `EZproxy-Config.exe`.

Once the `/data` folder is in place, the entire `EZproxy-Config` folder can be moved anywhere and run without path adjustments.

### 5. (Optional) Schedule with cron

```bash
crontab -e
```

Example — run every Monday at 2 AM:

```
0 2 * * 1 cd /path/to/ezproxy-stanza-sync && uv run -m src.main >> logs/stanza.log 2>&1
```

---

## GUI Reference

### First-time setup

| Button | When to use |
|--------|-------------|
| **LoadDB** | Run once at the start — loads stanza info from `config.txt` into the database. Skip if a database already exists. |

### Ongoing maintenance

| Button | When to use |
|--------|-------------|
| **Sync** | Run weekly — checks for OCLC updates from the past month, with retry logic. |
| **Audit** | Run if more than a month has passed since the last sync — performs a full historical check going back to 2006. |
| **Pack** | Run when a backup is needed — zips `config.txt` and `/stanzas` into `ez-config-DATE.zip`. |
| **Check** | Run occasionally — verifies that `IncludeFile` entries in `config.txt` match the database. |

### Adding a new stanza

1. Click **Add Stanza** to add the stanza entry to the database.
2. Manually create a `.txt` file for the new stanza and place it under `/data/stanzas/`.
3. Click **Render** to regenerate `config.txt` with the new stanza included.

> **Render** can also be run on its own at any time, but it is primarily useful after adding one or more stanzas.

---

## CLI Reference

| Command | Description |
|---------|-------------|
| `uv run -m src.cli stanza sync` | Check for recent OCLC updates (weekly task) |
| `uv run -m src.cli stanza audit` | Full historical update check |
| `uv run -m src.cli stanza render` | Regenerate `config.txt` from the Jinja2 template and database |
| `uv run -m src.cli stanza loaddb` | Populate `stanzas.db` from `config.txt` |
| `uv run -m src.cli stanza check` | Verify `IncludeFile` entries in `config.txt` match the database |
| `uv run -m src.cli pack` | Zip `config.txt` and `/stanzas` into a dated archive |

---

## Project Structure

### `data/` (git-ignored)

| Path | Description |
|------|-------------|
| `stanzas.db` | SQLite database storing stanza metadata |
| `stanzas/` | EZproxy stanza `.txt` files currently in use |
| `config/` | `config.txt`, timestamped backups, and Jinja2 templates (`config.tpl`, `header.tpl`, `footer.tpl`, `alumni.tpl`) |
| `diff/` | Diff files showing differences between local and OCUL versions of updated stanzas |
| `log/` | Log files from sync and audit runs |

### `src/`

**Core functions**

| File | Description |
|------|-------------|
| `update_stanza.py` | Checks all stanzas in the database against the OCUL website for updates after a given date (defaults to today). Intended for manual or infrequent use — e.g., initial deployment or after a long gap between checks. |
| `most_recent_update_stanza.py` | Monitors only the "Recently updated database stanzas" section on the OCUL website. Faster and lighter than a full scan. **Recommended for regular weekly runs.** |

**Built-in utilities**

| File | Description |
|------|-------------|
| `diff_stanza.py` | Compares local stanza versions against updated OCUL versions and saves `.diff` files to `/data/diff/`. |
| `send_email.py` | Handles email notifications. Credentials are read from environment variables; requires a Gmail App Password. |
| `generate_config.py` | Generates `config.txt` from scratch using Jinja2 templates and database content. |
| `update_config_file.py` | Updates the comment header for each stanza entry in `config.txt` (e.g., updates `# Knovel - last update 2021-05-21` to reflect the current date). |
| `organize_config_file.py` | Sorts `IncludeFile` entries in `config.txt` alphabetically by filename, independently within the Custom Stanzas and OCLC sections. |
| `zippack.py` | Packages the current `config.txt` and stanza files into a `.zip` archive for backup or transfer. |

**Configuration and infrastructure**

| File | Description |
|------|-------------|
| `main.py` | Primary entry point for scheduled runs. Executes the most-recent update check with retry logic. |
| `cli.py` | Maps CLI subcommands to their corresponding functions. |
| `config.py` | Centralized path and URL configuration (project directories, data paths, OCUL URLs). |
| `logging_config.py` | Initializes Loguru logging — sets log file location, rotation policy, and log level. |
| `db.py` | Database connection and all database-related functions (queries, rendering, adding stanzas, etc.). |
| `gui-import.py` | GUI built by importing functions directly. Supports packaging with PyInstaller and can be run from any location. **Use this for deployment.** |
| `gui-cli.py` | Earlier GUI implementation that invoked CLI subprocesses. Packaged apps generated from this file cannot be moved to a different directory. Retained for reference only — use `gui-import.py` instead. |

---

## Scope and Limitations

- Only tracks stanzas that exist on the OCUL website. Custom stanzas created specifically for Lakehead University Library are not monitored, as there is no OCUL reference to compare against.
- Does not automatically download or deploy updated stanzas. It identifies updates and provides relevant links for manual review.
- For regular use, `most_recent_update_stanza.py` (or the **Sync** button) is recommended. If there has been a long gap between checks, run `update_stanza.py` (or **Audit**) before resuming weekly syncs.
