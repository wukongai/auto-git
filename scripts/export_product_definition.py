"""仅导出产品定义主文与显式图片，不递归展开工程附件。"""
import argparse
import base64
import hashlib
import json
import re
from pathlib import Path
from html import escape
from markdown_it import MarkdownIt

CSS = """
@page { size: A4; margin: 17mm 16mm 18mm; }
body { font-family: "PingFang SC", "Noto Sans CJK SC", sans-serif; color: #20344e; font-size: 10.5pt; line-height: 1.65; }
h1 { font-size: 25pt; margin: 0 0 20pt; color:#14263d; }
h2 { font-size: 18pt; border-bottom:2px solid #285ba8; padding-bottom:7pt; margin:20pt 0 16pt; break-before:auto; }
h1 + h2 { break-before:auto; }
h3 { font-size:12.5pt; color:#285ba8; margin:16pt 0 8pt; }
h2,h3 { break-after:avoid; }
p { margin:7pt 0; orphans:3; widows:3; }
li { margin:5pt 0; }
table { border-collapse:collapse; width:100%; font-size:9.5pt; margin:12pt 0; break-inside:avoid; }
th,td { border:1px solid #d6dfe9; padding:7pt; vertical-align:top; overflow-wrap:anywhere; }
th { background:#edf3fa; color:#1d466e; }
thead { display:table-header-group; }
tr { break-inside:avoid; }
a { color:#285ba8; text-decoration:none; }
img { width:100%; height:auto; }
figure { margin:10pt 0 16pt; break-inside:avoid; }
figcaption { font-size:9pt; color:#65788f; }
.chart-page { break-inside:avoid; }
.chart-page h3 { margin-top:0; }
"""
def build(source, output):
    """保持主文内容；只解析图片，附件链接保持本机可点击引用。"""
    text = source.read_text(encoding="utf-8")
    text = re.sub(r"\A---\n.*?\n---\n", "", text, flags=re.S)
    parser = MarkdownIt("commonmark", {"html": False}).enable("table")
    body = parser.render(text)
    body = re.sub(r"\*\*([^\n]+?)\*\*", r"<strong>\1</strong>", body)
    images = []
    # 六领域布局的图片可位于knowledge；仍限制在主文所属docs树内。
    docs_root = next((p for p in source.parents if p.name == "docs"), source.parent)
    def embed(match):
        """只内嵌docs树以内的静态图片，禁止越界和网络请求。"""
        target = (source.parent / match.group(1)).resolve()
        if not target.is_relative_to(docs_root.resolve()) or not target.is_file():
            raise ValueError("图片不存在或越界：" + match.group(1))
        if target.suffix.lower() != ".png":
            raise ValueError("本导出入口仅支持已审核PNG")
        images.append(str(target))
        return 'src="data:image/png;base64,' + base64.b64encode(target.read_bytes()).decode() + '"'
    body = re.sub(r'src="([^"]+)"', embed, body)
    def link(match):
        """保留外部链接；本地引用只改为真实文件地址，不读取附件内容。"""
        target = match.group(1)
        if re.match(r"(https?://|mailto:|#)", target):
            return match.group(0)
        name, mark, anchor = target.partition("#")
        file = (source.parent / name).resolve()
        if not file.is_file():
            raise ValueError("引用文件不存在：" + name)
        return 'href="' + escape(file.as_uri() + (mark + anchor if mark else ""), quote=True) + '"'
    body = re.sub(r'href="([^"]+)"', link, body)
    # 两张宽画布各占独立页，文字仍按主文原有顺序排列。
    body = re.sub(r'(<h3>创业初期版</h3>\s*<p><img.*?</p>)', r'<section class="chart-page">\1</section>', body, flags=re.S)
    body = re.sub(r'(<h3>传统经营版</h3>\s*<p><img.*?</p>)', r'<section class="chart-page">\1</section>', body, flags=re.S)
    body = re.sub(r'<p>(<img[^>]+>)</p>', r'<figure>\1</figure>', body)
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        raise FileExistsError(output)
    output.write_text('<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>Auto Git 产品定义 0.2</title><style>' + CSS + '</style><body>' + body + '</body></html>', encoding="utf-8")
    return {"source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(), "images": images, "html": str(output)}

def main():
    """显式指定主文和输出，不覆盖已有导出。"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.source.resolve(), args.output.resolve()), ensure_ascii=False))

if __name__ == "__main__":
    main()
