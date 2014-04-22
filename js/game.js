var Hand = function (newCards){

    var cards = [];

    for(var i=0; i<newCards.length; i++){
        cards.push(newCards[i]);
        console.log('new card: ' + cards[i].suite + ', ' + cards[i].number);
    }

    this.getHand = function(){
        return cards;
    }
    this.setHand = function(newCards){
        cards = newCards;
    }

    this.hitMe = function(){
        console.log('hitting hand');
    }
};


var Player = function (){

    var userId = 0;
    var cash = 0.0;
    var hand = null;
    var betAmount = 0.0;
    var onCashChangedCallback;
    var onBetChanged;

    this.setUserId = function(id){
        userId = id;
    }
    this.getUserId = function(){
        return userId;
    }

    this.getCash = function(){
        return cash;
    }
    this.deductCash = function(deductAmount){
        cash = cash-deductAmount;
        onCashChanged();
    }

    this.increaseBet = function(increaseBetAmount){
        betAmount += increaseBetAmount;
        cash -= increaseBetAmount;
        onCashChanged();
        onBetChanged();
    }
    this.getCurrentBet = function(){
        return betAmount;
    }
    this.lostBet = function(){
        console.log("User "+userId+" lost their bet amount of " + this.getCurrentBet() + ". New cash amount: " + cash);
        betAmount = 0.0;
        onBetChanged();
    }
    this.wonBet = function(){
        cash += 2*betAmount;
        console.log("User "+userId+" won their bet amount of " + this.getCurrentBet() + ". New cash amount: " + cash);
        betAmount = 0.0;
        onCashChanged();
        onBetChanged();
    }

    this.setHand = function(newHand){
        hand = newHand;
    }

    this.getHand = function(){
        return hand;
    }

    var onCashChanged = function(){
        onCashChangedCallback();

        $.post('http://casino.curtiswendel.me:3000/api/requestFunds?userID=2&amount=30')
        .done(function(data){
            alert('data: '+data.error);
        });
    }

    this.setOnCashChangedCallback = function(newOnCashChanged){
        onCashChangedCallback = newOnCashChanged;
        onCashChangedCallback();
    }

    this.onBetChanged = function(newOnBetChanged){
        onBetChanged = newOnBetChanged;
        onBetChanged();
    }
};