import datetime
import random
import uuid

PASS = "PASS"
ROCK = "ROCK"
PAPER = "PAPER"
SCISSORS = "SCISSORS"
TIE = "TIE"


class Player:
    def __init__(self, uid=None, name=None, ws=None):
        self.uid = uid if uid else int(str(uuid.uuid1().int)[-6:])
        self.name = name if name else f"User_{self.uid}"
        self.ws = ws
        self.wins = 0
        self.games = 0
        self.ready = False
        self.game_type = 1
        self.history = []

    def to_dict(self):
        return {key: val for key, val in self.__dict__.items() if key != 'ws'}


class Arena:
    def __init__(self):
        self.players = []
        self.current_index = 0

    def __iter__(self):
        return self

    def __next__(self):
        self.current_index += 1

        if len(self.players) == 0 or self.current_index > len(self.players):
            raise StopIteration

        return self.players[self.current_index - 1]

    def create_player(self, uid=None, name=None, ws=None):
        player = Player(uid, name, ws)
        self.players.append(player)
        return player

    def get_or_create_player(self, session, ws):
        player = [u for u in self.players if u.uid == session["id"]]

        if not len(player):
            player = self.create_player(session["id"], session["name"], ws)
        else:
            player = player[0]
            player.ws = ws

        return player

    def remove_player(self, ws):
        self.players = list(filter(lambda u: u.ws is not ws, self.players))

    def names(self):
        return [[u.name, u.ready] for u in self.players]

    def get_rivals(self, gamer):
        def rival(g):
            return g is not gamer and g.ready and g.game_type == gamer.game_type

        all_rivals = list(filter(rival, self.players))

        if len(all_rivals) < gamer.game_type:
            return None

        elif len(all_rivals) == gamer.game_type:
            for r in all_rivals:
                r.ready = False
            return all_rivals

        else:
            rivals = [random.choice(all_rivals) for _ in range(gamer.game_type)]
            for r in rivals:
                r.ready = False
            return rivals

    async def broadcast(self, recipients=None, exclude=None):
        players = recipients if recipients else self.players

        for player in players:
            if exclude and player in exclude:
                continue

            await player.ws.send_json({
                "action": "queue_updates",
                "result": "Done",
                "user": player.to_dict(),
                "queue": self.names()
            })


class Games:
    def __init__(self):
        self.games = []

    def create_game(self, user, rivals):
        game = Game(user, rivals)
        self.games.append(game)
        return game

    def find_game(self, gamer):
        game = [g for g in self.games if g.user_in_game(gamer.uid)]
        return game[0] if len(game) else None

    async def cancel_game(self, game):
        game.status = "canceled"
        await game.broadcast()

        self.games.remove(game)


class Game:
    def __init__(self, user, rivals: list):
        self.status = "started"
        self.round = 1
        self.winner = None
        self.throws = {}
        self.players = list(rivals)
        self.players.insert(0, user)

    def user_in_game(self, uid):
        return bool([g for g in self.players if g.uid == uid])

    def stat(self):
        players = []
        for p in self.players:
            players.append({
                "uid": p.uid,
                "name": p.name,
                "wins": p.wins,
                "games": p.games,
            })

        return {
            "status": self.status,
            "round": self.round,
            "winner": self.winner,
            "throws": self.throws,
            "players": players
        }

    def throw(self, user, value):
        if self.status == "finished":
            self.reset()
        else:
            self.process()

        # Игнорируем второй ход одного игрока рамках одного раунда
        if user.uid in self.throws:
            return
        self.throws[user.uid] = value

        if len(self.throws) == len(self.players):
            if len(self.players) == 2:
                self.two_players()
            elif len(self.players) == 3:
                self.three_players()

    def start_new_round(self):
        # Если раунд еше не завершен игнорируем команду
        if self.status == "finished":
            self.reset()

    def two_players(self):
        winning_throw = self.play(self.throws.values())
        if winning_throw == TIE:
            self.winner = TIE

        for player in self.players:
            player.games += 1
            if self.throws[player.uid] == winning_throw:
                self.winner = player.uid
                player.wins += 1

        self.finish()

    def three_players(self):
        winners = []
        winning_throw = self.play(self.throws.values())

        for player in self.players:
            player.games += 1
            if self.throws[player.uid] == winning_throw:
                winners.append(player)

        if len(winners) == 1:
            self.winner = winners[0].uid
            winners[0].wins += 1
        else:
            self.winner = TIE

        self.finish()

    def process(self):
        self.status = "processing"

    def finish(self):
        self.status = "finished"
        self.log()

    def reset(self):
        self.round += 1
        self.status = "processing"
        self.throws = {}
        self.winner = None

    def log(self):
        participants = [g.name for g in self.players]
        entry = f"{datetime.datetime.now()} game {self.status} rounds #{self.round} " \
                f"participants: {participants} winner: {self.winner}\n"

        for gamer in self.players:
            gamer.history.append(entry)

    @staticmethod
    def play(throws):
        throws = list(set(throws))
        if len(throws) == 1:
            return TIE

        if PASS in throws:
            throws.remove(PASS)
        if len(throws) == 1:
            return throws[0]
        if len(throws) == 3:
            return TIE

        if (throws[0] == ROCK and throws[1] == SCISSORS) \
                or (throws[0] == SCISSORS and throws[1] == PAPER) \
                or (throws[0] == PAPER and throws[1] == ROCK):
            return throws[0]
        else:
            return throws[1]

    async def broadcast(self):
        stat = self.stat()

        for gamer in self.players:
            await gamer.ws.send_json({
                "action": "game_updates",
                "result": "Done",
                "game_stat": stat
            })
