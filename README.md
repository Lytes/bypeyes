## About
Each player sets a secret word. 

Can you chat without the AI eavesdropper guessing yours? 
Can you outsmart an AI? Can you do it while keeping it dumb enough for an human?

Every player gets a secret word, and they have to communicate their secret word to other player without the AI noticing.

A round ends if any of 3 conditions are met
1. The eavesdropping AI figures out either player's word (PLAYERS **lose**)
2. Both players figure out the other player's word correctly without the AI noticing (PLAYERS **win**)
3. 30 back and forth messages in the conversation (PLAYERS **lose**)

## Installation
- Best to use a virtual env
> pip3 -m venv venv
> source venv/bin/activate

- Pull repo
> git clone https://github.com/Lytes/bypeyes

- Add OpenAI key to config.py line 5
> nano bypeyes/config.py

- Run flask app
> python3 app.py

- Open `127.0.0.1:5000` in browser
