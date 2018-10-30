# sushi-go-game
An implementation of the card game SushiGo! in python.

### Still to do
1. Add the ability to decide the number of players and include their names.  
2. Add the event loop ability to play a wasabi card onto a nigiri card.  
3. Fix the way that the initial deck is generated.  
4. Remove the magic numbers from the code around scoring.  
5. Move the add wasabi logic to the nigiri cards.  
6. Add the chopstick type card.  
7. GameEngine does too much. Consider refactoring.

### Future work
1. Add a web API.  
2. Build a mobile app.  

### How to run
1. `python main.py` starts the game with two players
2. First players go, they input the index of the card they wish to play from their hand
3. Second players go, input the index of the card they wish to play from their hand
4. Play until all hands are complete
5. Highest score is the winner

### Run tests
`python3 -m unittest discover tests`