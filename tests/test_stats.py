"""Tests unitarios para Stats."""

import unittest

from stats.stats import Stats


class TestStatsInit(unittest.TestCase):
    def test_valores_por_defecto(self) -> None:
        s = Stats()
        self.assertEqual(s.level, 1)
        self.assertEqual(s.max_health, 100.0)
        self.assertEqual(s.damage, 10.0)
        self.assertEqual(s.defense, 5.0)
        self.assertEqual(s.endurance, 100.0)
        self.assertEqual(s.experience, 0.0)

    def test_valores_personalizados(self) -> None:
        s = Stats(max_health=200.0, damage=20.0, defense=10.0, level=3)
        self.assertEqual(s.max_health, 200.0)
        self.assertEqual(s.damage, 20.0)
        self.assertEqual(s.level, 3)

    def test_max_health_cero_lanza_error(self) -> None:
        with self.assertRaises(ValueError):
            Stats(max_health=0.0)

    def test_level_cero_lanza_error(self) -> None:
        with self.assertRaises(ValueError):
            Stats(level=0)

    def test_damage_negativo_lanza_error(self) -> None:
        with self.assertRaises(ValueError):
            Stats(damage=-1.0)

    def test_defense_negativa_lanza_error(self) -> None:
        with self.assertRaises(ValueError):
            Stats(defense=-1.0)


class TestStatsExperience(unittest.TestCase):
    def test_gain_experience_sin_level_up(self) -> None:
        s = Stats()
        levels = s.gain_experience(50.0)
        self.assertEqual(levels, 0)
        self.assertEqual(s.experience, 50.0)
        self.assertEqual(s.level, 1)

    def test_gain_experience_provoca_level_up(self) -> None:
        s = Stats()
        levels = s.gain_experience(100.0)
        self.assertEqual(levels, 1)
        self.assertEqual(s.level, 2)
        self.assertEqual(s.experience, 0.0)

    def test_gain_experience_multiples_niveles(self) -> None:
        s = Stats()
        # nivel 1 → 100 xp para subir; nivel 2 → 150 xp; total 250+
        levels = s.gain_experience(260.0)
        self.assertGreaterEqual(levels, 2)
        self.assertGreaterEqual(s.level, 3)

    def test_gain_experience_negativa_lanza_error(self) -> None:
        s = Stats()
        with self.assertRaises(ValueError):
            s.gain_experience(-10.0)


class TestStatsLevelUp(unittest.TestCase):
    def test_level_up_incrementa_nivel(self) -> None:
        s = Stats()
        s.level_up()
        self.assertEqual(s.level, 2)

    def test_level_up_mejora_atributos(self) -> None:
        s = Stats()
        prev_health = s.max_health
        prev_damage = s.damage
        prev_defense = s.defense
        prev_endurance = s.endurance
        s.level_up()
        self.assertGreater(s.max_health, prev_health)
        self.assertGreater(s.damage, prev_damage)
        self.assertGreater(s.defense, prev_defense)
        self.assertGreater(s.endurance, prev_endurance)

    def test_experience_threshold_crece_con_nivel(self) -> None:
        s = Stats()
        t1 = s.experience_threshold
        s.level_up()
        t2 = s.experience_threshold
        self.assertGreater(t2, t1)


if __name__ == "__main__":
    unittest.main()
