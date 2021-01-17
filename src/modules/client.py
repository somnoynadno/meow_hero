import logging
import random
import socket
import sys

import pygame
from pygame.locals import *

from . import objects, layouts, interface
from . import colors, config

"""
Game loop для двух игроков.
Игроки управляются с контроллера.
"""


def terminate():
    print("Goodbye")
    pygame.quit()
    sys.exit(0)


def two_players_mode(window_surface, WINDOW_WIDTH, WINDOW_HEIGHT):
    # setup game
    pygame.mouse.set_visible(False)

    main_clock = pygame.time.Clock()
    pygame.time.set_timer(pygame.USEREVENT, 500)

    # setup bg
    background_image_in_game = pygame.image.load("../drawable/backgrounds/abstract_background" + str(random.randint(1, 16)) + '.jpg')
    background_image_in_game = pygame.transform.scale(background_image_in_game, (WINDOW_WIDTH, WINDOW_HEIGHT))

    # setup Meow Hero
    meow_hero1 = objects.MeowHero(6)
    meow_hero1.move_rate = 12
    meow_hero1.rect.move_ip(int(WINDOW_WIDTH / 2)-100, 7 * int(WINDOW_HEIGHT / 8))

    meow_hero2 = objects.MeowHero(8)
    meow_hero2.move_rate = 12
    meow_hero2.rect.move_ip(int(WINDOW_WIDTH / 2)+100, 7 * int(WINDOW_HEIGHT / 8))

    move_left1 = move_right1 = move_up1 = move_down1 = False
    move_left2 = move_right2 = move_up2 = move_down2 = False

    # set up music
    game_over_sound = pygame.mixer.Sound('../sound/game_over.wav')
    damage_sound = pygame.mixer.Sound('../sound/short_tracks/damage.wav')
    victory_sound = pygame.mixer.Sound('../sound/short_tracks/victory.wav')
    coin_sound = pygame.mixer.Sound('../sound/short_tracks/coin.wav')
    health_sound = pygame.mixer.Sound('../sound/short_tracks/health.wav')
    new_top_sound = pygame.mixer.Sound('../sound/short_tracks/health.wav')
    attack_sound = pygame.mixer.Sound('../sound/short_tracks/attack_1' + ".wav")
    freeze_sound = pygame.mixer.Sound('../sound/short_tracks/freeze.wav')
    boom_sound = pygame.mixer.Sound('../sound/short_tracks/boom.wav')
    reload_sound = pygame.mixer.Sound('../sound/short_tracks/reload.wav')
    # coin_drop_sound = pygame.mixer.Sound('../sound/short_tracks/coin_dropping.wav')
    shield_sound = pygame.mixer.Sound('../sound/short_tracks/shield.wav')
    rate_of_fire_sound = pygame.mixer.Sound('../sound/short_tracks/rate_of_fire.wav')
    laser_sound = pygame.mixer.Sound('../sound/short_tracks/laser.wav')

    pygame.mixer.music.load('../sound/background_music/music' + str(random.randint(1, 13)) + '.mp3')
    pygame.mixer.music.play(-1, 0.0)

    # set up text
    font = pygame.font.SysFont(None, 78)
    player1_text = interface.TextView(font, color.WHITE, 10, 10, "Player 1")
    player1_life_text = interface.TextView(font, color.WHITE, 10, 80)
    player2_text = interface.TextView(font, color.WHITE, WINDOW_WIDTH*10/12, 10, "Player 2")
    player2_life_text = interface.TextView(font, color.WHITE, WINDOW_WIDTH*10/12, 80)
    score_text = interface.TextView(font, color.WHITE, WINDOW_WIDTH / 2, 72)
    score_text.rect.center = (WINDOW_WIDTH/2-120, 30)
    timer_text = interface.TextView(font, color.WHITE, WINDOW_WIDTH / 2, 10)
    timer_text.rect.center = (WINDOW_WIDTH/2-120, 96)

    # spawn enemy by time
    available_enemy_level = 1
    # spawn bonuses by time
    available_bonus_type = 1

    bullets = []
    enemies = []
    enemy_bullets = []
    bonuses = []
    bonus_types = ["Coin", "Life", "Weapon",
                   "Shield", "Rate of fire", "Mass Attack",
                   "Three Directions", "Freeze", "x2"]

    meow_heroes = list()
    meow_heroes.append(meow_hero1)
    meow_heroes.append(meow_hero2)

    enemy_spawn_probability = 0.2

    # score coefficient
    k = 1

    main_timer = 0
    score = 0

    # bonus timers
    freeze_bonus = 0
    x2_time = 0

    running = True
    while running:  # the game loop runs while the game part is playing
        score += 1*k  # increase score
        for event in pygame.event.get():
            if event.type == QUIT:
                terminate()

            if event.type == pygame.USEREVENT:  # time tick
                main_timer += 1

                # increase enemy level, bonus type and enemy spawn probability
                if main_timer % 60 == 0 and available_enemy_level < 12:
                    available_enemy_level += 1
                    enemy_spawn_probability += 0.03
                    if available_bonus_type < len(bonus_types):
                        available_bonus_type += 1

                # spawn enemy
                if len(enemies) < config.ENEMY_MAX_COUNT and not freeze_bonus:
                    dice = random.random()
                    if dice < enemy_spawn_probability:
                        level = random.randint(1, available_enemy_level)
                        enemy = objects.DogEnemyMultiplayer(level)
                        enemy.rect.move_ip(random.randint(0, WINDOW_WIDTH), 0)
                        enemies.append(enemy)

                # bonus lifetime
                for bonus in bonuses:
                    bonus.lifetime -= 1
                    if bonus.lifetime <= 0:
                        bonuses.remove(bonus)

                # victory condition
                if main_timer >= 600:
                    running = False

                # attack time
                for enemy in enemies:
                    enemy_bullet = enemy.attack()
                    if enemy_bullet is not None:
                        enemy_bullets.append(enemy_bullet)

                # decrement invulnerability, three directions and rate of fire
                for meow in meow_heroes:
                    if meow.invulnerability > 0:
                        meow.invulnerability -= 1
                    if meow.three_directions_time > 0:
                        meow.three_directions_time -= 1
                    if meow.rate_of_fire_time_limit > 0:
                        meow.rate_of_fire_time_limit -= 1
                        if meow.rate_of_fire_time_limit == 0:
                            meow.max_weapon_reload = 30

                # decrement freeze and x2 bonuses
                if freeze_bonus > 0:
                    freeze_bonus -= 1
                if x2_time > 0:
                    x2_time -= 1
                    if x2_time == 0:
                        k = 1

                # spawn bonus
                if main_timer % 12 == 0 and len(bonuses) <= 7:
                    bonus_type = random.randint(1, available_bonus_type)
                    bonus = objects.Bonus(bonus_types[bonus_type - 1])
                    bonus.rect.move_ip(random.randint(50, WINDOW_WIDTH - 50),
                                       random.randint(50, WINDOW_HEIGHT - 50))
                    bonuses.append(bonus)

            # terminating by ESC
            if event.type == KEYUP:
                if event.key == K_ESCAPE:
                    quit_state = layouts.interruption_menu(window_surface, WINDOW_WIDTH, WINDOW_HEIGHT)
                    if quit_state:
                        pygame.mixer.music.stop()
                        pygame.mouse.set_visible(True)
                        return False

            if event.type == KEYDOWN:
                if event.key == ord('a'):
                    move_right1 = False
                    move_left1 = True
                if event.key == ord('d'):
                    move_left1 = False
                    move_right1 = True
                if event.key == ord('w'):
                    move_down1 = False
                    move_up1 = True
                if event.key == ord('s'):
                    move_up1 = False
                    move_down1 = True

            if event.type == KEYUP:
                if event.key == ord('a'):
                    move_left1 = False
                if event.key == ord('d'):
                    move_right1 = False
                if event.key == ord('w'):
                    move_up1 = False
                if event.key == ord('s'):
                    move_down1 = False

            if event.type == KEYDOWN:
                if event.key == K_LEFT:
                    move_right2 = False
                    move_left2 = True
                if event.key == K_RIGHT:
                    move_left2 = False
                    move_right2 = True
                if event.key == K_UP:
                    move_down2 = False
                    move_up2 = True
                if event.key == K_DOWN:
                    move_up2 = False
                    move_down2 = True

            if event.type == KEYUP:
                if event.key == K_LEFT:
                    move_left2 = False
                if event.key == K_RIGHT:
                    move_right2 = False
                if event.key == K_UP:
                    move_up2 = False
                if event.key == K_DOWN:
                    move_down2 = False

        # move the first player around
        if move_left1 and meow_hero1.rect.left > 0:
            meow_hero1.move(-1, 0)
        if move_right1 and meow_hero1.rect.right < WINDOW_WIDTH:
            meow_hero1.move(1, 0)
        if move_up1 and meow_hero1.rect.top > 0:
            meow_hero1.move(0, -1)
        if move_down1 and meow_hero1.rect.bottom < WINDOW_HEIGHT:
            meow_hero1.move(0, 1)

        # move the second player around
        if move_left2 and meow_hero2.rect.left > 0:
            meow_hero2.move(-1, 0)
        if move_right2 and meow_hero2.rect.right < WINDOW_WIDTH:
            meow_hero2.move(1, 0)
        if move_up2 and meow_hero2.rect.top > 0:
            meow_hero2.move(0, -1)
        if move_down2 and meow_hero2.rect.bottom < WINDOW_HEIGHT:
            meow_hero2.move(0, 1)

        # auto attack
        for meow in meow_heroes:
            meow.current_reload += 1
            if meow.current_reload >= meow.max_weapon_reload:
                bullet = objects.Bullet(meow.weapon_power, "Multiplayer")
                bullet.rect.move_ip(meow.rect.left, meow.rect.top)
                bullets.append(bullet)
                meow.current_reload = 0
                if meow.three_directions_time > 0:
                    bullet = objects.Bullet(meow.weapon_power, "Multiplayer")
                    bullet.rect.move_ip(meow.rect.left, meow.rect.top)
                    bullet.x = int(bullet.speed/3)
                    bullets.append(bullet)

                    bullet = objects.Bullet(meow.weapon_power, "Multiplayer")
                    bullet.rect.move_ip(meow.rect.left, meow.rect.top)
                    bullet.x = int(bullet.speed/3)*(-1)
                    bullets.append(bullet)

        # hitting enemy
        for enemy in enemies:
            for bullet in bullets:
                if enemy.rect.colliderect(bullet.rect):
                    enemy.life -= bullet.power
                    bullet.life -= 1

	# if enemy under screen, hit hero
        for enemy in enemies:
            if enemy.rect.top > WINDOW_HEIGHT:
                for meow in meow_heroes:
                    meow.life -= 1
                enemies.remove(enemy)
                damage_sound.play()

        # hitting enemy and player
        for enemy in enemies:
            for meow in meow_heroes:
                if meow.rect.colliderect(enemy.rect) and not meow.invulnerability:
                    meow.life -= 1
                    enemies.remove(enemy)
                    damage_sound.play()

        # hitting players by bullets
        for bullet in enemy_bullets:
            for meow in meow_heroes:
                if meow.rect.colliderect(bullet.rect) and not meow.invulnerability:
                    meow.life -= 1
                    meow.invulnerability += 2
                    if meow.weapon_power > 1:
                        meow.weapon_power -= 1
                    enemy_bullets.remove(bullet)
                    damage_sound.play()

        # collecting bonuses:
        for bonus in bonuses:
            for meow in meow_heroes:
                if meow.rect.colliderect(bonus.rect):
                    if bonus.bonus_type == "Life":
                        meow.life += 1
                        health_sound.play()
                    elif bonus.bonus_type == "Coin":
                        score += 800*available_enemy_level*k
                        coin_sound.play()
                    elif bonus.bonus_type == "Weapon":
                        reload_sound.play()
                        if meow.weapon_power < 7:
                            meow.weapon_power += 1
                        else:
                            score += 10000*k
                    elif bonus.bonus_type == "Shield":
                        meow.invulnerability += 10
                        shield_sound.play()
                    elif bonus.bonus_type == "Mass Attack":
                        boom_sound.play()
                        for enemy in enemies:
                            enemy.life -= meow.weapon_power
                    elif bonus.bonus_type == "Rate of fire":
                        rate_of_fire_sound.play()
                        meow.max_weapon_reload = 8
                        meow.rate_of_fire_time_limit += 8 + available_enemy_level*2
                    elif bonus.bonus_type == "Freeze":
                        freeze_sound.play()
                        freeze_bonus += 8 + available_enemy_level
                    elif bonus.bonus_type == "Three Directions":
                        laser_sound.play()
                        meow.three_directions_time += 8 + available_enemy_level*2
                    elif bonus.bonus_type == "x2":
                        coin_sound.play()
                        x2_time += 2*available_enemy_level
                        k = 2

                    bonuses.remove(bonus)

        # check if bullet is out of screen
        for bullet in bullets:
            if bullet.rect.bottom <= 0:
                bullets.remove(bullet)

        # draw background
        window_surface.blit(background_image_in_game, [0, 0])

        # draw players
        meow_hero1.draw(window_surface)
        meow_hero2.draw(window_surface)

        # draw text
        player1_text.draw(window_surface)
        player2_text.draw(window_surface)
        score_text.draw_this(window_surface, 'Score: %s' % (score))
        timer_text.draw_this(window_surface, "Time " + str(main_timer).rjust(3) if main_timer <= 1600 else 'NICE, NIGGA')
        player1_life_text.draw_this(window_surface, 'Life: x%s' % (meow_hero1.life))
        player2_life_text.draw_this(window_surface, 'Life: x%s' % (meow_hero2.life))

        # draw bonuses
        for bonus in bonuses:
            bonus.draw(window_surface)

        # move and draw hero bullets
        for bullet in bullets:
            bullet.move()
            if bullet.rect.top > WINDOW_HEIGHT or bullet.life <= 0:
                bullets.remove(bullet)
            bullet.draw(window_surface)

        # move enemies and bullets
        if not freeze_bonus:
            for enemy in enemies:
                enemy.move()
            for bullet in enemy_bullets:
                bullet.move()

        # draw and kill enemies
        for enemy in enemies:
            if enemy.life <= 0:
                enemies.remove(enemy)
                score += 100 * enemy.level
            enemy.draw(window_surface)

        # draw enemy bullets
        for bullet in enemy_bullets:
            if bullet.rect.top > WINDOW_HEIGHT or bullet.life <= 0:
                enemy_bullets.remove(bullet)
            bullet.draw(window_surface)

        # check for ending:
        if meow_hero1.life <= 0 or meow_hero2.life <= 0:
            running = False

        pygame.display.update()
        main_clock.tick(config.FPS)

    pygame.mouse.set_visible(True)
    pygame.mouse.set_visible(True)

    pygame.mixer_music.stop()
    victory_sound.play()
    layouts.two_players_victory_layout(window_surface, WINDOW_WIDTH, WINDOW_HEIGHT, score, main_timer)
    return
