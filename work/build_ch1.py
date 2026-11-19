# Chèn nội dung Chương 1 vào bản sao mẫu báo cáo, giữ nguyên style của mẫu.
import re, shutil, os
from xml.sax.saxutils import escape
from PIL import Image

D = "unpacked/word/document.xml"
x = open(D, encoding="utf-8").read()

# ---------- helpers ----------
def run(t, b=False, i=False, sz=None):
    rpr = ""
    if b: rpr += "<w:b/>"
    if i: rpr += "<w:i/>"
    if sz: rpr += f'<w:sz w:val="{sz}"/><w:szCs w:val="{sz}"/>'
    rpr = f"<w:rPr>{rpr}</w:rPr>" if rpr else ""
    return f'<w:r>{rpr}<w:t xml:space="preserve">{escape(t)}</w:t></w:r>'

def rich(t, sz=None):
    """**đậm** và _nghiêng_ đơn giản."""
    out = []
    for part in re.split(r"(\*\*.+?\*\*|_[^_]+?_)", t):
        if not part: continue
        if part.startswith("**"): out.append(run(part[2:-2], b=True, sz=sz))
        elif part.startswith("_") and part.endswith("_") and len(part) > 2: out.append(run(part[1:-1], i=True, sz=sz))
        else: out.append(run(part, sz=sz))
    return "".join(out)

def para(t, extra_ppr="", prefix=""):
    ppr = f"<w:pPr>{extra_ppr}</w:pPr>" if extra_ppr else ""
    return f"<w:p>{ppr}{prefix}{rich(t)}</w:p>"

def caption(kind, title):
    # Giữ đúng cấu trúc field STYLEREF + SEQ của mẫu
    rp = '<w:rPr><w:rFonts w:cs="Times New Roman"/></w:rPr>'
    rpn = '<w:rPr><w:rFonts w:cs="Times New Roman"/><w:noProof/></w:rPr>'
    def fld(instr, val):
        return (f'<w:r>{rp}<w:fldChar w:fldCharType="begin"/></w:r>'
                f'<w:r>{rp}<w:instrText xml:space="preserve"> {instr} </w:instrText></w:r>'
                f'<w:r>{rp}<w:fldChar w:fldCharType="separate"/></w:r>'
                f'<w:r>{rpn}<w:t>{val}</w:t></w:r>'
                f'<w:r>{rpn}<w:fldChar w:fldCharType="end"/></w:r>')
    caption.n[kind] = caption.n.get(kind, 0) + 1
    return ('<w:p><w:pPr><w:pStyle w:val="Caption"/><w:rPr><w:rFonts w:cs="Times New Roman"/></w:rPr></w:pPr>'
            f'<w:r>{rp}<w:t xml:space="preserve">{kind} </w:t></w:r>'
            + fld("STYLEREF 1 \\s", "1")
            + f'<w:r>{rp}<w:t>.</w:t></w:r>'
            + fld(f"SEQ {kind} \\* ARABIC \\s 1", str(caption.n[kind]))
            + f'<w:r>{rp}<w:t xml:space="preserve">: {escape(title)}</w:t></w:r></w:p>')
caption.n = {}

def table(widths, rows):
    total = sum(widths)
    grid = "".join(f'<w:gridCol w:w="{w}"/>' for w in widths)
    out = [f'<w:tbl><w:tblPr><w:tblStyle w:val="TableGrid"/><w:tblW w:w="{total}" w:type="dxa"/>'
           '<w:jc w:val="center"/><w:tblLayout w:type="fixed"/>'
           '<w:tblCellMar><w:left w:w="85" w:type="dxa"/><w:right w:w="85" w:type="dxa"/></w:tblCellMar>'
           f'<w:tblLook w:val="04A0" w:firstRow="1" w:lastRow="0" w:firstColumn="1" w:lastColumn="0" w:noHBand="0" w:noVBand="1"/></w:tblPr><w:tblGrid>{grid}</w:tblGrid>']
    for ri, r in enumerate(rows):
        hdr = ri == 0
        trpr = '<w:trPr><w:tblHeader/><w:cantSplit/></w:trPr>' if hdr else '<w:trPr><w:cantSplit/></w:trPr>'
        cells = []
        for w, c in zip(widths, r):
            shade = '<w:shd w:val="clear" w:color="auto" w:fill="D9E2F3"/>' if hdr else ""
            jc = '<w:jc w:val="center"/>' if hdr else '<w:jc w:val="left"/>'
            ps = []
            for line in c.split("\n"):
                txt = run(line, b=True, sz=24) if hdr else rich(line, sz=24)
                keep = '<w:keepNext/>' if ri < len(rows) - 1 else ''
                ps.append(f'<w:p><w:pPr>{keep}<w:spacing w:before="40" w:after="40" w:line="276" w:lineRule="auto"/>'
                          f'<w:ind w:firstLine="0"/>{jc}</w:pPr>{txt}</w:p>')
            cells.append(f'<w:tc><w:tcPr><w:tcW w:w="{w}" w:type="dxa"/>{shade}<w:vAlign w:val="center"/></w:tcPr>{"".join(ps)}</w:tc>')
        out.append(f"<w:tr>{trpr}{''.join(cells)}</w:tr>")
    out.append("</w:tbl>")
    return "".join(out)

