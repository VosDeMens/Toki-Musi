from words import words
import random

# from itertools import count
from time import sleep

for _ in range(1):
    moderator = random.choice(["", "pl", "pt", "qu", "cp", "sp"])
    w = random.choice(words)
    if moderator == "pl":
        w = w.pluralize()
    elif moderator == "pt":
        w = w.past_tensify()
    elif moderator == "qu":
        w = w.questionify()
    elif moderator == "cp":
        w = w.comparativize()
    elif moderator == "sp":
        w = w.superlativize()

    w.play()
    sleep(3)
    print(w)
    sleep(1)
