# -*- coding: utf-8 -*-
"""Sửa trang trắng sau MỤC LỤC (chạy SAU khi Word đã cập nhật mục lục).
Mục lục kín đúng 2 trang nên 3 đoạn cuối của khối (đoạn kết thúc trường TOC, một đoạn trống, đoạn chứa ngắt section)
bị đẩy sang trang mới, tạo một trang trắng. Cách sửa: chuyển phần kết thúc trường và ngắt section vào dòng cuối
của mục lục rồi bỏ hai đoạn thừa.
python post_fix.py "<tệp .docx>"
"""
import re, sys, zipfile, shutil, os


def fix(x):
    a = x.find('TOC \\o "1-4"'); e = x.find("DANH MỤC HÌNH VẼ")
    seg = x[a:e]
    ps = list(re.finditer(r"<w:p[ >].*?</w:p>", seg, flags=re.S))
    last_toc, p_end, p_empty, p_sect = ps[-4], ps[-3], ps[-2], ps[-1]
    assert 'w:val="TOC' in last_toc.group(0), "khong tim thay dong cuoi muc luc"
    assert 'fldCharType="end"' in p_end.group(0) and "<w:t" not in p_end.group(0)
    assert "<w:t" not in p_empty.group(0) and "sectPr" in p_sect.group(0) and "<w:t" not in p_sect.group(0)
    end_run = re.search(r'<w:r[ >](?:(?!<w:r[ >]).)*?<w:fldChar w:fldCharType="end"/></w:r>', p_end.group(0), flags=re.S).group(0)
    end_run = end_run.replace("<w:lastRenderedPageBreak/>", "")
    sect = re.search(r"<w:sectPr.*?</w:sectPr>", p_sect.group(0), flags=re.S).group(0)
    t = last_toc.group(0)
    t = t.replace("</w:pPr>", sect + "</w:pPr>", 1)
    t = t[:-len("</w:p>")] + end_run + "</w:p>"
    new_seg = seg[:last_toc.start()] + t + seg[p_sect.end():]
    return x[:a] + new_seg + x[e:]


if __name__ == "__main__":
    path = sys.argv[1]; tmp = path + ".tmp"
    with zipfile.ZipFile(path) as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for it in zin.infolist():
            data = zin.read(it.filename)
            if it.filename == "word/document.xml":
                data = fix(data.decode("utf-8")).encode("utf-8")
            zout.writestr(it, data)
    shutil.move(tmp, path); print("da sua", path)
