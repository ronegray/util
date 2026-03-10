from enum import Enum, auto
from typing import Literal
from dataclasses import dataclass
import pyxel as px

# import .inputmanager as inp
from . import inputmanager as inp
import os

WindowMode = Literal["once", "wait", "page", "menu"]
FontSizeName = Literal["small", "basic", "large"]
MenuWindowName = Literal["main", "popup"]


class WindowAction(Enum):
    """メニュー／ウインドウ操作時の応答リスト"""

    CONTINUE = auto()  # 継続
    CLOSE = auto()  # 一つ戻る (pop)
    DISCARD = auto()  # 全て破棄して閉じる (初期化)
    EXECUTE = (
        auto()
    )  # 選択処理を実行（新しいメニューを開く等。メニューのインスタンスを添えても良い）


@dataclass
class FontData:
    name: FontSizeName  # サイズ名
    font: px.Font  # フォントオブジェクト
    height: int = 6  # フォントの高さ


class WindowManager:
    def __init__(self):
        """Window/Menuインスタンス管理クラス"""
        self.stacks: list[Window | Menu] = []
        self.image_chips: px.Image = px.Image.from_image("assets/image/chip_window.bmp")
        # self.fonts: dict[FontSize, px.Font] = {}
        # self.font_heights: dict[FontSize, int] = {}
        self.fontdata: dict[FontSizeName, FontData] = {}
        self.set_fontdata()

    def set_fontdata(self):
        """フォント情報を設定(BDFフォントの場合はフォントファイルのSIZEを取得)"""
        font_file_name: dict[FontSizeName, str] = {
            "small": "k6x8_gothic.bdf",
            "basic": "misaki_gothic.bdf",
            "large": "umplus_j12r.bdf",
        }
        for size_name, file_name in font_file_name.items():
            # self.fontdata[size_name].name = size_name
            # self.fontdata[size_name].font = px.Font(f"assets/font/{file_name}")
            if file_name.endswith(".bdf"):
                print(os.getcwd())
                with open(f"assets/font/{file_name}", mode="r", encoding="utf-8") as f:
                    data = f.readline()
                    while data.find("SIZE") == -1:
                        data = f.readline()
                    # self.font_heights[size_name] = int(data.split(" ")[1])
                    # self.fontdata[size_name].height = int(data.split(" ")[1])
                tmpdata = FontData(
                    size_name,
                    px.Font(f"assets/font/{file_name}"),
                    int(data.split(" ")[1]),
                )
                self.fontdata[size_name] = tmpdata
            else:
                match size_name:
                    case "small":
                        self.fontdata[size_name].height = 8
                    case "basic":
                        self.fontdata[size_name].height = 9
                    case "large":
                        self.fontdata[size_name].height = 13

    def get_fontdata(self, size_name: FontSizeName) -> FontData:
        """フォント"""
        return self.fontdata[size_name]

    def push_stack(self, class_name, font_size_name: FontSizeName, *args, **kwargs):
        """指定クラスのインスタンスをスタックに追加"""
        instance = class_name(font_size_name, *args, **kwargs)
        self.stacks.append(instance)

    def pop_stack(self):
        """スタック末尾のインスタンスを削除"""
        self.stacks.pop()

    def update(self):
        """管理クラス配下のインスタンス更新およびインスタンス応答の処理"""
        if len(self.stacks):
            action = self.stacks[-1].update()
            match action:
                case WindowAction.CLOSE:
                    self.pop_stack()
                case WindowAction.DISCARD:
                    self.stacks.clear()
                case WindowAction.EXECUTE:
                    # 基本的にEXECUTEを返すのはMenuのみだが念の為
                    if isinstance(self.stacks[-1], Menu):
                        self.stacks[-1].exec_menu()

    def draw(self):
        """管理クラス配下のインスタンスをスタックの奥から順に描画"""
        if len(self.stacks):
            for window in self.stacks:
                window.draw()
                if isinstance(window, Window):
                    window.draw_message()


"""モジュールシングルトンインスタンスの生成"""
window_manager = WindowManager()


