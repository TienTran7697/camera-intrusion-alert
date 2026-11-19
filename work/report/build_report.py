# -*- coding: utf-8 -*-
"""Dựng báo cáo hoàn chỉnh từ 'Bao cao do an - Chuong 1.docx' (giữ nguyên style, trang bìa, mục lục của mẫu):
chỉnh Chương 1, điền phần đầu, thay Chương 2–5 và tài liệu tham khảo. Sau đó mở bằng Word để cập nhật mục lục,
danh mục hình/bảng và số chú thích (update_fields).
python build_report.py
"""
import os, re, shutil, zipfile, subprocess, sys
from xml.sax.saxutils import escape
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "../.."))
SRC = os.path.join(ROOT, "Bao cao do an - Chuong 1.docx")
OUT = os.path.join(ROOT, "Bao cao do an - Hoan chinh.docx")
U = os.path.join(HERE, "u")
FIG = os.path.join(HERE, "fig")
sys.path.insert(0, HERE)
import report_content as C

# ---------------------------------------------------------------- trích dẫn
ORDER = list(C.CH1_KEYS)
CITE_RE = re.compile(r"[\{\[](" + "|".join(map(re.escape, C.REFS)) + r")[\}\]]")


def cite(t):
    def f(m):
        k = m.group(1)
        if k not in ORDER: ORDER.append(k)
        return f"[{ORDER.index(k) + 1}]"
    return CITE_RE.sub(f, t)


# ---------------------------------------------------------------- tạo XML
def run(t, b=False, i=False, sz=None):
    rpr = ("<w:b/>" if b else "") + ("<w:i/>" if i else "") + (f'<w:sz w:val="{sz}"/><w:szCs w:val="{sz}"/>' if sz else "")
    return f'<w:r>{"<w:rPr>" + rpr + "</w:rPr>" if rpr else ""}<w:t xml:space="preserve">{escape(t)}</w:t></w:r>'


RICH_RE = re.compile(r"(\*\*.+?\*\*|(?<!\w)_[^_]+?_(?!\w))")


def rich(t, sz=None, b=False):
    out = []
    for part in RICH_RE.split(cite(t)):
        if not part: continue
        if part.startswith("**"): out.append(run(part[2:-2], b=True, sz=sz))
        elif part.startswith("_") and part.endswith("_") and len(part) > 2: out.append(run(part[1:-1], b=b, i=True, sz=sz))
        else: out.append(run(part, b=b, sz=sz))
    return "".join(out)


def para(t, ppr='<w:jc w:val="both"/>'):
    return f"<w:p><w:pPr>{ppr}</w:pPr>{rich(t)}</w:p>"


def heading(level, t, extra=""):
    ind = '<w:ind w:left="567" w:hanging="567"/>' if level == 2 else ""
    return f'<w:p><w:pPr><w:pStyle w:val="Heading{level}"/>{ind}</w:pPr>{extra}{run(t)}</w:p>'


def equation(t, num):
    return ('<w:p><w:pPr><w:keepLines/><w:tabs><w:tab w:val="center" w:pos="4394"/><w:tab w:val="right" w:pos="8787"/></w:tabs>'
            '<w:spacing w:before="60" w:after="120"/><w:ind w:firstLine="0"/></w:pPr>'
            f'<w:r><w:tab/></w:r>{run(t, i=True)}<w:r><w:tab/></w:r>{run("(" + num + ")")}</w:p>')


CAP_N = {}


def caption(kind, title, chap):
    rp = '<w:rPr><w:rFonts w:cs="Times New Roman"/></w:rPr>'; rpn = '<w:rPr><w:rFonts w:cs="Times New Roman"/><w:noProof/></w:rPr>'
    CAP_N[(kind, chap)] = CAP_N.get((kind, chap), 0) + 1

    def fld(instr, val):
        return (f'<w:r>{rp}<w:fldChar w:fldCharType="begin"/></w:r><w:r>{rp}<w:instrText xml:space="preserve"> {instr} </w:instrText></w:r>'
                f'<w:r>{rp}<w:fldChar w:fldCharType="separate"/></w:r><w:r>{rpn}<w:t>{val}</w:t></w:r><w:r>{rpn}<w:fldChar w:fldCharType="end"/></w:r>')
    keep = '<w:keepNext/><w:spacing w:before="120"/>' if kind == "Bảng" else ""
    return (f'<w:p><w:pPr><w:pStyle w:val="Caption"/>{keep}<w:rPr><w:rFonts w:cs="Times New Roman"/></w:rPr></w:pPr>'
            f'<w:r>{rp}<w:t xml:space="preserve">{kind} </w:t></w:r>' + fld("STYLEREF 1 \\s", str(chap)) + f'<w:r>{rp}<w:t>.</w:t></w:r>'
            + fld(f"SEQ {kind} \\* ARABIC \\s 1", str(CAP_N[(kind, chap)]))
            + f'<w:r>{rp}<w:t xml:space="preserve">: {escape(cite(title))}</w:t></w:r></w:p>')


