import datetime
import logging
import os
import random
random.seed()
import re
import sys
import time
import json
from gamelogic import *
from banklogic import *
from pprint import pprint
from google.appengine.api import channel
from google.appengine.api import users
from google.appengine.ext import ndb
from google.appengine.ext import webapp
from google.appengine.ext import deferred
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app

DEPLOY = True

class GAME_STATE:
  END_GAME  = 'end_game'
  USER_TURN = 'user_turn'

class Game(ndb.Model):
    """All the data we store for a game"""
    dealer          = ndb.PickleProperty()
    users           = ndb.PickleProperty()
    game_key        = ndb.StringProperty()
    current_user_id = ndb.StringProperty()
    deck            = ndb.PickleProperty()
    state           = ndb.StringProperty()
    end_message     = ndb.StringProperty()
    game_link       = ''


    def addUser(self, newUserId):
        
        for user in self.users: #Already added to game!!
            if user.user_id == newUserId:
                return user

        users_list = [user.getDict() for user in self.users]
        user = User(self.deck, newUserId)

        if not self.users or len(self.users) == 0:
            self.users = []
            self.current_user_id = user.user_id

        self.users.append(user)

        return user

    def printGame(self):
        users_list = [user.getDict() for user in self.users]

        gameUpdate = {
            'dealer'          : self.dealer.getDict(),
            'users'           : users_list,
            'current_user_id' : self.current_user_id,
            'state'           : self.state,
            'end_message'     : self.end_message
        }
        logging.info('Game information: ' + str(json.dumps(gameUpdate, indent=4)))


def generateGameKey():
    return random.randrange(100)

def generateUserId():
    return random.randrange(9)+1

def createNewGame(game_key):
    deck = Deck()
    deck.shuffle()
    dealer = Dealer(deck)
    return Game(
                game_key        = game_key,
                dealer          = dealer,
                users           = [],
                deck            = deck,
                current_user_id = '0',
                state           = GAME_STATE.USER_TURN,
                end_message     = 'Waiting for next round'
                )

def resetGame(game):
    game.deck = Deck()
    game.deck.shuffle()
    game.dealer = Dealer(game.deck)
    game.users = []
    game.current_user_id = '0'
    game.state = GAME_STATE.USER_TURN
    game.end_message = 'Waiting for next round'
    return game

class GameUpdater():
  game = None

  def __init__(self, game):
    self.game = game

  def get_game_message_for_user(self, current_user):
    users_list = [user.getDict() for user in self.game.users if user != current_user]

    gameUpdate = {
      'dealer'          : self.game.dealer.getDict(),
      'users'           : users_list,
      'me'              : current_user.getDict(),
      'current_user_id' : self.game.current_user_id,
      'state'           : self.game.state,
      'end_message'     : self.game.end_message
    }
    # logging.info('JSON game update: ' + str(json.dumps(gameUpdate, indent=4)))
    return json.dumps(gameUpdate)

  def send_update(self):
    for user in self.game.users:
        message = self.get_game_message_for_user(user)
        channel.send_message(user.user_id + self.game.game_key, message)

  def send_user_update(self, user, message):
    channel.send_message(user.user_id + self.game.game_key, message)
    

class GameFromRequest():

  game = None;

  def __init__(self, request):
    user = users.get_current_user()
    game_key = request.get('g')

    ctx = ndb.get_context()
    ctx.clear_cache()

    game_from_db = Game.query(Game.game_key == game_key).fetch(1)
    if not game_from_db or len(game_from_db) == 0:
        time.sleep(2)
        ctx = ndb.get_context()
        ctx.clear_cache()
        game_from_db = Game.query(Game.game_key == game_key).fetch(1)
    self.game = game_from_db[0]

  def get_game(self):
    return self.game


class OpenedPage(webapp.RequestHandler):
    def post(self):
        user_id = self.request.get('user_id')
        game = GameFromRequest(self.request).get_game()
        new_user = game.addUser(user_id)
        game.put()

        if game.state == GAME_STATE.END_GAME:
            GameUpdater(game).send_user_update(new_user, json.dumps({'error':'Waiting to start...'}))
        else:
            GameUpdater(game).send_update()

class ClosedPage(webapp.RequestHandler):
    def post(self):
        id   = self.request.get('user_id')
        game = GameFromRequest(self.request).get_game()
        user = None

        # Find current user
        for i in range(0, len(game.users)):
            if id == game.users[i].user_id:
                user = game.users[i]

        if user == None:
            logging.error('[ClosedPage]. Could not find user in game.users! Doing nothing.')
            return

        
        if game.state == GAME_STATE.END_GAME:
            # game has already ended. Let people leave freely, don't update anyone.
            game.users.remove(user)
            game.put()
        else:
            if user.user_id == game.current_user_id:
                # user is current user...
                # delete user, move to next user.
                # if last user, end game.
                updateGameState(game)
                game.users.remove(user)
                onGameStateChanged(game)
            else: 
                # user is not current user
                # delete user, send update, do nothing about it tho
                game.users.remove(user)
                game.put()
                GameUpdater(game).send_update()

        game.put()

        if len(game.users) == 0:
            game.key.delete();

        
class ClearPage(webapp.RequestHandler):
    def get(self):
        games = Game.query().fetch()
        for game in games:
            game.key.delete()
        self.redirect('/?' + self.request.get('userID'))
        

class NewGamePage(webapp.RequestHandler):
    def post(self):
        game = GameFromRequest(self.request).get_game()
        if game.state != GAME_STATE.END_GAME:
            return

        users = game.users

        game = resetGame(game)
        for user in users:
            game.addUser(user.user_id)

        game.state = GAME_STATE.USER_TURN
        game.put()
        time.sleep(1)
        GameUpdater(game).send_update()

