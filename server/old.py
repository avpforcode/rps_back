import json
from aiohttp import web, WSMsgType
from aiohttp_session import get_session
from models import Game


async def websocket_handler(request):
  ws = web.WebSocketResponse()
  await ws.prepare(request)

  session = await get_session(request)
  if 'id' not in session: return ws

  player = request.app.arena.get_or_create_player(session, ws)
  await request.app.arena.broadcast()

  async for msg in ws:
    if msg.type == WSMsgType.TEXT:
      data = json.loads(msg.data)

      if data["action"] == 'mark_as_ready':
        rivals = request.app.arena.get_rivals(player)

        if not rivals:
          player.ready = True
          await request.app.arena.broadcast()
        else:
          game = Game(player, rivals)
          request.app.games.append(game)

          await game.broadcast()
          await request.app.arena.broadcast(exclude = rivals + [player])
          await request.app.arena.broadcast()

      elif data["action"] == 'throw':
        game = request.app.games.find_game(player)
        if game:
          game.throw(player, data["data"])
          await game.broadcast()

      elif data["action"] == 'start_new_round':
        game = request.app.games.find_game(player)
        if game:
          game.start_new_round()
          await game.broadcast()

      elif data["action"] == 'cancel_game':
        game = request.app.games.find_game(player)
        if game:
          await request.app.games.cancel_game(game)

        await request.app.arena.broadcast()

      elif data["action"] == 'show_history':
        await player.ws.send_json(player.history)

      elif data["action"] == 'change_name':
        player.name = data["data"]
        await request.app.arena.broadcast()

      elif data["action"] == 'change_type':
        player.game_type = data["data"]
        await request.app.arena.broadcast()

      else:
        await ws.send_json({"action": "Unknown", "result": "Fail"})


    elif msg.type == WSMsgType.ERROR:
      print(ws.exception())

  game = request.app.games.find_game(player)
  if game:
    await request.app.games.cancel_game(game)

  # request.app.arena.remove_player(ws)
  await request.app.arena.broadcast()

  return ws