class Window:
    chip_size = 8

    def __init__(
        self,
        font_size_name: FontSizeName,
        x: int,
        y: int,
        width: int,
        height: int,
        window_mode: WindowMode,
        wait_sec: float = 5.0,
    ):
        """汎用ウインドウクラス"""
        # 管理クラスへの参照
        self.chip = window_manager.image_chips
        self.fontdata = window_manager.get_fontdata(font_size_name)
        self.font = self.fontdata.font
        # 共通基本パラメータ
        self.x = (
            x if x + width <= px.width else px.width - width
        )  # 右端からはみ出す場合を考慮
        self.y = y
        self.width = width
        self.height = height
        # クラス個別パラメータ
        self.window_mode = window_mode
        self.wait_frame = px.ceil(wait_sec * 30)
        self.frame_counter = 0
        self.text_list = []
        self.window_image = px.Image(self.width, self.height)

        self.chip_cnt_w = self.width // self.chip_size
        self.chip_cnt_h = self.height // self.chip_size
        # ウインドウイメージ生成処理
        self.generate_window()

    def generate_window(self):
        """ウインドウイメージを生成（self.window_imageとして保持）"""
        chip_wxh = [self.chip_size, self.chip_size]
        lefttop = [0, 0] + chip_wxh
        righttop = [8, 0] + chip_wxh
        leftbottom = [0, 8] + chip_wxh
        rightbottom = [8, 8] + chip_wxh
        left = [0, 16] + chip_wxh
        right = [8, 16] + chip_wxh
        top = [0, 24] + chip_wxh
        bottom = [8, 24] + chip_wxh
        # 枠線
        for Ypos in range(self.chip_cnt_h):
            for Xpos in range(self.chip_cnt_w):
                # 四隅
                if Ypos == 0 and Xpos == 0:
                    self.window_image.blt(0, 0, self.chip, *lefttop, colkey=0)  # 左上
                elif Ypos == 0 and Xpos == self.chip_cnt_w - 1:
                    self.window_image.blt(
                        self.width - self.chip_size, 0, self.chip, *righttop, colkey=0
                    )  # 右上
                elif Ypos == self.chip_cnt_h - 1 and Xpos == 0:
                    self.window_image.blt(
                        0,
                        self.height - self.chip_size,
                        self.chip,
                        *leftbottom,
                        colkey=0,
                    )  # 左下
                elif Ypos == self.chip_cnt_h - 1 and Xpos == self.chip_cnt_w - 1:
                    self.window_image.blt(
                        self.width - self.chip_size,
                        self.height - self.chip_size,
                        self.chip,
                        *rightbottom,
                        colkey=0,
                    )  # 右下
                # 枠線
                elif Ypos == 0:  # 上端
                    self.window_image.blt(
                        (Xpos * self.chip_size), Ypos, self.chip, *top, colkey=0
                    )
                elif Xpos == 0:  # 左端
                    self.window_image.blt(
                        Xpos, (Ypos * self.chip_size), self.chip, *left, colkey=0
                    )
                elif Ypos == self.chip_cnt_h - 1:  # 下端
                    self.window_image.blt(
                        (Xpos * self.chip_size),
                        self.height - self.chip_size,
                        self.chip,
                        *bottom,
                        colkey=0,
                    )
                elif Xpos == self.chip_cnt_w - 1:  # 右端
                    self.window_image.blt(
                        self.width - self.chip_size,
                        (Ypos * self.chip_size),
                        self.chip,
                        *right,
                        colkey=0,
                    )
        # 塗りつぶし
        # px.blt(self.x + (Xpos*G_.CHIP_PIXEL), self.y + (Ypos*G_.CHIP_PIXEL), G_.IMGIDX["CHIP"],
        #         32, 240, G_.CHIP_PIXEL,G_.CHIP_PIXEL )
        self.window_image.rect(
            self.chip_size,
            self.chip_size,
            self.width - (self.chip_size * 2),
            self.height - (self.chip_size * 2),
            self.chip.pget(7, 7),
        )

    def update(self):
        self.frame_counter += 1
        # menuモードのウインドウは基本的にupdateを実行しないが念の為
        if self.window_mode == "menu":
            return
        # waitモード時は待機フレーム数が過ぎると全終了
        if self.window_mode == "wait" and self.frame_counter <= self.wait_frame:
            return WindowAction.DISCARD
        # waitモード時は待機フレーム数の半分を過ぎるまでキー入力を受け付けない
        if self.window_mode == "wait" and self.frame_counter <= self.wait_frame // 2:
            return WindowAction.CONTINUE

        # 決定またはキャンセルキー処理
        if inp.is_pressed("decide", "once") or inp.is_pressed("cancel", "once"):
            match self.window_mode:
                # ページ送り以外では全終了
                case "once" | "wait":
                    return WindowAction.DISCARD
                # ページ送り時は内部テキストリストを次に進める
                case "page":
                    self.text_list.pop(0)
                    # 最終メッセージを送った後は全終了
                    if len(self.text_list):
                        return WindowAction.CONTINUE
                    else:
                        return WindowAction.DISCARD

    def draw(self):
        # ウインドウ描画
        px.blt(
            self.x,
            self.y,
            self.window_image,
            0,
            0,
            self.width,
            self.height,
            colkey=px.COLOR_BLACK,
        )
        # ボタン押下アイコン
        if self.frame_counter >= self.wait_frame // 2:
            if px.frame_count // 8 % 2 == 0:
                px.blt(
                    self.x + self.width // 2 - 4,
                    self.y + self.height - 5,
                    self.chip,
                    35,
                    248,
                    5,
                    8,
                    colkey=0,
                    rotate=90,
                )

    def drawText(self, x: int, y: int, text_list: list):
        for i, text in enumerate(text_list):
            px.text(x, y + (i * 16 + 2), text, px.COLOR_WHITE, font=self.font)
        return

    def drawTextColor(self, x: int, y: int, text_list: list):
        for i, data in enumerate(text_list):
            px.text(x, y + (i * 16 + 2), data[0], data[1], font=self.font)
        return

    def add_message(self, message_text):
        if self.window_mode == "menu":
            return
        self.text_list.append(message_text)
        while len(self.text_list) > 3:
            self.text_list.pop(0)

    def draw_message(self):
        for i, text in enumerate(self.text_list):
            px.text(
                self.x + 8,
                self.y + 8 + (i * 16 + 2),
                text,
                px.COLOR_WHITE,
                font=self.font,
            )
        return


