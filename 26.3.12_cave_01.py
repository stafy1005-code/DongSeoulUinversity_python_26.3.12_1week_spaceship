import os
import sys
import json
from random import randint

import pygame
from pygame.locals import QUIT, Rect, K_UP, K_DOWN, K_LEFT, K_RIGHT, K_ESCAPE, K_r, K_BACKSPACE, K_RETURN

pygame.init()

WIDTH, HEIGHT = 800, 600
SURFACE = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("우주선 탄막게임")
FPSCLOCK = pygame.time.Clock()

BASE_DIR = r"D:\2112059\26.3.12 우주선 탄막게임"
RANKING_FILE = os.path.join(BASE_DIR, "ranking.json")
FONT_PATH = r"C:\Windows\Fonts\malgun.ttf"


def load_rankings():
    if not os.path.exists(RANKING_FILE):
        return []
    try:
        with open(RANKING_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            result = []
            for item in data:
                if isinstance(item, dict):
                    name = str(item.get("name", "PLAYER"))[:12]
                    score = int(item.get("score", 0))
                    result.append({"name": name, "score": score})
                else:
                    result.append({"name": "PLAYER", "score": int(item)})
            return result
    except Exception:
        pass
    return []


def save_rankings(rankings):
    try:
        with open(RANKING_FILE, "w", encoding="utf-8") as f:
            json.dump(rankings[:5], f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def update_rankings(name, score, rankings):
    safe_name = (name.strip() or "PLAYER")[:12]
    rankings.append({"name": safe_name, "score": int(score)})
    rankings = sorted(rankings, key=lambda x: x["score"], reverse=True)[:5]
    save_rankings(rankings)
    return rankings


def create_holes(walls=80):
    holes = []
    for xpos in range(walls):
        holes.append(Rect(xpos * 10, 100, 10, 400))
    return holes


def reset_game():
    return {
        "walls": 80,
        "ship_x": 50.0,
        "ship_y": 250.0,
        "score": 0,
        "slope": randint(1, 6),
        "game_over": False,
        "paused": False,
        "show_help": False,
        "asking_name": False,
        "player_name": "",
        "ranking_saved": False,
        "gravity": 0.8,
        "move_speed": 12,
        "holes": create_holes(80),
        "enemies": [],
        "enemy_spawn_timer": 0,
        "enemy_spawn_interval": randint(20, 40),
        "bullets": [],
        "bullet_timer": 0,
    }


def draw_button(surface, rect, text, font, bg_color, text_color=(255, 255, 255)):
    pygame.draw.rect(surface, bg_color, rect, border_radius=8)
    label = font.render(text, True, text_color)
    label_rect = label.get_rect(center=rect.center)
    surface.blit(label, label_rect)


def draw_help_popup(surface, title_font, help_font, close_button):
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 150))
    surface.blit(overlay, (0, 0))

    popup_rect = Rect(110, 90, 580, 390)
    pygame.draw.rect(surface, (30, 30, 50), popup_rect, border_radius=16)
    pygame.draw.rect(surface, (220, 220, 255), popup_rect, width=3, border_radius=16)

    title = title_font.render("게임방법", True, (255, 255, 255))
    surface.blit(title, (popup_rect.x + 220, popup_rect.y + 20))

    lines = [
        "1. 방향키로 우주선을 이동합니다.",
        "2. 중앙 배경 구역 안에 있으면 안전합니다.",
        "3. 바깥 배경 구역에 닿으면 게임오버입니다.",
        "4. 우주선은 자동으로 오른쪽으로 공격합니다.",
        "5. 공격이 적에게 맞으면 적이 사라지고 +100점입니다.",
        "6. 적과 충돌해도 게임오버입니다.",
        "7. ESC : 일시정지 / 해제",
        "8. R : 즉시 리셋",
        "9. Pause / Reset / 게임방법 버튼은 마우스로 누를 수 있습니다.",
    ]

    for i, line in enumerate(lines):
        text = help_font.render(line, True, (240, 240, 240))
        surface.blit(text, (popup_rect.x + 24, popup_rect.y + 85 + i * 26))

    draw_button(surface, close_button, "닫기", help_font, (70, 140, 220))


