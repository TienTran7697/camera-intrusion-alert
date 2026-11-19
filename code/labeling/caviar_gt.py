"""Đọc nhãn gốc CAVIAR (*gt.xml): trả về {id: [(frame, xc, yc, w, h), ...]}"""
import glob, os, xml.etree.ElementTree as ET

def load_tracks(video_dir):
    x = glob.glob(os.path.join(video_dir, "*gt.xml"))[0]
    tracks = {}
    for fr in ET.parse(x).getroot().findall("frame"):
        n = int(fr.get("number"))
        for o in fr.iter("object"):
            b = o.find("box")
            tracks.setdefault(int(o.get("id")), []).append(
                (n, float(b.get("xc")), float(b.get("yc")), float(b.get("w")), float(b.get("h"))))
    return tracks
