"""soundmanager.py
サウンド機能関連
依存：customtone.py

- pyxel基本channel・toneの拡張
- mml楽譜ファイルの読み込み（json形式、1ch=1要素）
"""
from pyxel import (
    tones as px_tones,
    Channel,
    channels as px_channels,
    sounds as px_sounds,
    musics as px_musics,
    # play as px_play,
    playm as px_playm,
    stop as px_stop,
)
from . import customtone
from .filemanager import check_file, read_json  # , read_bin


_music_list: dict[str, str] = {}  # 利用シーンID:曲名（＝ファイル名）
_now_bgm: int = 0  # BGM再生するMusic番号（クロスフェードで入れ替わる）
custom_tones: list[customtone.CustomTone] = []


def init(channel_num: int = 8, tone_num: int = 24):
    global _music_list, custom_tones
    # pyxel.channelsリストの再定義
    channel_list = []
    for _ in range(channel_num):
        channel = Channel()
        channel.gain = 0.95 / channel_num
        channel.detune = 0
        channel_list.append(channel)
    px_channels[0:channel_num] = channel_list

    # pyxel.tonesリストの再定義とカスタムトーン定義
    tone_list = []
    for i in range(tone_num):
        # カスタムトーン生成
        custom_tone = customtone.CustomTone()
        custom_tones.append(custom_tone)
        # カスタムトーン内のトーンオブジェクトを取得
        tone = custom_tone.get_parameter("tone")
        if i < len(px_tones):
            tone = px_tones[i]  # 標準トーン0～3は確保しておく
        tone_list.append(tone)
    px_tones[0:tone_num] = tone_list

    # 楽曲リストのロード {scene_id(int):filename(str)}
    music_list = "musiclist.json"
    path = check_file(music_list)
    if path:
        _music_list = read_json(path)


def fadeout():
    pass


def fadein():
    pass


def load_bgm(scene_id: int):
    """指定シーンIDのBGMをロードして再生"""
    px_stop()
    score_name = _get_score_name(scene_id)
    if score_name:
        _load_score(score_name)
    px_playm(_now_bgm, loop=True)


def _get_score_name(scene_id: int) -> str | None:
    """シーンIDを元にミュージックリストからBGMファイル名を取得"""
    global _music_list
    return _music_list.get(str(scene_id))


def _load_score(score_name: str):
    """MML楽譜ファイルの読み込み"""
    global _now_bgm
    path = check_file(score_name)
    if not path:
        raise FileNotFoundError
    score_data = read_json(path)

    for i, [mml, tonefile] in enumerate(score_data):
        px_sounds[i + (_now_bgm * 8)].mml = mml
        if tonefile:
            custom_tones[i + 4].load_parameter(tonefile)
    _build_music()


def _build_music():
    """８チャンネル分のサウンドを対象にミュージックデータを生成"""
    global _now_bgm
    trackset: list = [[i] for i in range(len(px_channels) + (_now_bgm * 8))]
    px_musics[_now_bgm].set(trackset)
    _now_bgm = abs(_now_bgm - 1)
