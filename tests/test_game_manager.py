"""Tests básicos para GameManager."""

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

sys.path.insert(0, str(Path(__file__).parent.parent))

from game_manager import GameManager
from core.vector2d import Vector2D
from entities.enemy import Enemy
from inventory.item import Item


class DummyEnemy:
    """Representa un enemigo mínimo para validar victoria."""

    def __init__(self, is_defeated: bool) -> None:
        self.is_defeated = is_defeated


class FakeKeys:
    """Simula teclado para tests de movimiento."""

    def __init__(self, pressed: set[int]) -> None:
        self.pressed = pressed

    def __getitem__(self, key: int) -> bool:
        return key in self.pressed


class TestGameManager(unittest.TestCase):
    """Verifica inicialización, reinicio y victoria del GameManager."""

    @classmethod
    def setUpClass(cls) -> None:
        pygame.init()

    @classmethod
    def tearDownClass(cls) -> None:
        pygame.quit()

    def setUp(self) -> None:
        self.screen = pygame.Surface((1280, 720))

        image_patcher = patch(
            "game_manager.pygame.image.load",
            return_value=pygame.Surface((64, 64)),
        )
        enemies_patcher = patch(
            "game_manager.generate_enemies_from_image",
            return_value=[],
        )

        self.addCleanup(image_patcher.stop)
        self.addCleanup(enemies_patcher.stop)

        image_patcher.start()
        enemies_patcher.start()

        self.manager = GameManager(screen=self.screen)

    def test_init_configura_estado_base(self) -> None:
        self.assertTrue(self.manager.is_playing)
        self.assertFalse(self.manager.game_over)
        self.assertEqual(self.manager.player.name, "Hero")
        self.assertIs(self.manager.hud.player, self.manager.player)
        self.assertEqual(len(self.manager.store.items), 3)
        self.assertGreater(len(self.manager.world.platforms), 0)

    def test_start_game_reinicia_estado_transitorio(self) -> None:
        old_player = self.manager.player
        self.manager.projectiles.append(object())
        self.manager.messages.append(("temp", 1.0))
        self.manager.game_over = True
        self.manager.store_dialog_open = True
        self.manager.store_dialog_tab = "sell"
        self.manager.store_buy_index = 2
        self.manager.store_sell_index = 1
        self.manager.player.cash = 0

        self.manager.start_game(seed=99)

        self.assertIsNot(self.manager.player, old_player)
        self.assertIs(self.manager.hud.player, self.manager.player)
        self.assertEqual(self.manager.player.cash, 100)
        self.assertEqual(self.manager.projectiles, [])
        self.assertEqual(self.manager.messages, [])
        self.assertFalse(self.manager.game_over)
        self.assertFalse(self.manager.store_dialog_open)
        self.assertEqual(self.manager.store_dialog_tab, "buy")
        self.assertEqual(self.manager.store_buy_index, 0)
        self.assertEqual(self.manager.store_sell_index, 0)

    def test_check_victory_por_exploracion(self) -> None:
        self.manager.world.enemies = [DummyEnemy(False)]
        self.manager.world.camera.offset.x = self.manager.VICTORY_CAMERA_X
        self.manager.boss_enemy = DummyEnemy(True)

        self.assertTrue(self.manager.check_victory())

    def test_check_victory_por_enemigos(self) -> None:
        self.manager.world.enemies = [DummyEnemy(True), DummyEnemy(True)]
        self.manager.world.camera.offset.x = 0.0
        self.manager.boss_enemy = DummyEnemy(True)

        self.assertTrue(self.manager.check_victory())

    def test_check_victory_falsa_si_faltan_objetivos(self) -> None:
        self.manager.world.enemies = [DummyEnemy(True), DummyEnemy(False)]
        self.manager.world.camera.offset.x = self.manager.VICTORY_CAMERA_X - 1.0
        self.manager.boss_enemy = DummyEnemy(False)

        self.assertFalse(self.manager.check_victory())

    def test_check_victory_falsa_si_boss_sigue_vivo(self) -> None:
        self.manager.world.enemies = [DummyEnemy(True), DummyEnemy(True)]
        self.manager.world.camera.offset.x = self.manager.VICTORY_CAMERA_X
        self.manager.boss_enemy = DummyEnemy(False)

        self.assertFalse(self.manager.check_victory())

    def test_caida_al_vacio_activa_game_over(self) -> None:
        self.manager.player.position.y = (
            self.manager.SCREEN_HEIGHT + self.manager.VOID_Y_MARGIN + 300.0
        )
        self.manager.player_vy = 0.0
        self.manager.on_ground = False

        self.manager.update(0.016)

        self.assertTrue(self.manager.game_over)
        self.assertFalse(self.manager.player.is_active)

    def test_spawn_inicia_sobre_una_plataforma(self) -> None:
        player_bottom = self.manager.player.position.y + self.manager.player.radius
        support_margin = self.manager.player.radius * 0.4

        is_supported = any(
            abs(platform.y - player_bottom) < 1e-6
            and (platform.x - support_margin)
            <= self.manager.player.position.x
            <= (platform.x + platform.width + support_margin)
            for platform in self.manager.world.platforms
        )

        self.assertTrue(self.manager.on_ground)
        self.assertTrue(is_supported)

    def test_player_puede_moverse_en_aire(self) -> None:
        self.manager.on_ground = False
        self.manager.player_vy = -100.0
        start_x = self.manager.player.position.x

        with patch("game_manager.pygame.key.get_pressed", return_value=FakeKeys({pygame.K_RIGHT})):
            self.manager.update(0.1)

        self.assertGreater(self.manager.player.position.x, start_x)

    def test_player_desacelera_sin_input(self) -> None:
        self.manager.on_ground = True
        self.manager.player_vx = self.manager.PLAYER_SPEED

        with patch("game_manager.pygame.key.get_pressed", return_value=FakeKeys(set())):
            self.manager.update(0.05)

        self.assertLess(self.manager.player_vx, self.manager.PLAYER_SPEED)

    def test_player_sale_del_borde_izquierdo_al_mover_derecha(self) -> None:
        left_world = self.manager.world.camera.offset.x + self.manager.player.radius
        self.manager.player.position.x = left_world
        start_screen_x = self.manager.player.position.x - self.manager.world.camera.offset.x

        with patch("game_manager.pygame.key.get_pressed", return_value=FakeKeys({pygame.K_RIGHT})):
            self.manager.update(0.1)

        end_screen_x = self.manager.player.position.x - self.manager.world.camera.offset.x
        self.assertGreater(end_screen_x, start_screen_x)

    def test_set_difficulty_facil_aplica_parametros(self) -> None:
        self.manager.set_difficulty("facil", restart=False)

        self.assertEqual(self.manager.current_difficulty, "facil")
        self.assertEqual(self.manager.enemy_count_for_run, 20)
        self.assertAlmostEqual(self.manager.enemy_spawn_interval, 2.0)
        self.assertAlmostEqual(self.manager.enemy_damage_multiplier, 0.7)
        self.assertAlmostEqual(self.manager.boss_damage_multiplier, 0.7)
        self.assertAlmostEqual(self.manager.world.camera.scroll_speed, 160.0)

    def test_set_difficulty_dificil_aplica_parametros(self) -> None:
        self.manager.set_difficulty("dificil", restart=False)

        self.assertEqual(self.manager.current_difficulty, "dificil")
        self.assertEqual(self.manager.enemy_count_for_run, 20)
        self.assertAlmostEqual(self.manager.enemy_spawn_interval, 0.7)
        self.assertAlmostEqual(self.manager.enemy_damage_multiplier, 1.35)
        self.assertAlmostEqual(self.manager.boss_damage_multiplier, 1.35)
        self.assertAlmostEqual(self.manager.world.camera.scroll_speed, 250.0)

    def test_set_difficulty_invalida_lanza_error(self) -> None:
        with self.assertRaises(ValueError):
            self.manager.set_difficulty("imposible", restart=False)

    def test_set_difficulty_con_restart_regenera_con_enemy_count_configurado(self) -> None:
        with patch.object(self.manager.world, "generate", wraps=self.manager.world.generate) as generate_spy:
            self.manager.set_difficulty("facil", restart=True)

        self.assertTrue(generate_spy.called)
        _, kwargs = generate_spy.call_args
        self.assertEqual(kwargs.get("enemy_count"), 20)

    def test_spawn_de_enemigos_es_progresivo(self) -> None:
        self.manager.enemy_spawn_interval = 0.01
        self.manager.pending_enemy_pool = [
            Enemy(self.screen, Vector2D(2000.0 + i * 120.0, self.manager.GROUND_Y), f"TestEnemy{i}")
            for i in range(3)
        ]
        self.manager.world.enemies = []
        self.manager.spawned_enemy_total = 0

        with patch("game_manager.pygame.key.get_pressed", return_value=FakeKeys(set())):
            self.manager.update(0.05)

        self.assertEqual(len(self.manager.world.enemies), 3)
        self.assertEqual(self.manager.spawned_enemy_total, 3)

    def test_boss_aparece_delante_de_la_camara_actual(self) -> None:
        self.manager.world.camera.offset.x = 5000.0

        boss = self.manager._create_boss_enemy()

        self.assertGreater(
            boss.position.x,
            self.manager.world.camera.offset.x + self.manager.SCREEN_WIDTH,
        )

    def test_draw_muestra_cartel_de_victoria_tras_derrotar_boss(self) -> None:
        boss = self.manager._create_boss_enemy()
        boss.health = 0.0
        boss.is_active = False
        self.manager.boss_enemy = boss
        self.manager.world.enemies = [DummyEnemy(True), DummyEnemy(True)]

        with patch("game_manager.pygame.display.flip"):
            try:
                self.manager.draw()
            except Exception as exc:
                self.fail(f"draw() lanzó una excepción al mostrar victoria: {exc}")

    def test_confirm_difficulty_selection_inicia_partida(self) -> None:
        self.manager.difficulty_menu_active = True
        self.manager._difficulty_selection_pending = True

        self.manager._confirm_difficulty_selection("dificil")

        self.assertFalse(self.manager.difficulty_menu_active)
        self.assertFalse(self.manager._difficulty_selection_pending)
        self.assertEqual(self.manager.current_difficulty, "dificil")

    def test_update_no_avanza_si_menu_dificultad_activo(self) -> None:
        self.manager.difficulty_menu_active = True
        initial_x = self.manager.player.position.x

        with patch("game_manager.pygame.key.get_pressed", return_value=FakeKeys({pygame.K_RIGHT})):
            self.manager.update(0.1)

        self.assertEqual(self.manager.player.position.x, initial_x)

    def test_store_inicia_bloqueada_por_dinero(self) -> None:
        self.assertFalse(self.manager.store_unlocked)
        self.assertLess(self.manager.player.cash, self.manager.STORE_UNLOCK_CASH)

    def test_store_se_desbloquea_al_alcanzar_umbral(self) -> None:
        self.manager.player.cash = self.manager.STORE_UNLOCK_CASH
        self.manager._update_store_unlock_state()

        self.assertTrue(self.manager.store_unlocked)

    def test_update_pausada_si_store_dialog_abierto(self) -> None:
        self.manager.store_dialog_open = True
        start_x = self.manager.player.position.x
        start_camera_x = self.manager.world.camera.offset.x

        with patch("game_manager.pygame.key.get_pressed", return_value=FakeKeys({pygame.K_RIGHT})):
            self.manager.update(0.2)

        self.assertEqual(self.manager.player.position.x, start_x)
        self.assertEqual(self.manager.world.camera.offset.x, start_camera_x)

    def test_tecla_e_abre_tienda_aunque_este_bloqueada(self) -> None:
        self.manager.store_unlocked = False
        self.manager.store_dialog_open = False

        with patch(
            "game_manager.pygame.event.get",
            return_value=[pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_e})],
        ):
            self.manager.handle_event()

        self.assertTrue(self.manager.store_dialog_open)

    def test_tecla_p_activa_y_desactiva_pausa(self) -> None:
        self.manager.paused = False

        with patch(
            "game_manager.pygame.event.get",
            return_value=[pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_p})],
        ):
            self.manager.handle_event()

        self.assertTrue(self.manager.paused)

        with patch(
            "game_manager.pygame.event.get",
            return_value=[pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_p})],
        ):
            self.manager.handle_event()

        self.assertFalse(self.manager.paused)

    def test_update_no_avanza_si_esta_en_pausa(self) -> None:
        self.manager.paused = True
        start_x = self.manager.player.position.x
        start_camera_x = self.manager.world.camera.offset.x

        with patch("game_manager.pygame.key.get_pressed", return_value=FakeKeys({pygame.K_RIGHT})):
            self.manager.update(0.2)

        self.assertEqual(self.manager.player.position.x, start_x)
        self.assertEqual(self.manager.world.camera.offset.x, start_camera_x)

    def test_use_selected_inventory_item_aplica_efecto_y_remueve_item(self) -> None:
        item = Item(
            "Pocion Test",
            buy_price=10.0,
            sell_price=5.0,
            attack_boost=3.0,
            defense_boost=2.0,
            damage=20.0,
        )
        self.manager.player.inventory.add_item(item)
        start_hp = self.manager.player.health
        start_atk = self.manager.player.stats.damage
        start_def = self.manager.player.stats.defense

        text, idx = self.manager._use_selected_inventory_item(0)

        self.assertIn("Usaste", text)
        self.assertEqual(idx, 0)
        self.assertNotIn(item, self.manager.player.inventory.items)
        self.assertGreaterEqual(self.manager.player.health, start_hp)
        self.assertEqual(self.manager.player.stats.damage, start_atk + 3.0)
        self.assertEqual(self.manager.player.stats.defense, start_def + 2.0)

    def test_use_selected_inventory_item_retorna_mensaje_si_inventario_vacio(self) -> None:
        self.manager.player.inventory.items.clear()

        text, idx = self.manager._use_selected_inventory_item(0)

        self.assertEqual(text, "Inventario vacio")
        self.assertEqual(idx, 0)


if __name__ == "__main__":
    unittest.main()
