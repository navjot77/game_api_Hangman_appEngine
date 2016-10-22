#Full Stack Nanodegree Project

## Set-Up Instructions:
1.  Update the value of application in app.yaml to the app ID you have registered
 in the App Engine admin console and would like to use to host your instance of this sample.
2.  Run the app with the devserver using dev_appserver.py DIR, and ensure it's
 running by visiting the API Explorer - by default localhost:8080/_ah/api/explorer.
Deploy your application.

 
##Game Description:
Hangman games is simple one player game. Player needs to guess a word.
User needs to enter the letter. And if letter matches tghe target word then
User will be shown string with letter placed in right position and others
letters  will be marked as '-'. User will be given 5 number of chances to guess
the word. User can resume the game anytime. Each game can be retrieved or
 played by using the path parameter `urlsafe_game_key`.

##Playing Instructions.
Player need to register first by using API 'create_user'. Email and unique user
name is required for registration.
To play a game, user needs to start a new game. Use appropriate API methods
given below. On success new_game, urlsafe key will be provided. User needs to
keep this string saved. And then to start a game, User need to use API
 'make_a_move'. It requires the urlsafe key to be entered.
For other actions as to get score, history, performance, cancel a game etc,
read below API methods.

##Files Included:
 - api.py: Contains endpoints and game playing logic.
 - app.yaml: App configuration.
 - cron.yaml: Cronjob configuration.
 - main.py: Handler for taskqueue handler.
 - models.py: Entity and message definitions including helper methods.
 - utils.py: Helper function for retrieving ndb.Models by urlsafe Key string.

##Endpoints Included:
 - **create_user**
    - Path: 'user'
    - Method: POST
    - Parameters: user_name, email (optional)
    - Returns: Message confirming creation of the User.
    - Description: Creates a new User. user_name provided must be unique. Will 
    raise a ConflictException if a User with that user_name already exists.
    
 - **new_game**
    - Path: 'game'
    - Method: POST
    - Parameters: user_name
    - Returns: GameForm with initial game state.
    - Description: Creates a new Game. user_name provided must correspond to an
    existing user - will raise a NotFoundException if not. Min must be less than
    max. Also adds a task to a task queue to update the average moves remaining
    for active games. Attempts is hard-coded in code for all games and for all
    users.
     
 - **get_game**
    - Path: 'game/{urlsafe_game_key}'
    - Method: GET
    - Parameters: urlsafe_game_key
    - Returns: GameForm with current game state.
    - Description: Returns the current state of a game.
    
 - **make_move**
    - Path: 'game/{urlsafe_game_key}'
    - Method: PUT
    - Parameters: urlsafe_game_key, guess
    - Returns: GameForm with new game state.
    - Description: Accepts a 'guess' and returns the updated state of the game.
    If this causes a game to end, a corresponding Score entity will be created.
    
 - **get_scores**
    - Path: 'scores'
    - Method: GET
    - Parameters: None
    - Returns: ScoreForms.
    - Description: Returns all Scores in the database (unordered).
    
 - **get_user_scores**
    - Path: 'scores/user/{user_name}'
    - Method: GET
    - Parameters: user_name
    - Returns: ScoreForms. 
    - Description: Returns all Scores recorded by the provided player(unordered).
    Will raise a NotFoundException if the User does not exist.
    
 - **get_active_game_count**
    - Path: 'games/active'
    - Method: GET
    - Parameters: None
    - Returns: StringMessage
    - Description: Gets the average number of attempts remaining for all games
    from a previously cached memcache key.

 - **get_active_games**
    - Path: 'games/active_users'
    - Method: GET
    - Parameters: None
    - Returns: StringMessages
    - Description: This returns list of all User's with active games.

 - **get_game_history**
    - Path: 'games/games_history/{urlsafe_game_key}'
    - Method: GET
    - Parameters: urlsafe_game_key
    - Returns: GameHistory
    - Description: This returns history of moves of requested game.

 - **get_users_ranking**
    - Path: 'games/users_ranking'
    - Method: GET
    - Parameters: None
    - Returns: RankingForms
    - Description: This returns list of all User's with ranks, name, score.

 - **get_high_scores**
    - Path: 'games/high_scores'
    - Method: GET
    - Parameters: limit(Optional)
    - Returns: ScoreForms
    - Description: This returns list of all ScoreForm with Increasing Scores.
                  Limit is optional, which limits the output to certain number.

 - **cancel_any_game**
    - Path: 'games/cancel_game/{urlsafe_key}'
    - Method: GET
    - Parameters: urlsafe_key
    - Returns: StringMessages
    - Description: This will receive the urlsafe_key from user, which will be
     mapped to key in Game datastore. On success, the entry from Game table
     will be deleted and Success message will be returned.

##Models Included:
 - **User**
    - Stores unique user_name and (optional) email address.
    
 - **Game**
    - Stores unique game states. Associated with User model via KeyProperty.
    
 - **Score**
    - Records completed games. Associated with Users model via KeyProperty.
    
##Forms Included:
 - **GameForm**
    - Representation of a Game's state (urlsafe_key, attempts_remaining,
    game_over flag, message, user_name).
 - **NewGameForm**
    - Used to create a new game (user_name, min, max, attempts)
 - **MakeMoveForm**
    - Inbound make move form (guess).
 - **ScoreForm**
    - Representation of a completed game's Score (user_name, date, won flag,
    guesses).
 - **ScoreForms**
    - Multiple ScoreForm container.
 - **RankingForm**
    - Representation of Username, ranks and score.
 - **RankingForms**
    - Multiple RankingForm representation.
 - **StringMessage**
    - General purpose String container.
 - **StringMessages**
    - Multiple StringMessage container.
 - **GameHistory**
    - Representation of Game's History, user_name, game_over and target_word.
 - **GamesHistory**
    - Multiple GameHistory container.
