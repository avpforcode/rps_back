import asyncio
import unittest
from serializers import *
from models import *


class GameTest(unittest.TestCase):
    def setUp(self):
        self.player_1 = Player()
        self.player_2 = Player()
        self.player_3 = Player()

    def test_two_gamers(self):
        game = Game(self.player_1, [self.player_2])

        game.throw(self.player_1, ROCK)
        game.throw(self.player_2, PAPER)
        self.assertEqual(game.winner, self.player_2.uid)

        game.throw(self.player_1, SCISSORS)
        game.throw(self.player_2, PAPER)
        self.assertEqual(game.winner, self.player_1.uid)

        game.throw(self.player_1, ROCK)
        game.throw(self.player_2, SCISSORS)
        self.assertEqual(game.winner, self.player_1.uid)

        game.throw(self.player_1, SCISSORS)
        game.throw(self.player_2, PASS)
        self.assertEqual(game.winner, self.player_1.uid)

        game.throw(self.player_1, PASS)
        game.throw(self.player_2, PAPER)
        self.assertEqual(game.winner, self.player_2.uid)

        game.throw(self.player_1, PASS)
        game.throw(self.player_2, PASS)
        self.assertEqual(game.winner, TIE)

        game.throw(self.player_1, PAPER)
        game.throw(self.player_2, PAPER)
        self.assertEqual(game.winner, TIE)

        game.throw(self.player_1, SCISSORS)
        game.throw(self.player_2, SCISSORS)
        self.assertEqual(game.winner, TIE)

        game.throw(self.player_1, ROCK)
        game.throw(self.player_2, ROCK)
        self.assertEqual(game.winner, TIE)

        self.assertEqual(self.player_1.games, 9)
        self.assertEqual(self.player_1.wins, 3)
        self.assertEqual(self.player_2.games, 9)
        self.assertEqual(self.player_2.wins, 2)
        self.assertEqual(game.round, 9)

    def test_three_gamers(self):
        self.player_1.game_type = 2
        self.player_2.game_type = 2
        self.player_3.game_type = 2

        game = Game(self.player_1, [self.player_2, self.player_3])

        game.throw(self.player_1, SCISSORS)
        game.throw(self.player_2, PAPER)
        game.throw(self.player_3, PAPER)
        self.assertEqual(game.winner, self.player_1.uid)

        game.throw(self.player_1, PAPER)
        game.throw(self.player_2, ROCK)
        game.throw(self.player_3, PASS)
        self.assertEqual(game.winner, self.player_1.uid)

        game.throw(self.player_1, ROCK)
        game.throw(self.player_2, PASS)
        game.throw(self.player_3, SCISSORS)
        self.assertEqual(game.winner, self.player_1.uid)

        game.throw(self.player_1, ROCK)
        game.throw(self.player_2, PASS)
        game.throw(self.player_3, PASS)
        self.assertEqual(game.winner, self.player_1.uid)

        game.throw(self.player_1, PASS)
        game.throw(self.player_2, PASS)
        game.throw(self.player_3, PASS)
        self.assertEqual(game.winner, TIE)

        game.throw(self.player_1, SCISSORS)
        game.throw(self.player_2, PAPER)
        game.throw(self.player_3, ROCK)
        self.assertEqual(game.winner, TIE)

        game.throw(self.player_1, SCISSORS)
        game.throw(self.player_2, ROCK)
        game.throw(self.player_3, ROCK)
        self.assertEqual(game.winner, TIE)

        self.assertEqual(self.player_1.games, 7)
        self.assertEqual(self.player_1.wins, 4)
        self.assertEqual(self.player_2.games, 7)
        self.assertEqual(self.player_2.wins, 0)
        self.assertEqual(self.player_3.games, 7)
        self.assertEqual(self.player_3.wins, 0)
        self.assertEqual(game.round, 7)


class ArenaTest(unittest.TestCase):
    def setUp(self):
        self.arena = Arena()

    def test_create_players(self):
        # Создаем пользователя
        player_1 = self.arena.create_player(name="test_1", uid=1)
        session_1 = {"id": 1, "name": "test_1"}
        self.assertTrue(isinstance(player_1, Player))

        # получаем игрока из кеша
        player_2 = self.arena.get_or_create_player(session_1, None)
        self.assertIs(player_1, player_2)

        self.assertEqual(player_2.name, "test_1")
        self.assertEqual(player_2.uid, 1)

        # проверяем список пользователей
        self.arena.create_player(name="test_2", uid=2)
        self.assertEqual(self.arena.names(), [["test_1", False], ["test_2", False]])

        # создаем еще 100 игроков, все готовы к игре
        for i in range(3, 100):
            name = f"test_{i}"
            session = {"id": i, "name": name}
            self.arena.create_player(name=name, uid=i)
            p = self.arena.get_or_create_player(session, None)
            p.ready = True

        self.assertEqual(len(self.arena.names()), 99)

        # подбираем одного случайного соперника
        self.assertEqual(len(self.arena.get_rivals(player_1)), 1)

        # подбираем 2-x соперников для игры на троих
        player_1.ready = True
        player_1.game_type = 2

        for i in range(2, 100):
            name = f"test_{i}"
            session = {"id": i, "name": name}
            p = self.arena.get_or_create_player(session, None)
            p.game_type = 2
            p.ready = True

        self.assertEqual(len(self.arena.get_rivals(player_1)), 2)


class FakeWS:
    @asyncio.coroutine
    async def send_json(self, msg):
        pass


def cancel_to_async(f):
    def wrapper(*args, **kwargs):
        coro = asyncio.coroutine(f)
        future = coro(*args, **kwargs)
        loop = asyncio.get_event_loop()
        loop.run_until_complete(future)

    return wrapper


# Тестируем манипуляции текущими играми
class GamesTest(unittest.TestCase):
    def setUp(self):
        self.arena = Arena()
        self.games = Games()

        for i in range(100):
            self.arena.create_player(i, f"Test_{i}")

    def test_two_gamers(self):
        session = {"id": random.randint(1, 99)}
        player = self.arena.get_or_create_player(session, None)
        player.ready = True
        player.ws = FakeWS()

        session = {"id": random.randint(1, 99)}
        rival = self.arena.get_or_create_player(session, None)
        rival.ready = True
        rival.ws = FakeWS()

        # создаем игру и проверяем есть ли она в кеше
        game = self.games.create_game(player, [rival])
        self.assertEqual(self.games.find_game(player), game)

        return game

    @cancel_to_async
    async def cancel_game(self):
        game = self.test_two_gamers()
        await self.games.cancel_game(game)
        self.assertFalse(len(self.games.games))


if __name__ == '__main__':
    unittest.main()
