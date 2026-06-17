=======================================================================================
===================================== MEMORY GAME =====================================
=======================================================================================
This project is an attemtp to create a simple desktop application for a quick game to try to exercise and improve my memory.
The idea is to create a sequence of numbers that will have to be input by the user whenever the game is played.
The application asks the user to define the following:
  * amount of digits for each of the numbers that will conform the sequence (All the numbers provided by the game for a given sequence, i.e., streak, will have the same number of digits)
  * amount of seconds that the provided random number will be displayed on the screen for the user to memorize it
The game will provide one number per day.
Right after the provided number disappears from the screen, the game will ask the user to input the number.
If forgotten, the user will have two options to remember the number of a particular day or numbers of the entire sequence:
  * ask the game to provide a cheat for the number corresponding to a particular day
  * ask the game to provide the entire sequence of ALL the numbers provided since day 1
Each time the cheat is consulted, there will be points penalties applied to the daily score obtained by the user.
The application keeps records of the results and creates a plot showing the daily score.
Color coding in the plot indicates if the daily score was achieved without cheats at all, or with single-day cheat, or with full sequence cheat. 

=======================================================================================
=================================== HOW TO LAUNCH IT ==================================
=======================================================================================
Simple. Double click on "memory_game.html"

=======================================================================================
====================================== FEEDBACK =======================================
=======================================================================================
[17-Jun-2026]
I've played the game for a couple of weeks and I want to make some changes and improvements.
Right now, I don't find it entertaining. I need to add optiosn to "play" with the provided numbers, so the user has more time to see them on the screen and memorize them.
I have few ideas in mind to implement this.
