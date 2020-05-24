import json

THROW = 'throw'
MARK_AS_READY = 'mark_as_ready'
START_NEW_ROUND = 'start_new_round'
CANCEL_GAME = 'cancel_game'
SHOW_HISTORY = 'show_history'
CHANGE_NAME = 'change_name'
CHANGE_TYPE = 'change_type'
QUEUE_UPDATES = 'queue_updates'
GAME_UPDATES = 'game_updates'
PASS = "PASS"
ROCK = "ROCK"
PAPER = "PAPER"
SCISSORS = "SCISSORS"
TIE = "TIE"


def serialize_request(method):
    async def wrapper(self, *args, **kwargs):
        assert isinstance(self.message, dict), "Request is not serializable"
        assert "action" in self.message, "Field 'action' is absent"
        assert self.message["action"] in [THROW, MARK_AS_READY, START_NEW_ROUND, CANCEL_GAME,
                                          SHOW_HISTORY, CHANGE_NAME, CHANGE_TYPE], "Unknown action"

        if self.message["action"] == THROW:
            assert "data" in self.message, "Field 'data' is absent in throw action"
            assert self.message["data"] in [PASS, ROCK, PAPER, SCISSORS], "Unsupported throw"

        if self.message["action"] == CHANGE_NAME:
            assert "data" in self.message, "Field 'data' is absent in change_name action"
            assert isinstance(self.message["data"], str), "Name must be string"
            assert len(self.message["data"]) < 20, "Name must be less then 20 characters"

        if self.message["action"] == CHANGE_TYPE:
            assert "data" in self.message, "Field 'data' is absent in change_type action"
            assert self.message["data"] in [1, 2], "Wrong game type value"

        return await method(self, *args, **kwargs)

    return wrapper


# для тестов
def serialize_response(response):
    response = json.loads(response)

    assert isinstance(response, dict), "Response is not serializable"
    assert "action" in response, "Field 'action' is absent"
    assert "result" in response, "Field 'result' is absent"
    assert response["action"] in [QUEUE_UPDATES, GAME_UPDATES], "Unknown action"

    if response["action"] == "queue_updates":
        assert "user" in response, "No user data in response"
        assert isinstance(response["user"], dict), "Response is not serializable"
        assert "queue" in response, "No users list in response"
        assert isinstance(response["queue"], list), "Response is not serializable"

        assert "uid" in response["user"], "Wrong user data"
        assert "name" in response["user"], "Wrong user data"
        assert "wins" in response["user"], "Wrong user data"
        assert "games" in response["user"], "Wrong user data"
        assert "game_type" in response["user"], "Wrong user data"
        assert "history" in response["user"], "Wrong user data"

        assert isinstance(response["user"]["history"], list), "Response is not serializable"

        for entry in response["user"]["history"]:
            assert isinstance(entry, str), "Response is not serializable"

        for gamers in response["queue"]:
            assert isinstance(gamers, list), "Response is not serializable"
            assert isinstance(gamers[0], str), "Response is not serializable"
            assert isinstance(gamers[1], bool), "Response is not serializable"
