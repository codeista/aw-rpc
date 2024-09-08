# aw-rpc

Turn based stratergy game clone 
with api interface using Flask.

## Setup virtual environment

    python -m venv flask-env

## start virtual environment

    . flask-env/bin/activate

## Install requirements

    pip install -r requirements.txt

## Run locally

    python3 app.py

## Unittest

    python test_unittest.py



Tests the following RPC methods in the app.py module:

unit creation,
unit move(with x, y coord's)

**Needs updating**
capture property,
end turn,
unit move2(with unit ID),



## View api

    http://localhost:5000/api/browse

## Start a game/view game

    http://localhost:5000/(game)


##TODO

Create secondary weapon and damage table

Add damage calculation to include COM_TOWER

Create all the tiles available in tile.png

CO's and powers

##**nice to have**

Create resupply on demand via context menu for APC and Blackboat

Fix loading multiple units to cargo index value

Mouse or select option to join troops together

Weather inc fog

Stealth mechanic for subs and stealth

Fix fuel consumption for hidden stealth and dived sub units

## vc-code Mermaid Extension

Markdown Preview Mermaid Support
https://marketplace.visualstudio.com/items?itemName=bierner.markdown-mermaid

Installation:
    Launch VS Code Quick Open (Ctrl+P), paste the following command, and press enter.
    'ext install bierner.markdown-mermaid'

preview flowchart.md