class BetPage(webapp.RequestHandler):
  def post(self):
    game = GameFromRequest(self.request).get_game()
    id = self.request.get('user_id')
    betAmount = int(self.request.get('bet_amount'))
    logging.info('betting for user_id: ' + str(id) + ' with bet amount: ' + str(betAmount))
    betForUser(game, id, betAmount)

class HitPage(webapp.RequestHandler):
  def post(self):
    game = GameFromRequest(self.request).get_game()
    id = self.request.get('user_id')
    logging.info('hitting for user_id: ' + str(id))
    hitForUser(game, id)

class StandPage(webapp.RequestHandler):
  def post(self):
    game = GameFromRequest(self.request).get_game()
    id = self.request.get('user_id')
    logging.info('standing for user_id: ' + str(id))
    standForUser(game, id)  

def hitForUser(game, id):
    current_user = next((user for user in game.users if user.user_id == id), None) 

    if current_user.user_id != game.current_user_id:
        GameUpdater(game).send_user_update(current_user, json.dumps({'error':'It\'s not your turn!'}))
        return
    if game.state == GAME_STATE.END_GAME:
        GameUpdater(game).send_user_update(current_user, json.dumps({'error':'Cannot bet now!'}))
        return

    if len(current_user.getHand().cards) < 5:
        current_user.hitMe()
    game.put()
    GameUpdater(game).send_update()

def standForUser(game, id):
    current_user = next((user for user in game.users if user.user_id == id), None)
    if current_user.user_id != game.current_user_id:
        GameUpdater(game).send_user_update(current_user, json.dumps({'error':'It\'s not your turn!'}))
        return
    
    updateGameState(game)
    onGameStateChanged(game)

def betForUser(game, id, betAmount):
    current_user = next((user for user in game.users if user.user_id == id), None)
    if current_user.user_id != game.current_user_id:
        GameUpdater(game).send_user_update(current_user, json.dumps({'error':'It\'s not your turn!'}))
        return

    try:
        current_user.changeBet(betAmount);
        game.put()
        GameUpdater(game).send_update()
    except ValueError, ex:
        GameUpdater(game).send_user_update(current_user, json.dumps({'error':str(ex)}))


def finishGame(game):
    game.state = GAME_STATE.END_GAME

    while game.dealer.getHand().score() < 18:
        game.dealer.hitMe()

    for user in game.users:
        user.setGameResult(game.dealer.getHand())


    
def updateGameState(game):
    for i in range(0, len(game.users)):
        # All users set, end the game
        if game.state == GAME_STATE.USER_TURN and i == len(game.users)-1:
            finishGame(game)
            
        # Proceed to next user
        elif game.users[i].user_id == game.current_user_id:
            game.current_user_id = game.users[(i+1) % len(game.users)].user_id
            return

def onGameStateChanged(game):
    game.put()
    GameUpdater(game).send_update()

    if game.state == GAME_STATE.END_GAME:

        ctx = ndb.get_context()
        ctx.clear_cache()
        time.sleep(5)
            
        games = Game.query(Game.game_key == game.game_key).fetch(1)
        if games and len(games) > 0: #May have been deleted upon browser closing
            new_game = games[0]
            users = new_game.users
            new_game = resetGame (new_game)

            for user in users:
                new_game.addUser(user.user_id)

            new_game.state = GAME_STATE.USER_TURN
            new_game.put()
            GameUpdater(new_game).send_update()


class Page(webapp.RequestHandler):
    def get(self):
        return

    def sendGameInfo(self, game, user_id):
        token = channel.create_channel(user_id + game.game_key)
        template_values = {
                           'token': token,
                           'game_key': game.game_key,
                           'user_id' : user_id,
                           'deploy'  : DEPLOY
                          }
        path = os.path.join(os.path.dirname(__file__), 'index.html')

        self.response.out.write(template.render(path,template_values))  

class MainPage(Page):
    """The main UI page, renders the 'index.html' template."""

    def get(self):
        game_key = self.request.get('g')
        user_id = self.request.get('userID')
        if not user_id:
            if self.request.arguments():
                user_id = self.request.arguments()[0]
            else:
                user_id = 1

        if not game_key:
            self.showGameMenu(user_id)
            return

        games = Game.query(Game.game_key == game_key).fetch(1)
        if games:
            game = games[0]
        else:
            game = createNewGame(game_key)
            game.put()

        if game:
            self.sendGameInfo(game, user_id);
        else:
            self.response.out.write('No such game')

    def showGameMenu(self, user_id):
        games = Game.query().fetch()
        index = 1
        for game in games:
            if DEPLOY:
                game.game_link = 'http://blackjack-game.appspot.com/?g=' + game.game_key
            else:
                game.game_link = 'http://localhost:8080/?g=' + game.game_key
            game.game_number = index
            game.number_of_players = len(game.users)
            if game.number_of_players > 0:
                index += 1

        template_values = { 'games': games, 'user_id':user_id, 'new_game_id':generateGameKey(), 'deploy':DEPLOY }
        path = os.path.join(os.path.dirname(__file__), 'menu.html')

        self.response.out.write(template.render(path,template_values))  

        #Delete all games with 0 players that are left over
        for game in games:
            if game.number_of_players < 1:
                game.key.delete()


application = webapp.WSGIApplication([
    ('/',       MainPage),
    ('/hit',    HitPage),
    ('/stand',  StandPage),
    ('/bet',    BetPage),
    ('/opened', OpenedPage),
    ('/closed', ClosedPage),
    ('/again',  NewGamePage),
    ('/clear',  ClearPage)], debug=True)


def main():
  run_wsgi_app(application)


if __name__ == "__main__":
  main()
