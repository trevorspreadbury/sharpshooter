I would like to design a simple python web UI to run locally to simulate a game. It should run using UV and modern python practices. 

## The Game Board

The game board in 16 spaces wide and 28 spaces long. Spaces may be blank, orange, red, or blue. There are two levels. 

blank will be _, Orange is O, Blue is B, and red is R.

### Level 1:

OOOOOOOOOOOOOOOO
________________
________________
________________
________________
________________
________________
________________
________________
________________
________________
________________
________________
B_B_B_B_B_B_B_B_
_B_B_B_B_B_B_B_B
________________
________________
________________
________________
________________
________________
________________
________________
________________
________________
________________
________________
OOOOOOOOOOOOOOOO

In this level, the top blue move left one space at at time, wrapping around. It takes 6 seconds for one blue to traverse the whole row.
The bottom level of blues move right one space at a time at the same speed and also wrapping around.

### Level 2

OOOOOOOOOOOOOOOO
________________
________________
________________
________________
____RRRR____RRRR
________________
________________
________________
________________
________________
________________
________________
B_B_B_B_B_B_B_B_
_B_B_B_B_B_B_B_B
________________
________________
________________
________________
________________
________________
________________
RRRR____RRRR____
________________
________________
________________
________________
OOOOOOOOOOOOOOOO

In level two, the blue and orange move in the same way. The reds on the bottom move to the right, with each tile moving the full 16 spaces every 4 seconds. The top reds move to the left at the same speed. If an orange hits a red, they both disappear. 


## Gameplay


The orange can be fired by the player. When fired, the top row ones move down and the bottom row ones move up. They move 12 spaces in the time a blue moves one space. 
If the orange hits the blue, they disappear. Once all the blue disappear, the player has beat the level. 

If a player hits a red, they lose a life. Players have 5 lives. Players have 45 seconds per level. 


