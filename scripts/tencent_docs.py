#!/usr/bin/env python
"""腾讯文档 Open API CLI — 统一命令行入口。

用法:
    python tencent_docs.py --account 1 verify
    python tencent_docs.py --account 2 list-folder
    python tencent_docs.py --account 2 read-form FILE_ID
    python tencent_docs.py --account 1 search "关键词"
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# 将 scripts/ 目录加入 sys.path 以支持直接运行
_SCRIPT_DIR = str(Path(__file__).resolve().parent)
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

from tencent_docs_client import TencentDocsClient, TencentDocsError
from tencent_docs_config import load_auth


def _json_output(data: object) -> None:
    """输出 JSON 格式。"""
    print(json.dumps(data, ensure_ascii=False, indent=2))


def _table_output(data: object) -> None:
    """输出人类可读的表格格式。"""
    if isinstance(data, list):
        if not data:
            print("(空)")
            return
        if isinstance(data[0], dict):
            # 提取所有键
            keys: list[str] = []
            for item in data:
                for k in item:
                    if k not in keys:
                        keys.append(k)
            # 计算列宽
            widths = {k: max(len(str(k)), *(len(str(item.get(k, ""))) for item in data)) for k in keys}
            # 表头
            header = " | ".join(k.ljust(widths[k]) for k in keys)
            sep = "-+-".join("-" * widths[k] for k in keys)
            print(header)
            print(sep)
            for item in data:
                row = " | ".join(str(item.get(k, "")).ljust(widths[k]) for k in keys)
                print(row)
        else:
            for item in data:
                print(item)
    elif isinstance(data, dict):
        for k, v in data.items():
            if isinstance(v, list) and v and isinstance(v[0], dict):
                print(f"\n{k}:")
                _table_output(v)
            else:
                print(f"  {k}: {v}")
    else:
        print(data)


def _output(data: object, fmt: str) -> None:
    """根据格式输出数据。"""
    if fmt == "json":
        _json_output(data)
    elif fmt == "table":
        _table_output(data)
    else:
        print(data)


def _build_client(args: argparse.Namespace) -> TencentDocsClient:
    """根据参数构建客户端。"""
    auth = load_auth(args.account)
    return TencentDocsClient(auth)


def _extract_file_id(raw_id: str) -> str:
    """从 URL 或原始 ID 中提取 fileID。

    支持:
      - 纯 ID: 300000000$ezRpaCQFjtkX
      - URL: https://docs.qq.com/form/page/DZXpScGFDUUZqdGtY
    """
    if raw_id.startswith("http"):
        # 从 URL 中提取最后一段
        parts = raw_id.rstrip("/").split("/")
        return parts[-1]
    return raw_id


def cmd_verify(args: argparse.Namespace) -> None:
    """验证认证。"""
    client = _build_client(args)
    data = client.verify()
    _output(data, args.format)


def cmd_list_folder(args: argparse.Namespace) -> None:
    """列出文件夹内容。"""
    client = _build_client(args)
    folder_id = args.folder_id if args.folder_id else "/"
    items = client.list_folder(folder_id=folder_id)
    # 精简输出
    summary = [
        {
            "ID": item.get("ID", ""),
            "title": item.get("title", ""),
            "type": item.get("type", ""),
            "url": item.get("url", ""),
        }
        for item in items
    ]
    _output(summary, args.format)


def cmd_search(args: argparse.Namespace) -> None:
    """搜索文件。"""
    client = _build_client(args)
    items = client.search(args.keyword)
    summary = [
        {
            "ID": item.get("ID", ""),
            "title": item.get("title", ""),
            "type": item.get("type", ""),
            "url": item.get("url", ""),
        }
        for item in items
    ]
    _output(summary, args.format)


def cmd_read_metadata(args: argparse.Namespace) -> None:
    """读取文件元数据。"""
    client = _build_client(args)
    file_id = _extract_file_id(args.file_id)
    data = client.read_metadata(file_id)
    _output(data, args.format)


def cmd_read_doc(args: argparse.Namespace) -> None:
    """读取在线文档内容。"""
    client = _build_client(args)
    file_id = _extract_file_id(args.file_id)
    data = client.read_doc(file_id, export_type=args.export_type)
    _output(data, args.format)


def cmd_read_sheet(args: argparse.Namespace) -> None:
    """读取表格单元格。"""
    client = _build_client(args)
    file_id = _extract_file_id(args.file_id)
    values = client.read_sheet(file_id, args.sheet_id, args.range)
    _output(values, args.format)


def cmd_read_form(args: argparse.Namespace) -> None:
    """读取收集表内容（自动导出解析）。"""
    client = _build_client(args)
    file_id = _extract_file_id(args.file_id)
    result = client.read_form(file_id)
    _output(result, args.format)


def cmd_create_file(args: argparse.Namespace) -> None:
    """创建文件。"""
    client = _build_client(args)
    data = client.create_file(
        title=args.title,
        doc_type=args.type,
        folder_id=args.folder_id,
    )
    _output(data, args.format)


def cmd_upload_image(args: argparse.Namespace) -> None:
    """上传图片。"""
    client = _build_client(args)
    data = client.upload_image(args.image_path)
    _output(data, args.format)


def cmd_rename(args: argparse.Namespace) -> None:
    """重命名文件。"""
    if not args.confirm:
        client = _build_client(args)
        file_id = _extract_file_id(args.file_id)
        meta = client.read_metadata(file_id)
        print(f"⚠️  即将重命名:")
        print(f"   当前标题: {meta.get('title', '?')}")
        print(f"   新标题: {args.new_title}")
        print(f"   URL: {meta.get('url', '?')}")
        print(f"   加 --confirm 确认执行")
        return
    client = _build_client(args)
    file_id = _extract_file_id(args.file_id)
    data = client.rename(file_id, args.new_title)
    _output(data, args.format)


def cmd_move(args: argparse.Namespace) -> None:
    """移动文件。"""
    if not args.confirm:
        client = _build_client(args)
        file_id = _extract_file_id(args.file_id)
        meta = client.read_metadata(file_id)
        print(f"⚠️  即将移动:")
        print(f"   文件: {meta.get('title', '?')}")
        print(f"   目标文件夹: {args.dest_folder_id}")
        print(f"   加 --confirm 确认执行")
        return
    client = _build_client(args)
    file_id = _extract_file_id(args.file_id)
    data = client.move(file_id, args.dest_folder_id)
    _output(data, args.format)


def cmd_copy(args: argparse.Namespace) -> None:
    """复制文件。"""
    client = _build_client(args)
    file_id = _extract_file_id(args.file_id)
    data = client.copy(file_id, args.title)
    _output(data, args.format)


def cmd_delete(args: argparse.Namespace) -> None:
    """删除文件。"""
    if not args.confirm:
        client = _build_client(args)
        file_id = _extract_file_id(args.file_id)
        meta = client.read_metadata(file_id)
        print(f"⚠️  即将删除 (移入回收站):")
        print(f"   标题: {meta.get('title', '?')}")
        print(f"   URL: {meta.get('url', '?')}")
        print(f"   加 --confirm 确认执行")
        return
    client = _build_client(args)
    file_id = _extract_file_id(args.file_id)
    data = client.delete(file_id)
    _output(data, args.format)


def cmd_async_export(args: argparse.Namespace) -> None:
    """异步导出文件。"""
    client = _build_client(args)
    file_id = _extract_file_id(args.file_id)
    content = client.async_export(file_id, export_type=args.export_type)

    # 保存到文件
    output_path = args.output
    if not output_path:
        ext = "xlsx" if args.export_type == "xlsx" else "pdf"
        output_path = f"export_{file_id.split('$')[-1]}.{ext}"

    Path(output_path).write_bytes(content)
    print(f"已导出到: {output_path} ({len(content)} bytes)")


def cmd_write_sheet(args: argparse.Namespace) -> None:
    """写入表格单元格。"""
    import json as _json

    client = _build_client(args)
    file_id = _extract_file_id(args.file_id)
    values = _json.loads(args.values)
    data = client.write_sheet(file_id, args.sheet_id, args.range, values)
    _output(data, args.format)


def cmd_clear_sheet(args: argparse.Namespace) -> None:
    """清空表格单元格范围。"""
    client = _build_client(args)
    file_id = _extract_file_id(args.file_id)
    data = client.clear_sheet(file_id, args.sheet_id, args.range)
    _output(data, args.format)


def cmd_add_sheet(args: argparse.Namespace) -> None:
    """添加新子表。"""
    client = _build_client(args)
    file_id = _extract_file_id(args.file_id)
    data = client.add_sheet(file_id, args.title)
    _output(data, args.format)


def cmd_delete_rows(args: argparse.Namespace) -> None:
    """删除行。"""
    client = _build_client(args)
    file_id = _extract_file_id(args.file_id)
    data = client.delete_rows(file_id, args.sheet_id, args.start, args.count)
    _output(data, args.format)


def cmd_delete_cols(args: argparse.Namespace) -> None:
    """删除列。"""
    client = _build_client(args)
    file_id = _extract_file_id(args.file_id)
    data = client.delete_columns(file_id, args.sheet_id, args.start, args.count)
    _output(data, args.format)


def main() -> None:
    """CLI 入口。"""
    parser = argparse.ArgumentParser(
        prog="tencent_docs",
        description="腾讯文档 Open API CLI",
    )
    parser.add_argument(
        "--account",
        type=int,
        default=1,
        choices=[1, 2],
        help="账号编号 (1 或 2)，默认 1",
    )
    parser.add_argument(
        "--format",
        dest="format",
        choices=["json", "table"],
        default="json",
        help="输出格式 (默认 json)",
    )

    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # verify
    sub_verify = subparsers.add_parser("verify", help="验证认证是否有效")
    sub_verify.set_defaults(func=cmd_verify)

    # list-folder
    sub_ls = subparsers.add_parser("list-folder", help="列出文件夹内容")
    sub_ls.add_argument("folder_id", nargs="?", default="/", help="文件夹 ID (默认根目录)")
    sub_ls.set_defaults(func=cmd_list_folder)

    # search
    sub_search = subparsers.add_parser("search", help="搜索文件")
    sub_search.add_argument("keyword", help="搜索关键词")
    sub_search.set_defaults(func=cmd_search)

    # read-metadata
    sub_meta = subparsers.add_parser("read-metadata", help="读取文件元数据")
    sub_meta.add_argument("file_id", help="文件 ID 或 docs.qq.com URL")
    sub_meta.set_defaults(func=cmd_read_metadata)

    # read-doc
    sub_doc = subparsers.add_parser("read-doc", help="读取在线文档内容")
    sub_doc.add_argument("file_id", help="文件 ID 或 docs.qq.com URL")
    sub_doc.add_argument("--export-type", default="text", help="导出类型 (默认 text)")
    sub_doc.set_defaults(func=cmd_read_doc)

    # read-sheet
    sub_sheet = subparsers.add_parser("read-sheet", help="读取表格单元格")
    sub_sheet.add_argument("file_id", help="文件 ID 或 docs.qq.com URL")
    sub_sheet.add_argument("--sheet-id", required=True, help="工作表 ID")
    sub_sheet.add_argument("--range", default="A1:Z100", help="单元格范围 (默认 A1:Z100)")
    sub_sheet.set_defaults(func=cmd_read_sheet)

    # read-form
    sub_form = subparsers.add_parser("read-form", help="读取收集表内容 (自动导出解析)")
    sub_form.add_argument("file_id", help="文件 ID 或 docs.qq.com URL")
    sub_form.set_defaults(func=cmd_read_form)

    # create-file
    sub_create = subparsers.add_parser("create-file", help="创建文件")
    sub_create.add_argument("title", help="文件标题")
    sub_create.add_argument("--type", required=True, help="文件类型 (doc/sheet/slide/mind/flowchart/smartsheet/form)")
    sub_create.add_argument("--folder-id", default=None, help="目标文件夹 ID")
    sub_create.set_defaults(func=cmd_create_file)

    # upload-image
    sub_img = subparsers.add_parser("upload-image", help="上传图片")
    sub_img.add_argument("image_path", help="图片文件路径")
    sub_img.set_defaults(func=cmd_upload_image)

    # rename
    sub_rename = subparsers.add_parser("rename", help="重命名文件 (需 --confirm)")
    sub_rename.add_argument("file_id", help="文件 ID 或 docs.qq.com URL")
    sub_rename.add_argument("new_title", help="新标题")
    sub_rename.add_argument("--confirm", action="store_true", help="确认执行写操作")
    sub_rename.set_defaults(func=cmd_rename)

    # move
    sub_move = subparsers.add_parser("move", help="移动文件 (需 --confirm)")
    sub_move.add_argument("file_id", help="文件 ID 或 docs.qq.com URL")
    sub_move.add_argument("--folder-id", dest="dest_folder_id", required=True, help="目标文件夹 ID")
    sub_move.add_argument("--confirm", action="store_true", help="确认执行写操作")
    sub_move.set_defaults(func=cmd_move)

    # copy
    sub_copy = subparsers.add_parser("copy", help="复制文件")
    sub_copy.add_argument("file_id", help="文件 ID 或 docs.qq.com URL")
    sub_copy.add_argument("--title", required=True, help="副本标题")
    sub_copy.set_defaults(func=cmd_copy)

    # delete
    sub_delete = subparsers.add_parser("delete", help="删除文件 (需 --confirm)")
    sub_delete.add_argument("file_id", help="文件 ID 或 docs.qq.com URL")
    sub_delete.add_argument("--confirm", action="store_true", help="确认执行写操作")
    sub_delete.set_defaults(func=cmd_delete)

    # async-export
    sub_export = subparsers.add_parser("async-export", help="异步导出文件到本地")
    sub_export.add_argument("file_id", help="文件 ID 或 docs.qq.com URL")
    sub_export.add_argument("--export-type", default="xlsx", help="导出格式 (xlsx/pdf, 默认 xlsx)")
    sub_export.add_argument("--output", default=None, help="输出文件路径")
    sub_export.set_defaults(func=cmd_async_export)

    # write-sheet
    sub_ws = subparsers.add_parser("write-sheet", help="写入表格单元格")
    sub_ws.add_argument("file_id", help="表格文件 ID")
    sub_ws.add_argument("--sheet-id", required=True, help="工作表 ID")
    sub_ws.add_argument("--range", required=True, help="写入范围，如 A1:C3")
    sub_ws.add_argument("--values", required=True, help="JSON 二维数组，如 [[\"a\",\"b\"],[\"c\",\"d\"]]")
    sub_ws.set_defaults(func=cmd_write_sheet)

    # clear-sheet
    sub_cs = subparsers.add_parser("clear-sheet", help="清空表格单元格范围")
    sub_cs.add_argument("file_id", help="表格文件 ID")
    sub_cs.add_argument("--sheet-id", required=True, help="工作表 ID")
    sub_cs.add_argument("--range", required=True, help="清空范围，如 A1:Z100")
    sub_cs.set_defaults(func=cmd_clear_sheet)

    # add-sheet
    sub_as = subparsers.add_parser("add-sheet", help="添加新子表")
    sub_as.add_argument("file_id", help="表格文件 ID")
    sub_as.add_argument("--title", required=True, help="新子表标题")
    sub_as.set_defaults(func=cmd_add_sheet)

    # delete-rows
    sub_dr = subparsers.add_parser("delete-rows", help="删除行")
    sub_dr.add_argument("file_id", help="表格文件 ID")
    sub_dr.add_argument("--sheet-id", required=True, help="工作表 ID")
    sub_dr.add_argument("--start", type=int, required=True, help="起始行号 (0-based)")
    sub_dr.add_argument("--count", type=int, default=1, help="删除行数 (默认 1)")
    sub_dr.set_defaults(func=cmd_delete_rows)

    # delete-cols
    sub_dc = subparsers.add_parser("delete-cols", help="删除列")
    sub_dc.add_argument("file_id", help="表格文件 ID")
    sub_dc.add_argument("--sheet-id", required=True, help="工作表 ID")
    sub_dc.add_argument("--start", type=int, required=True, help="起始列号 (0-based)")
    sub_dc.add_argument("--count", type=int, default=1, help="删除列数 (默认 1)")
    sub_dc.set_defaults(func=cmd_delete_cols)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        args.func(args)
    except TencentDocsError as e:
        print(f"❌ {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"❌ 配置错误: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ 未预期错误: {e}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