class Menu:
    def __init__(
        self,
        font_size_name: FontSizeName,
        x: int,
        y: int,  # width: int, height: int,
        menu_shape: list[int],
        menu_items: list[str],
    ):
        # self, image_chips: px.Image, x: int, y: int, font_name):
        """基底メニュークラス"""
        # 管理クラスへの参照
        self.chip = window_manager.image_chips
        self.img_cursor = [16, 0, Window.chip_size, Window.chip_size]
        self.fontdata = window_manager.get_fontdata(font_size_name)
        self.font = self.fontdata.font
        self.cursor_row_offset = px.ceil((self.fontdata.height - Window.chip_size) / 2)
        # クラス個別パラメータ
        self.cursor_position: list[int] = [0, 0]
        self.menu_shape: list = menu_shape  # 横軸数,縦軸数
        self.menu_items: list = menu_items  # 横軸テキスト[a,b,c],,,※縦軸数分
        # 共通基本パラメータ
        (
            width,
            height,
        ) = self.calculate_windowsize()  # フォントサイズを元にウインドウサイズ算出
        adjusted_x = (
            x if x + width <= px.width else px.width - width
        )  # 右端からはみ出す場合を考慮
        # ウインドウ生成処理
        self.windows: dict[MenuWindowName, Window] = {}
        self.windows["main"] = Window(
            font_size_name, adjusted_x, y, width, height, "menu"
        )

    def calculate_windowsize(self) -> list[int]:
        """メニューウインドウの幅／高さの算出と、描画アドレスのキャッシュ"""
        menuwidth = menuheight = 0
        framesize = Window.chip_size * 2  # 左右または上下の枠サイズ合計
        # --- 幅(X座標)の計算と保持 ---
        offset_cursor = Window.chip_size + (
            Window.chip_size // 4
        )  # カーソルサイズ、文字との余白
        offset_sepalete_col = self.font.text_width(" ") // 2  # 項目間余白

        # 文字列／カーソル表示用のpixelアドレスキャッシュ初期化
        self.column_x_pos: list[int] = []
        current_x = Window.chip_size  # 描画初期アドレスを枠のすぐ右に定義

        column_items = [list(col) for col in zip(*self.menu_items)]
        for column_text in column_items:
            # 現在のカラムのX座標を記録
            self.column_x_pos.append(current_x)

            max_column_textlen = self.font.text_width(
                max(column_text, key=self.font.text_width)
            )
            menuwidth += offset_cursor + max_column_textlen + offset_sepalete_col
            current_x += menuwidth

        # チップサイズで丸めて最終的な幅を算出
        menuwidth = (
            px.ceil((menuwidth + framesize) / Window.chip_size) * Window.chip_size
        )
        # menuwidth = px.ceil((current_x - offset_sepalete_col + Window.chip_size) / Window.chip_size) * Window.chip_size

        # 高さ
        rows = self.menu_shape[1]
        offset_sepalete_row = self.fontdata.height // 2
        # 文字列／カーソル表示用のpixelアドレスキャッシュ初期化
        self.row_y_pos: list[int] = []
        current_y = Window.chip_size - 1  # 描画初期アドレスを枠の下(余白埋め気味)に定義

        for _ in range(rows):
            self.row_y_pos.append(current_y)
            current_y += self.fontdata.height + offset_sepalete_row

        # 最終行はオフセット不要（枠の余白が相当するため
        menuheight = (
            rows * (self.fontdata.height + offset_sepalete_row) - offset_sepalete_row
        )
        # チップサイズで丸めて最終的な幅を算出
        menuheight = (
            px.ceil((menuheight + framesize) / Window.chip_size) * Window.chip_size
        )

        return [menuwidth, menuheight]

    def update_menu_size(self, menu_items: list | None = None):
        """メニュー項目の変化に合わせたウインドウサイズの変更"""
        if menu_items:
            self.menu_items = menu_items
        self.menu_shape = [len(self.menu_items), len(self.menu_items[0])]
        self.calculate_windowsize()

    def update(self):
        """更新"""
        RC = self.key_check()
        return RC

    def key_check(self):
        """キー入力の確認と応答"""
        if self.move_cursor():
            return WindowAction.CONTINUE
        if inp.is_pressed("decide"):
            return WindowAction.EXECUTE
        if inp.is_pressed("cancel"):
            return WindowAction.CLOSE
        if self.individual_key_check():
            pass

    def individual_key_check(self):
        """メニュー個別のキー判定用"""
        pass

    def move_cursor(self) -> bool:
        """キー入力に応じたカーソル移動とインデックス制御"""
        if inp.is_pressed("up", "hold"):
            self.cursor_position[1] = (self.cursor_position[1] - 1) % self.menu_shape[1]
            return True
        if inp.is_pressed("left", "hold"):
            self.cursor_position[0] = (self.cursor_position[0] - 1) % self.menu_shape[0]
            return True
        if inp.is_pressed("down", "hold"):
            self.cursor_position[1] = (self.cursor_position[1] + 1) % self.menu_shape[1]
            return True
        if inp.is_pressed("right", "hold"):
            self.cursor_position[0] = (self.cursor_position[0] + 1) % self.menu_shape[0]
            return True
        return False

    def exec_menu(self):
        """メニュー個別の処理実行用"""
        if self.cursor_position == [0, 0]:
            window_manager.push_stack(
                Window,
                "large",
                self.windows["main"].x + 16,
                self.windows["main"].y + 16,
                px.width // 2,
                px.height // 8,
                "once",
            )
            window_manager.stacks[-1].text_list = ["menuテスト"]
        elif self.cursor_position == [0, 1]:
            window_manager.push_stack(
                Menu,
                "small",
                self.windows["main"].x + 16,
                self.windows["main"].y + 16,
                [1, 2],
                [["縦１"], ["縦２"]],
            )
        elif self.cursor_position == [1, 1]:
            window_manager.push_stack(
                Menu,
                "basic",
                self.windows["main"].x + 16,
                self.windows["main"].y + 16,
                [2, 1],
                [["横１", "横２"]],
            )
        elif self.cursor_position == [1, 0]:
            window_manager.push_stack(
                Menu,
                "large",
                self.windows["main"].x + 16,
                self.windows["main"].y + 16,
                [2, 3],
                [["横１", "横２"], ["横１", "横２"], ["横１", "横２"]],
            )

    def draw(self):
        """描画"""
        for name, win in self.windows.items():
            win.draw()
            if name == "main":
                self.draw_main()

    def draw_main(self):
        """メニュー項目文字表示"""
        # for row in range(self.menu_shape[1]):
        #     for col in range(self.menu_shape[0]):
        #         # for i,_str in enumerate(self.menu_items[row][col]):

        #         #     px.text(self.windows["main"].x+(1+((1+1)*col+(self.menutext_length*2)*col)+(1+1+i*2))*G_.CHIP_PIXEL,
        #         #             self.menu_window.y+(1 + row*2)*G_.CHIP_PIXEL,
        #         #             _str, px.COLOR_WHITE, G_.JP_FONT)
        for row_idx, row in enumerate(self.menu_items):
            for col_idx, text in enumerate(row):
                text_x = (
                    self.windows["main"].x
                    + self.column_x_pos[col_idx]
                    + Window.chip_size
                )  # カーソルの右隣
                text_y = self.windows["main"].y + self.row_y_pos[row_idx]
                px.text(text_x, text_y, text, px.COLOR_WHITE, self.font)
        self.draw_cursor()

    def draw_cursor(self):
        """メニューカーソル表示"""
        # self.cursor_address = [self.menu_window.x +
        #                        #メニュー枠+余白+(カーソル位置(項目n番目)ｘ項目長x2)*チップサイズ(8)
        #                        (1+(((1)*(self.cursor_position[0]+1)+self.cursor_position[0]+(self.menutext_length*2)*self.cursor_position[0])))
        #                        *G_.CHIP_PIXEL - 2,
        #                        self.menu_window.y +
        #                        (1+(1+(self.cursor_position[1]*2)))*G_.CHIP_PIXEL - 5]
        # px.blt(*self.cursor_address, G_.IMGIDX["CHIP"], 32,248, G_.CHIP_PIXEL,G_.CHIP_PIXEL, colkey=0)
        pos_x, pos_y = self.cursor_position
        cursor_x = self.windows["main"].x + self.column_x_pos[pos_x]
        cursor_y = (
            self.windows["main"].y + self.row_y_pos[pos_y] + self.cursor_row_offset
        )
        px.blt(cursor_x, cursor_y, self.chip, *self.img_cursor, colkey=px.COLOR_BLACK)


