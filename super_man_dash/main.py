import pyxel

WIDTH, HEIGHT = 128, 128
TRANSPARENT_COLOR = 12
SCENE_TITLE = 0
SCENE_GAME = 1
SCENE_RESULT = 2
BOY_STATUS_LIVE = 0
BOY_STATUS_DEAD = 1
SCROLL_BORDER_X = 80
GRAVITY = 1
JUMP_VELOCITY = -10
CHECK_POINTS = [
    (-1, -1),
    (16, -1),
    (16, 16),
    (-1, 16),
    (8, -1),
    (16, 8),
    (8, 16),
    (-1, 8),
]

scroll_x = 0
coins = []
enemies = []


def get_tile(x, y):
    return pyxel.tilemap(0).pget(x, y)


def detect_collision(x, y):
    coll_flags = [False, False, False, False, False, False, False, False]
    for i, (px, py) in enumerate(CHECK_POINTS):
        if get_tile((x + px) // 8, (y + py) // 8)[1] == 6:
            coll_flags[i] = True
    return coll_flags


def check_goal(x, y):
    flag = False
    for px, py in CHECK_POINTS:
        if get_tile((x + px) // 8, (y + py) // 8)[1] == 14:
            flag = True
            break
    return flag


def spawn_coin(left_x, right_x):
    left_x = pyxel.ceil(left_x / 8)
    right_x = pyxel.floor(right_x / 8)
    for x in range(left_x, right_x + 1):
        for y in range(16):
            tile = get_tile(x, y)
            if tile == (0, 10):
                coins.append(Coin(x * 8, y * 8))


def spawn_enemy(left_x, right_x):
    left_x = pyxel.ceil(left_x / 8)
    right_x = pyxel.floor(right_x / 8)
    for x in range(left_x, right_x + 1):
        for y in range(16):
            tile = get_tile(x, y)
            if tile == (1, 10):
                enemies.append(Enemy(x * 8, y * 8))


class Coin:
    def __init__(self, x, y, w=16, h=16):
        self.x = x
        self.y = y
        self.w = w
        self.h = h

    def draw(self):
        u = pyxel.frame_count // 3 % 2 * 16
        pyxel.blt(self.x, self.y, 0, u, 64, self.w, self.h, TRANSPARENT_COLOR)


class Boy:
    def __init__(self, x, y, w=16, h=16, score=0):
        self.x, self.y, self.w, self.h, self.score = x, y, w, h, score
        self.v_y, self.status, self.jump_status = 0, BOY_STATUS_LIVE, 1

    def check_coin_collision(self):
        for coin in coins:
            if (
                self.x < coin.x + coin.w
                and self.x + self.w > coin.x
                and self.y < coin.y + coin.h
                and self.y + self.h > coin.y
            ):
                self.score += 1
                pyxel.play(2, 3)
                coins.remove(coin)

    def check_enemy_collision(self):
        for enemy in enemies:
            if (
                self.x < enemy.x + enemy.w
                and self.x + self.w > enemy.x
                and self.y < enemy.y + enemy.h
                and self.y + self.h > enemy.y
            ):
                pyxel.play(3, 4)
                self.status = BOY_STATUS_DEAD

    def update(self):
        global scroll_x
        if self.status != BOY_STATUS_LIVE:
            return
        coll_flags = detect_collision(self.x, self.y)
        if pyxel.btn(pyxel.KEY_LEFT) and self.x > scroll_x and not coll_flags[7]:
            self.x -= 2
        if (
            pyxel.btn(pyxel.KEY_RIGHT)
            and self.x < scroll_x + WIDTH - self.w
            and not coll_flags[5]
        ):
            self.x += 2

        self.v_y += GRAVITY
        new_y = self.y + self.v_y

        if self.v_y > 0:  # Falling
            while self.y < new_y:
                self.y += 1
                coll_flags = detect_collision(self.x, self.y)
                if coll_flags[2] or coll_flags[3]:
                    self.y = (self.y // 8) * 8
                    self.v_y = 0
                    self.jump_status = 0
                    break
        elif self.v_y < 0:  # Jumping
            while self.y > new_y:
                self.y -= 1
                coll_flags = detect_collision(self.x, self.y)
                if coll_flags[0] or coll_flags[1]:
                    self.y = (self.y // 8 + 1) * 8
                    self.v_y = 0
                    break

        if pyxel.btnp(pyxel.KEY_SPACE) and (coll_flags[2] or coll_flags[3]):
            self.v_y = JUMP_VELOCITY  # Jump velocity
            self.jump_status = 1

        self.check_coin_collision()
        self.check_enemy_collision()

        if self.y > 128:
            self.status = BOY_STATUS_DEAD
            pyxel.play(3, 4)

        if self.x > scroll_x + SCROLL_BORDER_X:
            last_scroll_x = scroll_x
            scroll_x = min(self.x - SCROLL_BORDER_X, 240 * 8)
            spawn_coin(last_scroll_x + 128, scroll_x + 127)
            spawn_enemy(last_scroll_x + 128, scroll_x + 127)

    def draw(self):
        u = 3 * 16 if self.jump_status else pyxel.frame_count // 3 % 2 * 16
        pyxel.blt(self.x, self.y, 0, u, 16, self.w, self.h, TRANSPARENT_COLOR)


class Enemy:
    def __init__(self, x, y, w=16, h=16):
        self.x, self.y, self.w, self.h = x, y, w, h
        self.v_y = 0.5

    def update(self):
        self.x -= self.v_y

    def draw(self):
        u = pyxel.frame_count // 6 % 2 * 16
        pyxel.blt(self.x, self.y, 0, u, 88, self.w, self.h, TRANSPARENT_COLOR)


class App:
    def __init__(self):
        pyxel.init(WIDTH, HEIGHT)
        pyxel.load("./scene.pyxres")
        self.scene = SCENE_TITLE
        # BGM
        pyxel.sounds[0].set(
            "e3 e3 e3 c3 e3 g3 g2 "  # Super Mario Bros. theme intro
            "c3 g2 e2 a2 b2 a#2 a2 g2 e3 g3 a3 f3 g3 e3 c3 d3 b2 ", 
            "p", "6", "vffn fnff vffs vfnn", 25,
        )
        
        pyxel.sounds[1].set(
            "c3 c4 a2 a3 a#2 a3 g2 e3 g3 a3 f3 g3 e3 c3 d3 b2 "  # Super Mario Bros. theme continuation
            "c3 g2 e2 a2 b2 a#2 a2 g2 e3 g3 a3 f3 g3 e3 c3 d3 b2 ",
            "s", "6", "nnff vfff vvvv vfff svff vfff vvvv svnn", 25,
        )
        pyxel.sounds[2].set(
            "f0ra4r f0ra4r f0ra4r f0f0a4r", "n", "6622 6622 6622 6422", "f", 25
        )
        # コイン
        pyxel.sounds[3].set(
            "c3e3g3e4g4", # ノート（音の高さ）
            "t", # トーン（音色）
            "6", # ボリューム
            "f", # エフェクト（フェードイン）
            5 # スピード
        )
        # ゲームオーバーの効果音
        pyxel.sounds[4].set(
            "g2f2e2d2c2", # ノート（音の高さ）
            "t", # トーン（音色）
            "76543", # ボリューム
            "fffnn", # エフェクト（n=ノーマル、f=ファーストディケイ）
            10 # スピード
        )
        # 成功時の効果音
        pyxel.sounds[5].set(
            "c3e3g3c4e4", # ノート（音の高さ）
            "p", # トーン（音色）
            "66443", # ボリューム
            "nnffn", # エフェクト（n=ノーマル、f=ファーストディケイ）
            10 # スピード
        )
        # 失敗時の効果音
        pyxel.sounds[6].set(
            "g2f2e2d2c2", # ノート（音の高さ）
            "t", # トーン（音色）
            "76543", # ボリューム
            "fffnn", # エフェクト（n=ノーマル、f=ファーストディケイ）
            10 # スピード
        )
        pyxel.play(1, 2, loop=True)
        self.game_settings()

    def game_settings(self):
        pyxel.image(0).rect(0, 80, 16, 8, TRANSPARENT_COLOR)
        self.boy = Boy(0, 0)
        spawn_coin(0, 127)
        spawn_enemy(0, 127)
        pyxel.run(self.update, self.draw)

    def game_over(self):
        self.scene = SCENE_RESULT

    def clean_game_scene(self):
        global enemies, coins, scroll_x
        self.boy = None
        enemies = []
        coins = []
        scroll_x = 0

    def restart_game(self):
        self.boy = Boy(0, 0)

    def update_title_scene(self):
        if pyxel.btnp(pyxel.KEY_SPACE):
            self.scene = SCENE_GAME
            self.clean_game_scene()
            pyxel.stop(1)
            pyxel.play(0, [0, 1], loop=True)
            self.game_settings()

    def update_game_scene(self):
        if self.boy.status == BOY_STATUS_LIVE:
            self.boy.update()
            for enemy in enemies:
                enemy.update()
            if check_goal(self.boy.x, self.boy.y):
                self.scene = SCENE_RESULT
                pyxel.play(3, 5)
                pyxel.stop(0)
                pyxel.play(1, 2, loop=True)
        elif self.boy.status == BOY_STATUS_DEAD:
            self.game_over()
            pyxel.stop(0)
            pyxel.play(1, 2, loop=True)

    def update_result(self):
        if pyxel.btnp(pyxel.KEY_SPACE):
            self.scene = SCENE_GAME
            self.clean_game_scene()
            pyxel.stop(1)
            pyxel.play(0, [0, 1], loop=True)
            self.game_settings()
        elif pyxel.btnp(pyxel.KEY_R):
            self.scene = SCENE_TITLE

    def update(self):
        if self.scene == SCENE_TITLE:
            self.update_title_scene()
        elif self.scene == SCENE_GAME:
            self.update_game_scene()
        elif self.scene == SCENE_RESULT:
            self.update_result()

    def draw_title_scene(self):
        pyxel.text(scroll_x + 36, 40, "SUPER MAN DASH", 7)
        pyxel.text(scroll_x + 32, 80, "- START[SPACE] -", 7)

    def draw_game_scene(self):
        if self.boy.status == BOY_STATUS_LIVE:
            pyxel.camera()
            pyxel.bltm(0, 0, 0, scroll_x, 0, WIDTH, HEIGHT)
            pyxel.camera(scroll_x, 0)
            self.boy.draw()
        for coin in coins:
            coin.draw()
        for enemy in enemies:
            enemy.draw()
        score_text = "Score:{:>4}".format(self.boy.score)
        pyxel.text(scroll_x + 5, 4, score_text, 7)

    def draw_result(self):
        score_text = "Score:{:>4}".format(self.boy.score)
        pyxel.text(scroll_x + 5, 4, score_text, 7)
        if self.boy.status == BOY_STATUS_LIVE:
            pyxel.text(scroll_x + 36, 40, "YOU SUCCESSED", 7)
        else:
            pyxel.text(scroll_x + 36, 40, "YOU FAILED", 7)
        pyxel.text(scroll_x + 32, 60, "- RESTART[R] -", 7)
        pyxel.text(scroll_x + 32, 80, "- RETURN[SPACE] -", 7)

    def draw(self):
        pyxel.cls(0)
        if self.scene == SCENE_TITLE:
            self.draw_title_scene()
        elif self.scene == SCENE_GAME:
            self.draw_game_scene()
        elif self.scene == SCENE_RESULT:
            self.draw_result()


App()