def table(widths, rows):
    total = sum(widths); grid = "".join(f'<w:gridCol w:w="{w}"/>' for w in widths)
    out = [f'<w:tbl><w:tblPr><w:tblStyle w:val="TableGrid"/><w:tblW w:w="{total}" w:type="dxa"/><w:jc w:val="center"/><w:tblLayout w:type="fixed"/>'
           '<w:tblCellMar><w:left w:w="85" w:type="dxa"/><w:right w:w="85" w:type="dxa"/></w:tblCellMar>'
           f'<w:tblLook w:val="04A0" w:firstRow="1" w:lastRow="0" w:firstColumn="1" w:lastColumn="0" w:noHBand="0" w:noVBand="1"/></w:tblPr><w:tblGrid>{grid}</w:tblGrid>']
    for ri, r in enumerate(rows):
        hdr = ri == 0
        trpr = '<w:trPr><w:tblHeader/><w:cantSplit/></w:trPr>' if hdr else '<w:trPr><w:cantSplit/></w:trPr>'
        cells = []
        for w, c in zip(widths, r):
            shade = '<w:shd w:val="clear" w:color="auto" w:fill="D9E2F3"/>' if hdr else ""
            jc = '<w:jc w:val="center"/>' if hdr else '<w:jc w:val="left"/>'
            keep = '<w:keepNext/>' if ri < len(rows) - 1 and len(rows) <= 8 else ''
            ps = [f'<w:p><w:pPr>{keep}<w:spacing w:before="40" w:after="40" w:line="276" w:lineRule="auto"/><w:ind w:firstLine="0"/>{jc}</w:pPr>'
                  f'{rich(line, sz=24, b=hdr)}</w:p>' for line in str(c).split("\n")]
            cells.append(f'<w:tc><w:tcPr><w:tcW w:w="{w}" w:type="dxa"/>{shade}<w:vAlign w:val="center"/></w:tcPr>{"".join(ps)}</w:tc>')
        out.append(f"<w:tr>{trpr}{''.join(cells)}</w:tr>")
    return "".join(out) + "</w:tbl>"


IMG = []          # (rid, tên tệp)


def image(fname, width_cm):
    n = len(IMG) + 1; rid = f"rId{3000 + n}"; IMG.append((rid, fname))
    wpx, hpx = Image.open(os.path.join(FIG, fname)).size
    cx = int(width_cm * 360000); cy = int(cx * hpx / wpx); did = 3000 + n
    return ('<w:p><w:pPr><w:keepNext/><w:spacing w:before="120" w:after="0"/><w:ind w:firstLine="0"/><w:jc w:val="center"/></w:pPr><w:r><w:drawing>'
            f'<wp:inline distT="0" distB="0" distL="0" distR="0"><wp:extent cx="{cx}" cy="{cy}"/><wp:docPr id="{did}" name="Hinh {did}"/>'
            '<wp:cNvGraphicFramePr><a:graphicFrameLocks xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" noChangeAspect="1"/></wp:cNvGraphicFramePr>'
            '<a:graphic xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">'
            f'<pic:pic xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture"><pic:nvPicPr><pic:cNvPr id="{did}" name="{fname}"/><pic:cNvPicPr/></pic:nvPicPr>'
            f'<pic:blipFill><a:blip r:embed="{rid}"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
            f'<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr>'
            '</pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing></w:r></w:p>')


def render(items, chap, first_heading_extra=""):
    out = []
    for it in items:
        k = it[0]
        if k == "h1": out.append(heading(1, it[1], first_heading_extra)); first_heading_extra = ""
        elif k in ("h2", "h3", "h4"): out.append(heading(int(k[1]), it[1]))
        elif k == "p": out.append(para(it[1]))
        elif k == "eq": out.append(equation(it[1], it[2]))
        elif k == "fig": out += [image(it[1], it[2]), caption("Hình", it[3], chap)]
        elif k == "tab": out += [caption("Bảng", it[1], chap), table(it[2], it[3]), '<w:p><w:pPr><w:spacing w:after="0"/></w:pPr></w:p>']
    return "".join(out)


# ---------------------------------------------------------------- xử lý tài liệu
def p_bounds(x, pos):
    """Vị trí (đầu, cuối) của đoạn <w:p> chứa vị trí pos."""
    a = max(x.rfind("<w:p ", 0, pos), x.rfind("<w:p>", 0, pos)); b = x.find("</w:p>", pos) + 6
    return a, b


