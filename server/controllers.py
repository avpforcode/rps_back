import json
from aiohttp import WSMsgType
from serializers import serialize_request


class WSException(Exception):
  def __init__(self, message):
    self.message = message

  def __repr__(self):
    str(self.message)


class WSController:
  error_body = {"result": "Fail", "data": None}

  def __init__(self, message, request):
    if message.type == WSMsgType.ERROR:
      self.client_error("unknown")

    self.request = request
    self.message = message.data
    self.arena = getattr(request.app, 'arena')
    self.games = getattr(request.app, 'games')
    self.player = getattr(request, 'user')

  def client_error(self, msg):
    self.error_body["data"] = msg
    raise WSException(self.error_body)

  @serialize_request
  async def handle(self):
    method = getattr(self, self.message["action"], None)
    if not method:
      self.client_error("Unsupported action")
    else:
      await method(**self.message)


class JsonWSController(WSController):
  def __init__(self, message, request):
    super().__init__(message, request)

    try:
      self.message = json.loads(self.message)
    except json.JSONDecodeError:
      raise self.client_error("message not serializable")


class ActionsController(JsonWSController):
  async def mark_as_ready(self, **kwargs):
    rivals = self.arena.get_rivals(self.player)

    if not rivals:
      self.player.ready = True
      await self.arena.broadcast()
    else:
      game = self.games.create_game(self.player, rivals)

      await game.broadcast()
      await self.arena.broadcast(exclude = rivals + [self.player])

  async def throw(self, **kwargs):
    game = self.games.find_game(self.player)
    if game:
      game.throw(self.player, kwargs["data"])
      await game.broadcast()

  async def start_new_round(self, **kwargs):
    game = self.games.find_game(self.player)
    if game:
      game.start_new_round()
      await game.broadcast()

  async def cancel_game(self, **kwargs):
    game = self.games.find_game(self.player)
    if game:
      await self.games.cancel_game(game)

    await self.arena.broadcast()

  async def show_history(self, **kwargs):
    await self.player.ws.send_json(self.player.history)

  async def change_name(self, **kwargs):
    self.player.name = kwargs["data"]
    await self.arena.broadcast()

  async def change_type(self, **kwargs):
    self.player.game_type = kwargs["data"]
    await self.arena.broadcast()