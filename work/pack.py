import zipfile, os, sys
src, out = sys.argv[1], sys.argv[2]
files = []
for r, _, fs in os.walk(src):
    for f in fs:
        p = os.path.join(r, f); files.append((os.path.relpath(p, src).replace(os.sep, "/"), p))
files.sort(key=lambda t: (t[0] != "[Content_Types].xml", t[0]))
with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
    for a, p in files: z.write(p, a)
print("packed", out)
