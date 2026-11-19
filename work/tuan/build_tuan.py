# Tạo báo cáo tuần từ mẫu "3. Báo cáo tuần x.docx", giữ nguyên định dạng mẫu.
# Cú pháp nội dung: **đậm**, {{chỗ cần điền}} (tô vàng).
import re, os, shutil, zipfile, sys
from xml.sax.saxutils import escape

RPR = '<w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:cs="Times New Roman"/>'
SZ = '<w:sz w:val="26"/><w:szCs w:val="26"/>'

def run(t, b=False, hl=False):
    extra = ("<w:b/>" if b else "") + ('<w:highlight w:val="yellow"/>' if hl else "")
    return f'<w:r><w:rPr>{RPR}{extra}{SZ}</w:rPr><w:t xml:space="preserve">{escape(t)}</w:t></w:r>'

def rich(t):
    out = []
    for part in re.split(r"(\*\*.+?\*\*|\{\{.+?\}\})", t):
        if not part: continue
        if part.startswith("**"): out.append(run(part[2:-2], b=True))
        elif part.startswith("{{"): out.append(run("[" + part[2:-2] + "]", hl=True))
        else: out.append(run(part))
    return "".join(out)

def p_sec(t):   # mục đánh số 1., 2., ...
    return (f'<w:p><w:pPr><w:pStyle w:val="ListParagraph"/><w:numPr><w:ilvl w:val="0"/><w:numId w:val="1"/></w:numPr><w:keepNext/>'
            f'<w:spacing w:before="120"/><w:rPr>{RPR}{SZ}</w:rPr></w:pPr>{rich(t)}</w:p>')

def p_text(t):  # đoạn thường dưới mục
    return (f'<w:p><w:pPr><w:pStyle w:val="ListParagraph"/><w:jc w:val="both"/><w:rPr>{RPR}{SZ}</w:rPr></w:pPr>{rich(t)}</w:p>')

def p_bul(t):   # gạch đầu dòng như mẫu
    return (f'<w:p><w:pPr><w:pStyle w:val="ListParagraph"/><w:numPr><w:ilvl w:val="0"/><w:numId w:val="4"/></w:numPr>'
            f'<w:ind w:left="1134" w:hanging="283"/><w:jc w:val="both"/><w:rPr>{RPR}{SZ}</w:rPr></w:pPr>{rich(t)}</w:p>')

KIND = {"sec": p_sec, "text": p_text, "bul": p_bul}

def build(week, items, out):
    shutil.rmtree("u_tmp", ignore_errors=True)
    with zipfile.ZipFile("mau_tuan.docx") as z: z.extractall("u_tmp")
    D = "u_tmp/word/document.xml"
    x = open(D, encoding="utf-8").read()
    # tiêu đề: đổi số tuần
    x = x.replace("TUẦN 1 ĐỒ ÁN", f"TUẦN {week} ĐỒ ÁN", 1) if "TUẦN 1 ĐỒ ÁN" in x else re.sub(r"(TUẦN\s*</w:t>.*?<w:t[^>]*>)\s*1", rf"\g<1>{week}", x, count=1, flags=re.S)
    assert f"TUẦN {week}" in re.sub(r"<[^>]+>", "", x), "không tìm thấy tiêu đề tuần"
    # thay phần sau bảng (giữ đoạn trống ngay sau bảng và sectPr)
    a = x.find("</w:tbl>") + len("</w:tbl>")
    a = x.find("</w:p>", a) + len("</w:p>")          # giữ đoạn trống sau bảng
    b = x.rfind("<w:sectPr")
    body = "".join(KIND[k](t) for k, t in items)
    x = x[:a] + body + x[b:]
    open(D, "w", encoding="utf-8").write(x)
    files = []
    for r, _, fs in os.walk("u_tmp"):
        for f in fs:
            p = os.path.join(r, f); files.append((os.path.relpath(p, "u_tmp").replace(os.sep, "/"), p))
    files.sort(key=lambda t: (t[0] != "[Content_Types].xml", t[0]))
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for arc, p in files: z.write(p, arc)
    shutil.rmtree("u_tmp")
    print("saved", out)

if __name__ == "__main__":
    import noi_dung_tuan as N
    # python build_tuan.py [thư_mục_ra] [tuần ...]   (mặc định: ../.. và tuần 1 2 3)
    out_dir = sys.argv[1] if len(sys.argv) > 1 else "../.."
    weeks = [int(w) for w in sys.argv[2:]] or [1, 2, 3, 4, 5, 6]
    for w in weeks:
        build(w, getattr(N, f"TUAN{w}"), os.path.join(out_dir, f"Bao cao tuan {w}.docx"))
