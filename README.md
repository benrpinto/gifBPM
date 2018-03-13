# gifBPM
Tap a beat, and have a gif play in sync with your tapping

Isn't it great when an animated gif loops at the same pace as the song you're listening to?
Wouldn't it be great if you could tap a beat, and have a computer tell you which gifs match that tempo?

That's what this program is for.
Add gifs to a local database, and then tap a regular beat and the program will pull up a gif for you.

OPTIONS:
* G: Add a gif
* A: Add multiple gifs (by specifying a file containing gif pathnames)
* T: Tap a beat and get a gif
* P: Print the database
* D: Delete an entry from the database
* H: Help
* Q: Quit the program

IMPLEMENTED:
- [X] calculating the length and tempo of a gif on your computer
- [X] calculating the length and tempo of a gif from a url
- [X] calculating the length and tempo of multiple gifs from a file containing pathnames
- [X] storing the filepath, filename, length, and tempo of a gif in a local database
- [X] displaying the database contents
- [X] clearing the database
- [X] calculating the tempo of a user's keyboard taps
- [X] querying the database for a gif that most closely matches the tempo (e.g. if you tap at 120 BPM then a gif of 120 BPM can be selected)
- [X] querying the database for a gif that is in time with the tempo (e.g. if you tap at 120 BPM, then a gif of 60BPM can be selected too)
- [X] excluding gifs that are much shorter or longer than the tempo from queries (e.g. a gif of 300 BPM matches a user tapping at 30 BPM, but is too fast to be a satisfying match)
- [X] displaying the gif
- [X] Windows support
- [X] Deleting a specific gif from the database
