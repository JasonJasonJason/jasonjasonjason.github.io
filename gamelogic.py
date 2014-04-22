import random
import banklogic
import json
import logging

class Card(object):
  def __init__(self, newSuite, newNumber):
    self.suite = newSuite
    self.number = newNumber

  def getValue(self):
    if self.number >= 10:
      return 10
    if self.number == 1:
      return 11
    else:
      return self.number

  def getDict(self):
    return {
      'suite': self.suite,
      'number': self.number
    }


class Hand(object):

  def __init__(self, newDeck):
    self.cards  = []

    self.deck = newDeck

    self.hitMe()
    self.hitMe()

  def hitMe(self):
    if len(self.cards) < 5 and self.score() < 21:
      self.cards.append(self.deck.deal());

  def score(self):
    score = 0
    aces = 0

    for card in self.cards:
      value = card.getValue()
      if value == 11:
        aces  += 1
        score += 10
      else:
        score += value

    while score > 20 and aces > 0:
      score -= 10
      aces -= 1

    return score

  def getDict(self):
    cardsDictList = []
    for card in self.cards:
      cardsDictList.append(card.getDict())
    return cardsDictList


class Deck(object):

  def __init__(self):
    self.cards = []
    for i in range(1, 53):
      suite  = 1 + i%4
      number = 1 + i%13
      self.cards.append(Card(suite, number))

  def shuffle(self):
    for i in range(0,52):
      randomIndex = random.randrange(52)
      self.cards[i], self.cards[randomIndex] = self.cards[randomIndex], self.cards[i]

  def deal(self):
    return self.cards.pop()


class Dealer():
  def __init__(self, deck):
    self.hand = Hand(deck)

  def getHand(self):
    return self.hand

  def getDict(self):
    return self.hand.getDict()

  def hitMe(self):
    self.hand.hitMe()


class User():
  def __init__(self, deck, new_id):
    
    self.bet = 0
    self.game_result = ''
    self.user_id = new_id
    self.hand = Hand(deck)
    self.getAPIInfo()

  def getAPIInfo(self):
    # Call the banking API to get current balance
    # Example: casino.curtiswendel.me:3000/api/getUser/1
    self.balance = 0
    self.name = 'User'
    try:
      result = banklogic.getUser(self.user_id)
      if result:
        self.balance = result['balance']
        self.name = result['screenName']
    except Exception as e:
      logging.error('Error while checking user balance...' + str(e))
      pass


  def getHand(self):
    return self.hand


  def getDict(self):
    if self.hand:
      cards_result = self.hand.getDict()
    else:
      cards_result = ''

    return {
      'cards': cards_result,
      'bet'  :self.bet,
      'game_result': self.game_result,
      'user_id':self.user_id,
      'balance':self.balance,
      'name':self.name
    }

  def hitMe(self):
    logging.info('user hand score: ' + str(self.hand.score()))
    if(self.hand.score() < 21):
      self.hand.hitMe()


  def changeBet(self, increaseAmount):
    responseJSON = banklogic.requestFunds(self.user_id, increaseAmount)
    if responseJSON:
      logging.info('Raw data from \'RequestFunds\': ' + responseJSON)
      response = json.loads(responseJSON)
      if 'error' in response:
        logging.error('Error received from \'RequestFunds\': ' + response['error'])
        raise ValueError( "Insufficient funds!" )
      else:
        self.bet += increaseAmount
        self.balance -= increaseAmount
    else:
      logging.error('no response from \'RequestFunds\'')

  def setGameResult(self, dealerHand):
    if self.hand.score() > 21:
      self.game_result = 'user_bust'
    elif dealerHand.score() > 21:
      self.game_result = 'dealer_bust'
    elif self.hand.score() <= dealerHand.score():
      self.game_result = 'dealer_win'
    else:
      self.game_result = 'user_win'

    if self.game_result == 'user_win' or self.game_result == 'dealer_bust':
      # add in twice the amount of the bet, because the amount of the bet was deducted when they placed the bet.
      # add in once to get to original amount, twice to actually add $
      banklogic.addTransaction(self.user_id, 2*self.bet)
    else:
      banklogic.addTransaction(self.user_id, -self.bet)
