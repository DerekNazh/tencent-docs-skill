---
name: tencent-docs
description: Create, read, list, search, and manage Tencent Docs (腾讯文档) — online documents, sheets, slides, mind maps, flowcharts, smart tables, and forms — via the Tencent Docs Open API. Use when the user mentions 腾讯文档 / Tencent Docs / docs.qq.com, a docs.qq.com link, or wants to create / read / organize a doc, sheet, slide, mind map, or flowchart in their Tencent Docs space.
---

# Tencent Docs (腾讯文档)

Drive the [Tencent Docs Open API](https://docs.qq.com/open/document/app/) via
the Python CLI in `scripts/`. Everything runs **in the user's own Tencent Docs
account** — only files they can access, only the scopes they granted at connect
time.

## Quick start

All commands go through the single CLI entry point:

```sh
SCRIPT="$(dirname "$0")/scripts/tencent_docs.py"
# Or use the absolute path after installation:
# SCRIPT="$HOME/.claude/skills/tencent-docs/scripts/tencent_docs.py"
python "$SCRIPT" --account 1 verify
```

**`--account N`** selects which account (1 or 2, default 1).
**`--format json|table`** selects output format (default json).

## Auth & multi-account

Credentials live in `.env` (same directory as this file). Two accounts are
configured:

- **Account 1** (蓝): `TENCENTDOCS1_*` env vars
- **Account 2**: `TENCENTDOCS2_*` env vars

Switch with `--account 2`. The CLI loads credentials automatically — never
handle tokens manually.

If `verify` returns error code `400006`, the token has expired — tell the user
to re-authorize.

## Response & error handling

The CLI checks every API response (`ret == 0` = success). On error it prints
a Chinese message and exits non-zero. Common codes:

| code | meaning | what to do |
|---|---|---|
| `400006` | access token expired | tell user to re-authorize |
| `400007` | VIP (超级会员) required | link https://docs.qq.com/vip |
| `400008` | 积分 insufficient | tell user to top up |

## Doc types

| type | Product |
|---|---|
| `doc` | 在线文档 (Word-style) |
| `sheet` | 在线表格 (Excel) |
| `slide` | 幻灯片 (PPT) |
| `mind` | 思维导图 |
| `flowchart` | 流程图 |
| `smartsheet` | 智能表格 |
| `form` | 收集表 |

## Commands

### Verify auth (always run first)

```sh
python "$SCRIPT" --account 1 verify
```

### List a folder

Root folder (default):

```sh
python "$SCRIPT" --account 1 list-folder
```

Specific folder:

```sh
python "$SCRIPT" --account 1 list-folder FOLDER_ID
```

### Search files

```sh
python "$SCRIPT" --account 1 search "Q1 预算"
```

### Read file metadata

Accepts a file ID or a `docs.qq.com` URL:

```sh
python "$SCRIPT" --account 1 read-metadata FILE_ID
python "$SCRIPT" --account 1 read-metadata "https://docs.qq.com/doc/XXXXX"
```

### Read an online document

```sh
python "$SCRIPT" --account 1 read-doc FILE_ID
```

### Read a sheet's cell range

```sh
python "$SCRIPT" --account 1 read-sheet FILE_ID --sheet-id SHEET_ID --range A1:D10
```

### Write values to a sheet

```sh
python "$SCRIPT" --account 1 write-sheet FILE_ID --sheet-id SHEET_ID --range A1:C2 --values '[["姓名","年龄","城市"],["张三","25","北京"]]'
```

`--values` is a JSON 2D array matching the range dimensions.

### Clear a sheet range

```sh
python "$SCRIPT" --account 1 clear-sheet FILE_ID --sheet-id SHEET_ID --range A1:Z10
```

### Add a new worksheet (sub-table)

```sh
python "$SCRIPT" --account 1 add-sheet FILE_ID --title "新子表"
```

### Delete rows

```sh
python "$SCRIPT" --account 1 delete-rows FILE_ID --sheet-id SHEET_ID --start 2 --count 3
```

`--start` is 0-based (row 0 = first row). Deletes 3 rows starting from row 2.

### Delete columns

```sh
python "$SCRIPT" --account 1 delete-cols FILE_ID --sheet-id SHEET_ID --start 1 --count 2
```

`--start` is 0-based (column 0 = column A). Deletes 2 columns starting from column 1 (B).

### Read a form (收集表) — one command

Automatically generates the result sheet, async-exports to xlsx, and parses
the content:

```sh
python "$SCRIPT" --account 2 read-form FILE_ID
```

Output includes `fields` (question names) and `records` (submitted answers).

### Create a file

```sh
python "$SCRIPT" --account 1 create-file "会议纪要 2026-07-03" --type doc
python "$SCRIPT" --account 1 create-file "数据表" --type sheet --folder-id FOLDER_ID
```

### Upload an image

```sh
python "$SCRIPT" --account 1 upload-image ./cover.png
```

### Rename a file — GATED

Without `--confirm`, shows a preview only:

```sh
python "$SCRIPT" --account 1 rename FILE_ID "新标题"
```

With `--confirm`, executes the rename:

```sh
python "$SCRIPT" --account 1 rename FILE_ID "新标题" --confirm
```

### Move a file — GATED

```sh
python "$SCRIPT" --account 1 move FILE_ID --folder-id DEST_FOLDER_ID --confirm
```

### Copy a file

```sh
python "$SCRIPT" --account 1 copy FILE_ID --title "副本 - 项目计划"
```

### Delete a file — GATED

```sh
python "$SCRIPT" --account 1 delete FILE_ID --confirm
```

### Async export (manual)

For advanced use — `read-form` already handles this automatically:

```sh
python "$SCRIPT" --account 1 async-export FILE_ID --export-type xlsx --output result.xlsx
```

## Notes

- **Gate writes.** Rename / move / delete require `--confirm`; without it the
  command only shows a preview.
- **Extract ids from links.** Commands accept both raw file IDs and full
  `docs.qq.com` URLs — the CLI extracts the ID automatically.
- **Pagination.** List / search may return paginated results; pass cursor
  parameters as needed.
- **Rate / quota.** Free apps get 20,000 API calls/month. A `400007` /
  `400008` error means account tier / credits, not a bug.
- **Dependencies.** The CLI needs `requests` and `openpyxl` — install with
  `pip install -r scripts/requirements.txt`.
