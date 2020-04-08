import traceback, sys
from aiohttp import web
from aiohttp.web_exceptions import HTTPInternalServerError
from aiohttp_session import get_session
from aiohttp_jinja2 import template
from controllers import ActionsController, WSException
from logs import create_log


@template('index.html')
async def init_handler(request):
  session = await get_session(request)

  if 'id' not in session:
    player = request.app.arena.create_player()
    session["id"] = player.uid
    session["name"] = player.name

  return {}


class ConnectWSView(web.View):
  async def get(self):
    ws = web.WebSocketResponse()
    await ws.prepare(self.request)
    return ws


class SessionWSView(ConnectWSView):
  async def get(self):
    ws = await super().get()
    session = await get_session(self.request)

    if 'id' not in session: return ws

    arena = getattr(self.request.app, 'arena', None)
    if not arena: raise HTTPInternalServerError()

    player = arena.get_or_create_player(session, ws)
    await arena.broadcast()

    setattr(self.request, 'user', player)

    return ws


class MainWSView(SessionWSView):
  async def quit(self):
    arena = getattr(self.request.app, 'arena', None)
    player = getattr(self.request, 'user', None)
    games = getattr(self.request.app, 'games', None)
    game = games.find_game(player)

    if games.find_game(player):
      await games.cancel_game(game)

    # arena.remove_player(ws)
    await arena.broadcast()

  async def get(self):
    ws = await super().get()

    async for msg in ws:
      try:
        controller = ActionsController(msg, self.request)
        await controller.handle()
      except AssertionError as e:
        await ws.send_json({"result":"Fail", "data": e.__str__()})
      except WSException as e:
        await ws.send_json(e.message)
      except:
        log = create_log('rps')
        log.error("Unpredictable exception:\n {}".format(
          "".join(traceback.format_exception(*sys.exc_info()))
        ))
        await ws.send_json({"result": "Fail", "data": "Unknown error"})

    await self.quit()

    return ws