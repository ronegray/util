import pyxel as px
import gzip
from pathlib import Path
from hashlib import sha256
from .filemanager import check_file, read_json, write_bin


# jsonファイルの暗号圧縮
def encrypt_json(filename):
    path = check_file(filename, "r")
    if not path:
        return

    data = read_json(path)
    compressed = gzip.compress(data)
    hash_value = sha256(compressed).digest()
    writepath = check_file(path.with_suffix(".jbn"), "w")
    if not writepath:
        return False
    write_bin(writepath, hash_value + compressed)


# 暗号圧縮
if __name__ == "__main__":
    px.init(120, 120, title="common")

    dir_path = Path.cwd()
    for json_fullpath in dir_path.rglob("*.json"):
        print(json_fullpath)

    [encrypt_json(json_fullpath) for json_fullpath in dir_path.rglob("*.json")]

    px.text(0, 0, "encrypt finished. ", px.COLOR_WHITE)
    px.text(0, 10, "press ESC key", px.COLOR_WHITE)
    px.show()
