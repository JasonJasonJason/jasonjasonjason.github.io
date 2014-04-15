import random

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

  def total(self):
    aces = self.cards.count(11)
    t = sum(self.cards)
    if t > 21 and aces > 0:
        while aces > 0 and t > 21:
            t -= 10
            aces -= 1
    return t

  def score(self):
    score = 0
    aces = 0

    for card in self.cards:
      value = card.getValue()
      if value == 1:
        aces += 1
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
    self.hand = Hand(deck)
    self.bet = 0
    self.game_result = ''
    self.user_id = new_id

  def getHand(self):
    return self.hand

  def getDict(self):
    return {
      'cards':self.hand.getDict(),
      'bust' :(self.hand.score() > 21),
      'bet'  :self.bet,
      'game_result': self.game_result,
      'user_id':self.user_id
      }

  def hitMe(self):
    if(self.hand.score() < 21):
      self.hand.hitMe()

  def changeBet(self, increaseAmount):
    self.bet += increaseAmount

  def setGameResult(self, dealerHand):
  	if self.hand.score() > 21:
  		self.game_result = 'user_bust'
  	elif dealerHand.score() > 21:
  		self.game_result = 'dealer_bust'
  	elif self.hand.score() <= dealerHand.score():
  		self.game_result = 'dealer_win'
  	else:
  		self.game_result = 'user_win'






