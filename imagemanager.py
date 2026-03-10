import gzip
from pyxel import Image
from hashlib import sha256
from struct import pack, unpack
from .filemanager import check_file, write_bin, read_bin


def convert_bmp(filename: str) -> bool:
    """指定された画像ファイルに画像サイズとハッシュを付けてgzip保存する"""
    # ファイル存在チェック
    filepath = check_file(filename, "r")
    if not filepath:
        return False

    # 1. いったん普通にBMPを読み込む
    img = Image.from_image(filename)
    # 2. Pyxelのメモリから「純粋なピクセルデータ」をbytesとして取り出す
    pixel_data = img.data_ptr()
    raw_pixel_data = bytes(pixel_data)
    # 3. 展開時に利用する画像サイズ情報を付与してピクセルデータを圧縮する
    sizeheader = pack("!HH", img.width, img.height)
    compressed = gzip.compress(sizeheader + raw_pixel_data)
    # 4. ハッシュ計算
    hash_value = sha256(compressed).digest()
    # 5. データファイルの出力
    writepath = check_file(filepath.with_suffix(".bdt"), "w")
    if not writepath:
        return False
    write_bin(writepath, hash_value + compressed)

    return True


def load_dat_bmp(filename: str) -> Image | None:
    """変換済ビットマップファイルを読み込んでImageオブジェクトを生成"""
    # ファイル存在チェック
    filepath = check_file(filename, "r")
    if not filepath:
        return None

    # データファイル読込
    bin_data = read_bin(filepath)
    # ハッシュデータと分離
    hash_value = bin_data[:32]  # SHA-256ハッシュ（32バイト）
    compressed = bin_data[32:]
    # ハッシュチェック
    if sha256(compressed).digest() != hash_value:  # ハッシュ一致
        return None

    # 復元処理
    decompressed = gzip.decompress(compressed)
    sizeheader = decompressed[:4]
    raw_pixel_data = decompressed[4:]
    img_width, img_height = unpack("!HH", sizeheader)

    pixel_image = Image(img_width, img_height)
    pixel_data = pixel_image.data_ptr()
    pixel_data[:] = raw_pixel_data

    return pixel_image
