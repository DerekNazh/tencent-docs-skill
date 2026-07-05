# tencent-docs-skill

腾讯文档 Open API 的 Claude Code Skill —— 通过 Python CLI 驱动腾讯文档的读写、管理和收集表数据导出。

## 安装

```bash
npx skills add DerekNazh/tencent-docs-skill
```

## 功能

- 📁 文件管理：列出、搜索、创建、重命名、移动、复制、删除
- 📊 表格读写：读取/写入/清空单元格，添加子表，删除行/列
- 📝 收集表：一键读取表单数据（自动导出+解析）
- 🔐 权限控制：禁止复制、评论等
- 👥 多账号：`--account 1/2` 切换
- 📄 文档读取：获取在线文档结构化内容

## 配置凭证

安装后，编辑凭证文件：

```bash
cd ~/.claude/skills/tencent-docs
cp .env.example .env
# 编辑 .env 填入你的腾讯文档 API 凭证
```

凭证获取：[腾讯文档开放平台](https://docs.qq.com/open/)

## 使用

```bash
SCRIPT="$HOME/.claude/skills/tencent-docs/scripts/tencent_docs.py"

# 验证认证
python "$SCRIPT" --account 1 verify

# 列出文件
python "$SCRIPT" --account 1 list-folder

# 读取收集表
python "$SCRIPT" --account 2 read-form FILE_ID

# 写入表格
python "$SCRIPT" --account 1 write-sheet FILE_ID --sheet-id XX --range A1:B2 --values '[["a","b"],["c","d"]]'
```

## 依赖

```bash
pip install -r ~/.claude/skills/tencent-docs/scripts/requirements.txt
```

## 注意事项

- `.env` 文件包含 API Token，**绝对不能提交到 Git**
- Access Token 有效期约 30 天，过期需重新获取
- 收集表题目编辑不支持 API，只能在网页端手动修改
- 文档写入需要 `scope.doc` 权限（需在开放平台额外申请审核）