def image(rid, path, width_cm):
    wpx, hpx = Image.open(path).size
    cx = int(width_cm * 360000); cy = int(cx * hpx / wpx)
    return ('<w:p><w:pPr><w:keepNext/><w:spacing w:before="120" w:after="0"/><w:ind w:firstLine="0"/><w:jc w:val="center"/></w:pPr><w:r><w:drawing>'
            f'<wp:inline distT="0" distB="0" distL="0" distR="0"><wp:extent cx="{cx}" cy="{cy}"/>'
            '<wp:docPr id="101" name="Hinh 1.1"/>'
            '<wp:cNvGraphicFramePr><a:graphicFrameLocks xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" noChangeAspect="1"/></wp:cNvGraphicFramePr>'
            '<a:graphic xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">'
            '<pic:pic xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture"><pic:nvPicPr><pic:cNvPr id="101" name="hinh_1_1.png"/><pic:cNvPicPr/></pic:nvPicPr>'
            f'<pic:blipFill><a:blip r:embed="{rid}"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
            f'<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr>'
            '</pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing></w:r></w:p>')

def tcap_keep(xml):  # chú thích bảng nằm trên bảng -> giữ liền với bảng
    return xml.replace('<w:pStyle w:val="Caption"/>', '<w:pStyle w:val="Caption"/><w:keepNext/><w:spacing w:before="120"/>', 1)

# ---------- nội dung ----------
from ch1_content import S11, S12, S13, S14, TABLE_11, TABLE_12, FIG_11_TITLE, TABLE_11_TITLE, TABLE_12_TITLE, S11_AFTER_FIG, S13_AFTER_TABLE

# ảnh
os.makedirs("unpacked/word/media", exist_ok=True)
shutil.copy("hinh_1_1.png", "unpacked/word/media/hinh_1_1.png")
rels_p = "unpacked/word/_rels/document.xml.rels"
rels = open(rels_p, encoding="utf-8").read()
RID = "rId101"
if RID not in rels:
    rels = rels.replace("</Relationships>", f'<Relationship Id="{RID}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/hinh_1_1.png"/></Relationships>')
    open(rels_p, "w", encoding="utf-8").write(rels)
ct_p = "unpacked/[Content_Types].xml"
ct = open(ct_p, encoding="utf-8").read()
if 'Extension="png"' not in ct:
    ct = ct.replace('<Default Extension="xml"', '<Default Extension="png" ContentType="image/png"/><Default Extension="xml"')
    open(ct_p, "w", encoding="utf-8").write(ct)

# namespace wp / r có sẵn trong document.xml?
root = x[:x.find(">", x.find("<w:document")) + 1]
assert "xmlns:wp=" in root and "xmlns:r=" in root, root

# ---------- thay vùng Chương 1 ----------
h1 = x.find('<w:pStyle w:val="Heading1"/>')
p_h11_end = x.find("</w:p>", x.find('w:name="_Toc226397267"')) + 6          # hết tiêu đề 1.1
p_h12_start = x.rfind("<w:p ", 0, x.find('w:name="_Toc226397268"', p_h11_end))
p_h12_end = x.find("</w:p>", p_h12_start) + 6
p_h13_start = x.rfind("<w:p ", 0, x.find('w:name="_Toc226397269"', p_h12_end))
p_h13_end = x.find("</w:p>", p_h13_start) + 6
p_h14_start = x.rfind("<w:p ", 0, x.find('w:name="_Toc226397270"', p_h13_end))
p_h14_end = x.find("</w:p>", p_h14_start) + 6
# đoạn hướng dẫn của mục 1.4 (1 đoạn), phía sau là 3 đoạn trống của mẫu (giữ lại, đoạn cuối chứa sectPr)
p_14_body_end = x.find("</w:p>", p_h14_end) + 6
assert h1 < p_h11_end < p_h12_start < p_h13_start < p_h14_start

keep_bm = '<w:bookmarkStart w:id="2" w:name="_Toc140297269"/><w:bookmarkStart w:id="3" w:name="_Toc142813558"/>'
assert keep_bm in x[p_h11_end:p_h12_start]

sec11 = [para(S11[0], prefix=keep_bm)] + [para(t) for t in S11[1:]]
sec11 += [image(RID, "hinh_1_1.png", 15.5), caption("Hình", FIG_11_TITLE)]
sec11 += [para(t) for t in S11_AFTER_FIG]
sec11 += [tcap_keep(caption("Bảng", TABLE_11_TITLE)), table([1500, 2400, 2500, 2387], TABLE_11), para("", '<w:spacing w:after="0"/>')]

sec12 = [para(t) for t in S12]
sec13 = [para(t) for t in S13]
sec13 += [tcap_keep(caption("Bảng", TABLE_12_TITLE)), table([2300, 6487], TABLE_12), para("", '<w:spacing w:after="0"/>')]
sec13 += [para(t) for t in S13_AFTER_TABLE]
sec14 = [para(t) for t in S14]

new = (x[:p_h11_end] + "".join(sec11)
       + x[p_h12_start:p_h12_end] + "".join(sec12)
       + x[p_h13_start:p_h13_end] + "".join(sec13)
       + x[p_h14_start:p_h14_end] + "".join(sec14)
       + x[p_14_body_end:])
open(D, "w", encoding="utf-8").write(new)
print("done", len(x), "->", len(new))
