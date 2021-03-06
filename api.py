# -*- coding: utf-8 -*-`


from itertools import izip
import endpoints
from protorpc import remote, messages
from google.appengine.api import memcache
from google.appengine.api import taskqueue
from models import User, Game, Score
from models import StringMessage, NewGameForm, GameForm, MakeMoveForm,\
    ScoreForms, GameHistory, Performance,PerformanceForms, GamesForm
from utils import get_by_urlsafe

NEW_GAME_REQUEST = endpoints.ResourceContainer(NewGameForm)
GET_GAME_REQUEST = endpoints.ResourceContainer(
    urlsafe_game_key=messages.StringField(1),
    user_name=messages.StringField(2,required=True))
GET_SCORES_LIMIT = endpoints.ResourceContainer(
    limit=messages.IntegerField(1),)
MAKE_MOVE_REQUEST = endpoints.ResourceContainer(
    MakeMoveForm,
    urlsafe_game_key=messages.StringField(1),)
USER_REQUEST = endpoints.ResourceContainer(user_name=messages.StringField(1),
                                           email=messages.StringField(2))

MEMCACHE_MOVES_REMAINING = 'MOVES_REMAINING'


@endpoints.api(name='guess_a_number', version='v1')
class HangmanApi(remote.Service):
    """Game API for Hangman"""
    @endpoints.method(request_message=USER_REQUEST,
                      response_message=StringMessage,
                      path='user',
                      name='create_user',
                      http_method='POST')
    def create_user(self, request):
        """Create a User. Requires a unique username"""
        if User.query(User.name == request.user_name).get():
            raise endpoints.ConflictException(
                'A User with that name already exists!')
        user = User(name=request.user_name, email=request.email)
        user.put()
        return StringMessage(message='User {} created!'.format(
            request.user_name))

    @endpoints.method(request_message=NEW_GAME_REQUEST,
                      response_message=GameForm,
                      path='game',
                      name='new_game',
                      http_method='POST')
    def new_game(self, request):
        """Creates new game"""
        user = User.query(User.name == request.user_name).get()
        if not user:
            raise endpoints.NotFoundException('A User with that'
                                              'name does not exist!')
        try:
            game = Game.new_game(user.key, request.attempts)
        except ValueError:
            raise endpoints.BadRequestException('Maximum must be greater '
                                                'than minimum!')

        # Use a task queue to update the average attempts remaining.
        # This operation is not needed to complete the creation of a new game
        # so it is performed out of sequence.
        taskqueue.add(url='/tasks/cache_average_attempts')
        return game.to_form('Good luck playing Guess a Number!')

    @endpoints.method(request_message=GET_GAME_REQUEST,
                      response_message=GameForm,
                      path='game/{urlsafe_game_key}',
                      name='get_game',
                      http_method='GET')
    def get_game(self, request):
        """Return the current game state."""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        user=User.query(User.name == request.user_name).get()
        if user and game and user.key == game.user:
            return game.to_form('Time to make a move!')
        else:
            raise endpoints.NotFoundException('Game not found!')

    @endpoints.method(request_message=MAKE_MOVE_REQUEST,
                      response_message=GameForm,
                      path='game/{urlsafe_game_key}',
                      name='make_move',
                      http_method='PUT')
    def make_move(self, request):
        """Makes a move. Returns a game state with message"""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if game:
            pass
        else:
            raise endpoints.BadRequestException('Game Not Found!')
        # Return if game is already Over
        if game.game_over:
            raise  endpoints.ForbiddenException('Game already over!')
        # get the target word from database. Target word is created during new
        # game.
        chosen_word = game.target
        game_history = game.game_history
        guessed_letters = game.letters_guessed
        word_guessed = []
        for i in chosen_word:
            word_guessed.append("-")
        player_guess = request.guess
        player_guess = player_guess.lower()
        if not player_guess.isalpha():
            raise endpoints.BadRequestException("That is not a"
                                                " letter. Please try again.")
        elif len(player_guess) > 1:  # check the input is signle character
            raise endpoints.BadRequestException("That is more than one letter."
                                "'Please try again.")
        # check letter is guesssed previously
        elif player_guess in guessed_letters:
            raise endpoints.BadRequestException("You have already guessed that"
                                " letter. Please try again.")
        else:
            pass
        guessed_letters.append(player_guess)
        game.letters_guessed = guessed_letters

        for letter in range(len(chosen_word)):
            for guess in guessed_letters:
                if guess == chosen_word[letter]:
                    word_guessed[letter] = guess
        joined_word = "".join(word_guessed)

        if "-" not in word_guessed:
            game.end_game(True)
            game_history.append(
                "Guess Made:<{}>. Result: Correct Guess".format(player_guess))
            game.game_history = game_history
            game.put()
            return game.to_form(
                "\nCongratulations! You Won.'"
                "' The word is:{}".format(chosen_word))

        if game.attempts_remaining == 1 and player_guess not in chosen_word:
            game.attempts_remaining -= 1
            game_history.append(
                "Guess Made:<{}>. Result: Wrong Guess".format(player_guess))
            game.game_history = game_history
            game.put()
            game.end_game(False)
            return game.to_form('All attempts made. YouLoose')

        if player_guess not in chosen_word:
            game_history.append(
                "Guess Made:<{}>. Result: Wrong Guess".format(player_guess))
            game.attempts_remaining -= 1
            game.game_history = game_history
        else:
            game_history.append(
                "Guess Made:<{}>. Result: Correct Guess".format(player_guess))
            game.game_history = game_history
        game.put()

        return game.to_form("Nice Move <{}>. Guess Other"
                            " Letter (A-Z)".format(joined_word))

    @endpoints.method(response_message=ScoreForms,
                      path='scores',
                      name='get_scores',
                      http_method='GET')
    def get_scores(self, request):
        """Return all scores from database"""
        return ScoreForms(items=[score.to_form() for score in Score.query()])

    @endpoints.method(request_message=USER_REQUEST,
                      response_message=ScoreForms,
                      path='scores/user/{user_name}',
                      name='get_user_scores',
                      http_method='GET')
    def get_user_scores(self, request):
        """Returns score of an individual User"""
        if request.user_name:
            user = User.query(User.name == request.user_name).get()
            if not user:
                raise endpoints.NotFoundException(
                    'A User with that name does not exist!')
            scores = Score.query(Score.user == user.key)
            return ScoreForms(items=[score.to_form() for score in scores])
        else:
            raise endpoints.BadRequestException(
                'Enter Valid USer Name.')

    @endpoints.method(response_message=StringMessage,
                      path='games/average_attempts',
                      name='get_average_attempts_remaining',
                      http_method='GET')
    def get_average_attempts(self, request):
        """Get the cached average moves remaining"""
        return StringMessage(
            message=memcache.get(MEMCACHE_MOVES_REMAINING) or '')

    @endpoints.method(request_message=GET_GAME_REQUEST,
                      response_message=StringMessage,
                      path='games/cancel_game/{urlsafe_game_key}',
                      name='cancel_any_game',
                      http_method='GET')
    def cancel_game(self, request):
        """Cancel game as per requested urlsafe_key"""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        user = User.query(User.name == request.user_name).get()
        if user and game and user.key == game.user:
            if game.game_over == True:
                raise endpoints.BadRequestException('Can not cancel this'
                                             'game as Game is already OVER.')
            else:
                name = game.user.get().name
                game.key.delete()
                return StringMessage(message='Game played by'
                                             'User: {} Cancelled'.format(name))
        else:
            raise endpoints.NotFoundException('Game not found!')

    @endpoints.method(request_message=GET_SCORES_LIMIT,
                      response_message=ScoreForms,
                      path='games/high_scores',
                      name='get_high_scores',
                      http_method='GET')
    def get_high_scores(self, request):
        "Get scores of all users, higher scores on top"
        limit = 5
        if request.limit:
            limit = request.limit

        scores =\
            Score.query().order(-Score.won).order(Score.guesses).fetch(limit)
        if scores:
            return ScoreForms(items=[score.to_form() for score in scores])
        else:
            raise endpoints.NotFoundException("Score Board Empty.")

    @endpoints.method(request_message=USER_REQUEST,
                      response_message=GamesForm,
                      path='games/user_games/{user_name}',
                      name='get_user_games',
                      http_method='GET')
    def get_user_games(self, request):
        """Get the list of all active games of a users """
        user = User.query(User.name == request.user_name).get()
        if user:
            game = Game.query(Game.game_over == False, Game.user == user.key)
            if game.count():
                return GamesForm(
                    mess=[active.to_form("Games Stat") for active in game])
            else:
                raise endpoints.ForbiddenException('No active'
                                                   ' game for requested User')
        else:
            raise endpoints.ForbiddenException('User Name does not Exist')

    @endpoints.method(response_message=PerformanceForms,
                      path='games/users_ranking',
                      name='get_users_ranking',
                      http_method='GET')
    def get_users_ranking(self, request):
        "Get ranking of all users based on performance"
        user=User.query()
        entity=Performance.query()
        for each in entity:
            each.key.delete()
        for each_user in user:
            game=Score.query(Score.user == each_user.key)
            total_performance=0.0
            for each in game:
                factor=0
                if each.won == True:
                    factor=1
                total_performance =total_performance+(factor* each.performance)
            each_user.add_performance(total_performance)
        players = Performance.query().order(-Performance.performance)
        rank_list=[]
        count=players.count()
        if count:
            for player, rank in izip(players, range(count)):
                rank_list.append(player.to_form(rank=rank+1))
            return PerformanceForms(
                                 ranks=rank_list)
        else:
            raise endpoints.NotFoundException("Performance board Empty")


    @endpoints.method(request_message=GET_GAME_REQUEST,
                      response_message=GameHistory,
                      path='games/games_history/{urlsafe_game_key}',
                      name='get_games_history',
                      http_method='GET')
    def get_games_history(self, request):
        "Get history of all moves of all games."
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        user = User.query(User.name == request.user_name).get()
        if user and game and user.key == game.user:
            return game.to_form_game()
        else:
            raise endpoints.NotFoundException('Game not found!')

    @staticmethod
    def _cache_average_attempts():
        """Populates memcache with the average moves remaining of Games"""
        games = Game.query(Game.game_over == False).fetch()
        if games:
            count = len(games)
            total_attempts_remaining = sum([game.attempts_remaining
                                            for game in games])
            average = float(total_attempts_remaining)/count
            memcache.set(MEMCACHE_MOVES_REMAINING,
                         'The average moves '
                         'remaining is {:.2f}'.format(average))


api = endpoints.api_server([HangmanApi])
