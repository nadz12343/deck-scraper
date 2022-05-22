from importlib.resources import path
import requests
from bs4 import BeautifulSoup
import re
import time
import json
from requests.api import get
from requests.models import Response
import tkinter as tk
import sys
from pathlib import Path
import os
url = "https://yugioh.fandom.com/wiki/Zane_Truesdale_(Tag_Force)#Tag_Force_3"
r = requests.get(url)
soup = BeautifulSoup(r.content, 'html.parser')

#get all tag force editions

#comment the code
#automise to allow title to deck
#make fetching ids more efficient
#make directory for each character, and tag force edition
#download some individual web pages to show that the applications works correctly

#note not all decks can be extracted. some cards do not have id, other cards have aliases name to the API

#future improvements
#generalise so that you do not have to manually change the character page



def getTitle(url):
    title = soup.select("big") #all deck title are found within the <big> tag. It returns an array
    t = [] #used to hold each deck title
    for i in range(len(title)):
        #since some deck name has strange unicode characters, we want to replace it with "*" character to remove the error
        t.append(title[i].get_text().replace("\u2605", "★")) 
    return t


def removeBrack(cards):
    for i in range(len(cards)):
        #as some cards come with "(D)", we want to remove it along with trailing whitespaces
        cards[i] = re.sub("\([a-z, A-Z]*\)", "", cards[i]).strip() 
    return cards

def deStackCards(raw_cards):
    m = [m for m in raw_cards.split('\n')] # placing each monster in each entry of the array #
    print(m)
    m = removeBrack(m)
    cards = []
    for i in m: #loop used it find multiplicites of every card
        x = re.search("x[0-5]|X[0-5]", i) #using regular expression to search for multiplicities
        if x != None:# when there are multiplicities
            ind = x.span()[0]+1 #get the index of the multiplicity
            multiplicity = int(i[ind:]) #convert the index to int
            for m in range(multiplicity): #loop through multiplicty times and each time append the same name to the array
                cards.append(i[:ind-2].rstrip())
        else:
            cards.append(i)
    print("destack, ", cards)
    return cards

def formatCards(cards):
    for i in range(len(cards)): #for every monster format it so that it can be used for the api
        cards[i] = cards[i].replace(" ", "%20")
    return cards

#Do not use this as this is the old version generalise this for spell and extra cards
def LEGACY_getMonsters(url):
    formated_monsters = []#this is where the finalised monsters names will be held

    rows = soup.select("#monsters") #fetching all elements with the id of "monsters"
    raw_monsters = rows[16].get_text() #get all text within every tags
    raw_monsters = raw_monsters[26:] #splicing to get rid of useless data
    raw_monsters = raw_monsters.replace("Effect Monsters\n","") #getting rid of useless data

    m = [m for m in raw_monsters.split('\n')] # placing each monster in each entry of the array 
    
    for i in m: #loop used it find multiplicites of every card
        x = re.search("x[0-5]", i) #using regular expression to search for multiplicities
        if x != None:# when there are multiplicities
            ind = x.span()[0]+1 #get the index of the multiplicity
            multiplicity = int(i[ind:]) #convert the index to int
            for m in range(multiplicity): #loop through multiplicty times and each time append the same name to the array
                formated_monsters.append(i[:ind-2].rstrip())
        else:
            formated_monsters.append(i)

    for i in range(len(formated_monsters)): #for every monster format it so that it can be used for the api
        formated_monsters[i] = formated_monsters[i].replace(" ", "%20")
    return formated_monsters

def getMonsters(url, deckLocation):
    raw_monsters = deckLocation.select("#monsters ul") #within our current html code, find all monsters. returns an array
    s = "" #holds the monsters in one string, with a whitespace between each name
    for i in range(len(raw_monsters)):
        if i== len(raw_monsters)-1: # we do not want the last name to leave a "\n"
            s += raw_monsters[i].get_text()
        else:
           s += raw_monsters[i].get_text() + "\n"
    print(s)
    return formatCards(deStackCards(s))

def getExtras(url, deckLocation):
    raw_extra = deckLocation.select("#extra-deck ul") #within our current html code, find all extra. returns an array
    print(raw_extra)
    if len(raw_extra) == 0:
        return 0
    c = raw_extra[0].get_text().replace("F.G.D.", "Five-Headed Dragon") #special case: a text is f.g.d, and its eng translation is five-headed dragon
    return formatCards(deStackCards(c))