def draw_name_input_popup(surface, title_font, font, name_text, save_button):
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 170))
    surface.blit(overlay, (0, 0))

    popup_rect = Rect(150, 150, 500, 260)
    pygame.draw.rect(surface, (35, 35, 55), popup_rect, border_radius=16)
    pygame.draw.rect(surface, (230, 230, 255), popup_rect, width=3, border_radius=16)

    title = title_font.render("랭킹 이름 입력", True, (255, 255, 255))
    surface.blit(title, (popup_rect.x + 130, popup_rect.y + 25))

    guide = font.render("이름을 입력한 뒤 저장 버튼 또는 Enter를 누르세요.", True, (230, 230, 230))
    surface.blit(guide, (popup_rect.x + 35, popup_rect.y + 90))

    input_rect = Rect(popup_rect.x + 60, popup_rect.y + 130, 380, 45)
    pygame.draw.rect(surface, (255, 255, 255), input_rect, border_radius=8)
    pygame.draw.rect(surface, (50, 50, 70), input_rect, width=2, border_radius=8)

    display_name = name_text if name_text else ""
    name_surface = font.render(display_name, True, (0, 0, 0))
    surface.blit(name_surface, (input_rect.x + 12, input_rect.y + 10))

    draw_button(surface, save_button, "저장", font, (60, 160, 90))