# class MenuYesNo(Menu):
#     def __init__(self, x, y, msg:list, command_instance, parent):
#         super().__init__(x + 2*G_.CHIP_PIXEL, y + (len(msg)*2+1)*G_.CHIP_PIXEL , [1,2],  [["はい"],["いいえ"]], 4, 3)
#         self.address = [x,y]
#         _textlength = 0
#         for texts in msg:
#             _textlength = max(len(texts),_textlength)
#         _msg_window_width = (_textlength*2+2)*G_.CHIP_PIXEL
#         if x + _msg_window_width > px.width:
#             x = px.width - _msg_window_width
#         self.message_window  = Window(x, y, _msg_window_width, (len(msg)*2+2)*G_.CHIP_PIXEL, 0)
#         self.message = msg
#         self.command_instance     = command_instance
#         self.parent = parent

#     def update(self):
#         if self.is_command:
#             return self.chkCmdRtn()
#         btn = comf.get_button_state()
#         if btn["a"]:
#             px.play(3,G_.SNDEFX["pi"], resume=True)
#             match self.cursor_position[1] % self.menu_shape[1]:
#                 case 0:
#                     self.command_instance.exec()
#                     self.is_command = True
#                 case 1:
#                     return False
#             return True
#         if btn["b"]:
#             if self.is_command:
#                 return True
#             else:
#                 return False

#         self.moveCursor()
#         return True

#     def draw(self):
#         if self.is_command:
#             self.command_instance.draw()
#         else:
#             self.message_window.draw()
#             self.message_window.drawText(self.address[0]+8,self.address[1]+8, self.message)
#             self.drawMenu()