def getSpellTraps(url, deckLocation):
    raw_spellTraps = deckLocation.select("#spells-traps ul") #within our current html code, find all spell and trap cards. returns an array
    s = "" #holds the monsters in one string, with a whitespace between each name
    for i in range(len(raw_spellTraps)):
        if i== len(raw_spellTraps)-1: # we do not want the last name to leave a "\n"
            s += raw_spellTraps[i].get_text()
        else:
            s += raw_spellTraps[i].get_text() + "\n"
    print(s)
    return formatCards(deStackCards(s))

def getId(cards):
    ids = [] #the ids of each card are stored
    if cards == 0: return 0
    for i in range(len(cards)): #loop through each card and get the id for it by using the API
        cardData = requests.get("https://db.ygoprodeck.com/api/v7/cardinfo.php?name="+cards[i]) #retrieving the id from this restful API
        cardData = json.loads(cardData.text) 
        print("IN ID ", cards[i])
        try:
            ids.append(cardData["data"][0]["id"])
        except:
            pass
        time.sleep(1) #to ensure we dont get blocked by the API
    return ids

#the id of the cards are stored into txt file. this file is then saved as a ydk
def dataToYDK(deckName, monsterCards, extraCards, spellTrapCards):

    f = open(deckName, "x") #open the file held in the variable 'deckName'
    f.write("#main\n") #indication of main deck

    for i in range(len(monsterCards)):
        f.write(str(monsterCards[i])+"\n") #applying formatting

    for i in range(len(spellTrapCards)):
        f.write(str(spellTrapCards[i])+"\n") #applying formatting

    f.write("#extra\n") #indication of extra deck
    if extraCards != 0:
        for i in range(len(extraCards)):
            f.write(str(extraCards[i])+"\n") #applying formatting

    f.write("!side") #indication of side deck
    f.close()

    path_ = os.getcwd()
    myFile = Path(path_+"/" + deckName)
    myFile.rename(myFile.with_suffix(".ydk"))     #change the file from .txt to ydk
 

def get_deck_and_change_status():
    deckName = inputEntryText.get().strip()

    titles = getTitle(url) #store only the clean titles in the array
    if deckName not in titles:
        completionStatusText.set("could not find deck") #finish function
    else:
        #now find the cards of this deck
        deckLocation = soup.find("big", string = deckName.replace("*", "★")).parent.parent #this is where the deck html part is located   .select("#monsters ul")[1].text

        completionStatusText.set("half way done")

        monsterCards = getId(getMonsters(url, deckLocation)) #retrieve the monster cards 
        extraCards = getId(getExtras(url, deckLocation)) #retrieve the extra pile cards
        spellTrapCards = getId(getSpellTraps(url, deckLocation)) #get the spell and trap cards

        dataToYDK(deckName, monsterCards, extraCards, spellTrapCards) #mapping between the cards and its unique ID

        completionStatusText.set("Deck Completed")



# GUI, #
win = tk.Tk()
inputEntryText = tk.StringVar()
inputEntry = tk.Entry(textvariable = inputEntryText, width = 100).pack() #creating an input text

completionStatusText = tk.StringVar()
completionStatusText.set("not started") #downloading data status update message
CompletionStatusLabel = tk.Label(textvariable= completionStatusText).pack()

compileDeckButton = tk.Button(text = "Compile Deck", command = get_deck_and_change_status).pack() #button which executes the code

win.mainloop()

########   TEXT HANDLER ##############
 
# monsterCards = [21844576, 21844576, 58932615, 58932615, 84327329, 84327329, 20721928, 20721928, 34124316, 33875961, 59793705, 79979666, 33508719, 57116033, 57116033, 98585345, 6480253]
# extraCards = [35809262, 35809262, 35809262, 52031567, 47737087, 81197327, 83121692, 61204971, 61204971, 61204971]
# spellTrapCards = [31036355, 90928333, 53129443, 95286165, 26902560, 19613556, 5318639, 67169062, 55144522, 24094653, 24094653, 24094653, 70828912, 32807846, 32807846, 63035430, 63035430, 95281259, 25573054]