def main():
    state = reset_game()
    rankings = load_rankings()

    sysfont = pygame.font.Font(FONT_PATH, 28)
    bigfont = pygame.font.Font(FONT_PATH, 52)
    rankfont = pygame.font.Font(FONT_PATH, 24)

    # 게임방법 팝업 전용 폰트: 기존보다 대략 절반 수준
    help_title_font = pygame.font.Font(FONT_PATH, 28)
    help_font = pygame.font.Font(FONT_PATH, 16)

    ship_path = os.path.join(BASE_DIR, "우주선파랑.png")
    bang_path = os.path.join(BASE_DIR, "bang.png")
    enemy_path = os.path.join(BASE_DIR, "보라색적.png")
    center_bg_path = os.path.join(BASE_DIR, "중앙배경.png")
    outer_bg_path = os.path.join(BASE_DIR, "바깥배경.png")
    bullet_path = os.path.join(BASE_DIR, "공격.png")

    ship_image = pygame.image.load(ship_path).convert_alpha()
    bang_image = pygame.image.load(bang_path).convert_alpha()
    enemy_image = pygame.image.load(enemy_path).convert_alpha()
    center_bg_image = pygame.image.load(center_bg_path).convert()
    outer_bg_image = pygame.image.load(outer_bg_path).convert()
    bullet_image = pygame.image.load(bullet_path).convert_alpha()

    ship_image = pygame.transform.scale(ship_image, (70, 70))
    enemy_image = pygame.transform.scale(enemy_image, (55, 55))
    bang_image = pygame.transform.scale(bang_image, (80, 80))
    bullet_image = pygame.transform.scale(bullet_image, (36, 18))
    center_bg_image = pygame.transform.scale(center_bg_image, (WIDTH, HEIGHT))
    outer_bg_image = pygame.transform.scale(outer_bg_image, (WIDTH, HEIGHT))

    ship_width = ship_image.get_width()
    ship_height = ship_image.get_height()
    enemy_width = enemy_image.get_width()
    enemy_height = enemy_image.get_height()
    bullet_width = bullet_image.get_width()
    bullet_height = bullet_image.get_height()

    pause_button = Rect(20, 20, 110, 45)
    reset_button = Rect(145, 20, 110, 45)
    help_button = Rect(270, 20, 130, 45)
    restart_button = Rect(WIDTH // 2 - 90, HEIGHT // 2 + 25, 180, 55)
    help_close_button = Rect(WIDTH // 2 - 55, HEIGHT - 135, 110, 40)
    save_name_button = Rect(WIDTH // 2 - 60, 330, 120, 45)

    while True:
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()

            elif event.type == pygame.KEYDOWN:
                if state["asking_name"]:
                    if event.key == K_BACKSPACE:
                        state["player_name"] = state["player_name"][:-1]
                    elif event.key == K_RETURN:
                        rankings = update_rankings(state["player_name"], state["score"], rankings)
                        state["ranking_saved"] = True
                        state["asking_name"] = False
                    else:
                        if len(state["player_name"]) < 12 and event.unicode.isprintable():
                            state["player_name"] += event.unicode

                elif state["show_help"]:
                    pass

                else:
                    if event.key == K_ESCAPE and not state["game_over"]:
                        state["paused"] = not state["paused"]
                    elif event.key == K_r:
                        state = reset_game()

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = event.pos

                if state["asking_name"]:
                    if save_name_button.collidepoint(mouse_pos):
                        rankings = update_rankings(state["player_name"], state["score"], rankings)
                        state["ranking_saved"] = True
                        state["asking_name"] = False

                elif state["show_help"]:
                    if help_close_button.collidepoint(mouse_pos):
                        state["show_help"] = False

                else:
                    if pause_button.collidepoint(mouse_pos) and not state["game_over"]:
                        state["paused"] = not state["paused"]
                    elif reset_button.collidepoint(mouse_pos):
                        state = reset_game()
                    elif help_button.collidepoint(mouse_pos) and not state["game_over"]:
                        state["show_help"] = True
                    elif state["game_over"] and not state["asking_name"] and restart_button.collidepoint(mouse_pos):
                        state = reset_game()

        keys = pygame.key.get_pressed()

        game_running = (
            not state["game_over"]
            and not state["paused"]
            and not state["show_help"]
            and not state["asking_name"]
        )

        if game_running:
            state["score"] += 10

            state["ship_y"] += state["gravity"]

            if keys[K_UP]:
                state["ship_y"] -= state["move_speed"]
            if keys[K_DOWN]:
                state["ship_y"] += state["move_speed"]
            if keys[K_LEFT]:
                state["ship_x"] -= state["move_speed"]
            if keys[K_RIGHT]:
                state["ship_x"] += state["move_speed"]

            if state["ship_x"] < 0:
                state["ship_x"] = 0
            if state["ship_x"] > WIDTH - ship_width:
                state["ship_x"] = WIDTH - ship_width
            if state["ship_y"] < 0:
                state["ship_y"] = 0
            if state["ship_y"] > HEIGHT - ship_height:
                state["ship_y"] = HEIGHT - ship_height

            edge = state["holes"][-1].copy()
            test = edge.move(0, state["slope"])

            if test.top <= 0 or test.bottom >= HEIGHT:
                state["slope"] = randint(1, 6) * (-1 if state["slope"] > 0 else 1)
                edge.inflate_ip(0, -20)

            edge.move_ip(10, state["slope"])
            state["holes"].append(edge)
            del state["holes"][0]
            state["holes"] = [x.move(-10, 0) for x in state["holes"]]

            state["enemy_spawn_timer"] += 1
            if state["enemy_spawn_timer"] >= state["enemy_spawn_interval"]:
                rightmost_hole = state["holes"][-1]
                safe_top = rightmost_hole.top + 5
                safe_bottom = rightmost_hole.bottom - enemy_height - 5

                if safe_bottom < safe_top:
                    enemy_y = rightmost_hole.top
                else:
                    enemy_y = randint(safe_top, safe_bottom)

                enemy_x = WIDTH - enemy_width

                state["enemies"].append({
                    "x": float(enemy_x),
                    "y": float(enemy_y),
                    "speed": float(randint(3, 6))
                })

                state["enemy_spawn_timer"] = 0
                state["enemy_spawn_interval"] = randint(20, 40)

            for enemy in state["enemies"]:
                enemy["x"] -= enemy["speed"]

            state["enemies"] = [e for e in state["enemies"] if e["x"] > -enemy_width]

            state["bullet_timer"] += 1
            if state["bullet_timer"] >= 8:
                bullet_x = state["ship_x"] + ship_width - 5
                bullet_y = state["ship_y"] + ship_height // 2 - bullet_height // 2
                state["bullets"].append({
                    "x": float(bullet_x),
                    "y": float(bullet_y),
                    "speed": 14.0
                })
                state["bullet_timer"] = 0

            for bullet in state["bullets"]:
                bullet["x"] += bullet["speed"]

            state["bullets"] = [b for b in state["bullets"] if b["x"] < WIDTH + bullet_width]

            ship_rect = Rect(int(state["ship_x"]), int(state["ship_y"]), ship_width, ship_height)

            for hole in state["holes"]:
                wall_top = Rect(hole.left, 0, hole.width, hole.top)
                wall_bottom = Rect(hole.left, hole.bottom, hole.width, HEIGHT - hole.bottom)

                if ship_rect.colliderect(wall_top) or ship_rect.colliderect(wall_bottom):
                    state["game_over"] = True
                    state["paused"] = False
                    state["asking_name"] = True
                    break

            if not state["game_over"]:
                for enemy in state["enemies"]:
                    enemy_rect = Rect(int(enemy["x"]), int(enemy["y"]), enemy_width, enemy_height)
                    if ship_rect.colliderect(enemy_rect):
                        state["game_over"] = True
                        state["paused"] = False
                        state["asking_name"] = True
                        break

            if not state["game_over"]:
                remaining_bullets = []
                remaining_enemies = state["enemies"][:]
                removed_enemy_indexes = set()

                for bullet in state["bullets"]:
                    bullet_rect = Rect(int(bullet["x"]), int(bullet["y"]), bullet_width, bullet_height)
                    hit = False

                    for idx, enemy in enumerate(remaining_enemies):
                        if idx in removed_enemy_indexes:
                            continue

                        enemy_rect = Rect(int(enemy["x"]), int(enemy["y"]), enemy_width, enemy_height)

                        if bullet_rect.colliderect(enemy_rect):
                            removed_enemy_indexes.add(idx)
                            state["score"] += 100
                            hit = True
                            break

                    if not hit:
                        remaining_bullets.append(bullet)

                state["bullets"] = remaining_bullets
                state["enemies"] = [
                    enemy for idx, enemy in enumerate(remaining_enemies)
                    if idx not in removed_enemy_indexes
                ]

        SURFACE.blit(outer_bg_image, (0, 0))

        for hole in state["holes"]:
            SURFACE.blit(center_bg_image, hole, area=hole)

        for enemy in state["enemies"]:
            SURFACE.blit(enemy_image, (int(enemy["x"]), int(enemy["y"])))

        for bullet in state["bullets"]:
            SURFACE.blit(bullet_image, (int(bullet["x"]), int(bullet["y"])))

        SURFACE.blit(ship_image, (int(state["ship_x"]), int(state["ship_y"])))

        score_image = sysfont.render(f"점수 : {state['score']}", True, (255, 255, 255))
        SURFACE.blit(score_image, (WIDTH - 170, 25))

        pause_text = "재개" if state["paused"] else "일시정지"
        draw_button(SURFACE, pause_button, pause_text, sysfont, (70, 70, 200))
        draw_button(SURFACE, reset_button, "리셋", sysfont, (200, 80, 80))
        draw_button(SURFACE, help_button, "게임방법", sysfont, (70, 160, 110))

        if state["paused"] and not state["game_over"] and not state["show_help"] and not state["asking_name"]:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 120))
            SURFACE.blit(overlay, (0, 0))

            pause_msg = bigfont.render("일시정지", True, (255, 255, 255))
            pause_msg_rect = pause_msg.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 20))
            SURFACE.blit(pause_msg, pause_msg_rect)

        if state["show_help"]:
            draw_help_popup(SURFACE, help_title_font, help_font, help_close_button)

        if state["game_over"]:
            SURFACE.blit(bang_image, (int(state["ship_x"]), int(state["ship_y"]) - 10))

            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 140))
            SURFACE.blit(overlay, (0, 0))

            over_msg = bigfont.render("게임 오버", True, (255, 255, 255))
            over_msg_rect = over_msg.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 130))
            SURFACE.blit(over_msg, over_msg_rect)

            score_msg = sysfont.render(f"최종 점수 : {state['score']}", True, (255, 255, 255))
            score_msg_rect = score_msg.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 90))
            SURFACE.blit(score_msg, score_msg_rect)

            if state["asking_name"]:
                draw_name_input_popup(SURFACE, sysfont, sysfont, state["player_name"], save_name_button)
            else:
                draw_button(SURFACE, restart_button, "다시시작", sysfont, (60, 160, 90))

                rank_title = sysfont.render("TOP 5 랭킹", True, (255, 255, 0))
                SURFACE.blit(rank_title, (WIDTH // 2 - 70, HEIGHT // 2 + 110))

                for i, item in enumerate(rankings[:5], start=1):
                    rank_text = rankfont.render(
                        f"{i}. {item['name']} - {item['score']}",
                        True,
                        (255, 255, 255)
                    )
                    SURFACE.blit(rank_text, (WIDTH // 2 - 120, HEIGHT // 2 + 110 + i * 28))

        pygame.display.update()
        FPSCLOCK.tick(30)


if __name__ == '__main__':
    main()