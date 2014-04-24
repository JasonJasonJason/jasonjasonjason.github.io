var Hand = function (newCards){

    var cards = [];

    for(var i=0; i<newCards.length; i++){
        cards.push(newCards[i]);
    }

    this.getHand = function(){
        return cards;
    }
    this.setHand = function(newCards){
        cards = newCards;
    }
};