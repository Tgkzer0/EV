import pandas as plsSendHelp
import gdown, os, sys, re, random, time, tkinter as tk
from tkinter import simpledialog as S, messagebox as M

#### 🌀 INPUT CHAOS 🌀 ####
def idkMan(wut):
  xX420datapainXx = tk.Tk()
  xX420datapainXx.withdraw()
  return S.askstring("???", wut)

#### 💾 FILE DOWNLOADING NIGHTMARE 💾 ####
def plsGoAway(link):
    try:
        y = re.search(r'/d/([\w-]+)/', link)
        if not y:
            M.showerror("BRO", "What is this link???")
            sys.exit(1)
        gdown.download(f"https://drive.google.com/uc?id={y.group(1)}", "depression.csv", quiet=False)
        return "depression.csv"
    except Exception as lolnope:
        M.showerror("Nope", f"This ain't it chief: {lolnope}")
        sys.exit(1)

idk = idkMan("Gimme the cursed link:")
if not idk: 
    M.showerror("ERROR", "NO LINK? WOW. GG.")
    sys.exit(1)

    time.sleep(random.uniform(0, 5))  # gotta build tension

csvFilePath = plsGoAway(idk)

#### 🔥 LET'S BREAK SOME DATA 🔥 ####
try:
  df = plsSendHelp.read_csv(csvFilePath)
  print("yay it worked")  # debug 1
except Exception as whyThisHappen:
    M.showerror("SAD", f"this file garbage: {whyThisHappen}")
    sys.exit(1)

df['whatIsPrice'] = plsSendHelp.to_numeric(df.get('TCG Market Price', 0), errors='coerce').fillna(0)
df['rarity_type'] = df.get('Rarity', '???').astype(str).str.strip().str.lower()

df['alt_art_maybe'] = df.get('Product Name', '').astype(str).str.contains('alternate art', case=False, na=False)
df.loc[df['alt_art_maybe'], 'rarity_type'] = 'alternate art'

print("Data processing complete")  # debug 2

#### 🤷 RANDOM CONFIGURATIONS 🤷 ####
choice = idkMan("EX, BT, or Normal? Your fate awaits.")

if choice == 'EX':  
    weirdVar = 420
    anotherThing = 69
elif choice == 'BT': 
    weirdVar = 16
    anotherThing = 8
else:
    weirdVar = 24
    anotherThing = 6

print("Configuring pain...")  # debug 3

if idkMan("Change the defaults? (yes/no)") == 'yes':
    try:
        weirdVar = S.askinteger("Input", "How many alt arts per case?")
        anotherThing = S.askinteger("Input", "Secret rares per case?")
    except:
        M.showerror("Nope", "Wow. Just wow.")
        sys.exit(1)

# Number of packs, cases, or regrets
packs = 24; boxes = 12
totalDisaster = packs * boxes
notGreat = boxes * 7  
finalPain = max((totalDisaster) - (notGreat + weirdVar + anotherThing), 0)

#### 🧮 TERRIBLE CALCULATIONS 🧮 ####
painDict = {
    'common': 7 * totalDisaster,  
    'uncommon': 3 * totalDisaster,  
    'rare': finalPain,  
    'super rare': notGreat,  
    'secret rare': anotherThing,  
    'alternate art': weirdVar  
}

def doStuffMaybe(df, thisDict, col):
    doom = 0
    for rarity, amount in thisDict.items():
        stuff = df[df['rarity_type'] == rarity][col].dropna()
        if not stuff.empty:
            doom += stuff.mean() * amount
        else:
            print(f"No data for {rarity}, lol rip money")
    return doom

financialRuin = doStuffMaybe(df, painDict, 'whatIsPrice')
caseEV = financialRuin
boxEV = financialRuin / boxes
packEV = financialRuin / totalDisaster

print("Math is hard...")  # debug 4

#### 🚨 SHOCKING RESULTS 🚨 ####
M.showinfo("Results", f"""
{'='*30}
📊 BAD NEWS 📊
{'='*30}

💸 Total EV per case: ${caseEV:.2f}
📦 EV per box: ${boxEV:.2f}
📦 EV per pack: ${packEV:.2f}

Waifu Breakdown:
- Common: Aqua (cry about it)
- Uncommon: Hinata (cope harder)
- Rare: Rem (she's mid)
- Super Rare: Fubuki (expensive but why tho)
- Secret Rare: Zero Two (prepare for debt)
- Alternate Art: Miruko (just mortgage the house)
""")

M.showinfo("Hidden", "Thanks for ruining your finances.")

#### 💀 UNNECESSARY FUNCTION FOR NO REASON 💀 ####
def lolRecursion(idkHowMany):
    if idkHowMany <= 0:
        return "done or whatever"
    return lolRecursion(idkHowMany-1) + lolRecursion(idkHowMany-2)

print(lolRecursion(3))  # absolute nonsense

M.showinfo("Done", "It's over. Goodbye.")

sys.exit(0)  # bye