def main():
    shutil.rmtree(U, ignore_errors=True)
    with zipfile.ZipFile(SRC) as z: z.extractall(U)
    D = os.path.join(U, "word/document.xml"); x = open(D, encoding="utf-8").read()

    # 1) chỉnh Chương 1
    for a, b in C.CH1_FIX:
        a, b = escape(a), escape(b); assert x.count(a) == 1, a[:60]; x = x.replace(a, b)
    h1a = x.find('<w:pStyle w:val="Heading1"/>'); h2a = x.find('<w:pStyle w:val="Heading1"/>', h1a + 10)
    seg = x[h1a:h2a]
    seg = seg.replace("<w:p><w:r>", '<w:p><w:pPr><w:jc w:val="both"/></w:pPr><w:r>').replace("<w:p><w:bookmarkStart", '<w:p><w:pPr><w:jc w:val="both"/></w:pPr><w:bookmarkStart')
    x = x[:h1a] + seg + x[h2a:]

    # 2) phần đầu: danh mục từ viết tắt, tóm tắt, mở đầu
    t = x.find("DANH MỤC TỪ VIẾT TẮT"); _, a = p_bounds(x, t); s = x.find("<w:sectPr", a); b, _ = p_bounds(x, s)
    x = x[:a] + caption_free_table(C.ABBR) + x[b:]
    t = x.find("TÓM TẮT "); _, a = p_bounds(x, t); t2 = x.find("MỞ ĐẦU", a); b, _ = p_bounds(x, t2)
    x = x[:a] + "".join(para(p) for p in C.SUMMARY) + x[b:]
    t = x.find("MỞ ĐẦU"); _, a = p_bounds(x, t); t2 = x.find('<w:pStyle w:val="Heading1"/>', a); b, _ = p_bounds(x, t2)
    x = x[:a] + "".join(para(p) for p in C.INTRO) + x[b:]

    # 3) Chương 2–5
    t = x.find("CƠ SỞ LÝ THUYẾT", x.find('<w:pStyle w:val="Heading1"/>', x.find("TỔNG QUAN VỀ ĐỀ TÀI</w:t>") + 10) - 10)
    r_start, _ = p_bounds(x, t)
    tl = x.find("TÀI LIỆU THAM KHẢO", r_start); tl_start, tl_end = p_bounds(x, tl)
    s = x.rfind("<w:sectPr", r_start, tl_start); _, r_end = p_bounds(x, s)
    sect = x[s:x.find("</w:sectPr>", s) + 11]
    old = x[r_start:r_end]
    assert '<w:bookmarkEnd w:id="2"/>' in old and '<w:bookmarkEnd w:id="3"/>' in old
    sect_p = f"<w:p><w:pPr>{sect}</w:pPr></w:p>"; page_p = '<w:p><w:r><w:br w:type="page"/></w:r></w:p>'
    body = (render(C.CH2, 2, '<w:bookmarkEnd w:id="2"/><w:bookmarkEnd w:id="3"/>') + sect_p
            + render(C.CH3, 3) + page_p + render(C.CH4, 4) + page_p + render(C.CH5, 5) + sect_p)
    x = x[:r_start] + body + x[r_end:]

    # 4) tài liệu tham khảo
    tl = x.find("TÀI LIỆU THAM KHẢO"); _, a = p_bounds(x, tl); b0, b = p_bounds(x, x.find("IEEE", a))
    assert b0 == a
    refs = "".join(f'<w:p><w:pPr><w:ind w:left="567" w:hanging="567"/><w:jc w:val="both"/></w:pPr>{run(f"[{i + 1}]  ")}{rich(C.REFS[k])}</w:p>'
                   for i, k in enumerate(ORDER))
    unused = [k for k in C.REFS if k not in ORDER]
    x = x[:a] + refs + x[b:]
    open(D, "w", encoding="utf-8").write(x)

    # 5) ảnh: media, rels, content types
    os.makedirs(os.path.join(U, "word/media"), exist_ok=True)
    rp = os.path.join(U, "word/_rels/document.xml.rels"); rels = open(rp, encoding="utf-8").read()
    for rid, f in IMG:
        shutil.copy(os.path.join(FIG, f), os.path.join(U, "word/media", f))
        rels = rels.replace("</Relationships>", f'<Relationship Id="{rid}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/{f}"/></Relationships>')
    open(rp, "w", encoding="utf-8").write(rels)
    cp = os.path.join(U, "[Content_Types].xml"); ct = open(cp, encoding="utf-8").read()
    for ext, typ in (("png", "image/png"), ("jpg", "image/jpeg")):
        if f'Extension="{ext}"' not in ct: ct = ct.replace('<Default Extension="xml"', f'<Default Extension="{ext}" ContentType="{typ}"/><Default Extension="xml"')
    open(cp, "w", encoding="utf-8").write(ct)

    # 6) kiểm tra bookmark và đóng gói
    starts = set(re.findall(r'<w:bookmarkStart w:id="(\d+)"', x)); ends = set(re.findall(r'<w:bookmarkEnd w:id="(\d+)"', x))
    assert starts == ends, (starts ^ ends)
    files = []
    for r_, _, fs in os.walk(U):
        for f in fs: p = os.path.join(r_, f); files.append((os.path.relpath(p, U).replace(os.sep, "/"), p))
    files.sort(key=lambda t: (t[0] != "[Content_Types].xml", t[0]))
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
        for arc, p in files: z.write(p, arc)
    print("saved", OUT, "| hinh:", len(IMG), "| tai lieu:", len(ORDER), "| khong dung:", unused)


def caption_free_table(rows):
    return table([1800, 3500, 3487], rows) + '<w:p><w:pPr><w:spacing w:after="0"/></w:pPr></w:p>'


if __name__ == "__main__":
    main()
