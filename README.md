# aw-rpc

## Install venv

    python3.9 -m venv flask-env

## start env

    . flask-env/bin/activate

## Install requirements

    pip install -r requirements.txt

## Run locally

    python3 app.py

## Unittest

    python test_unittest.py



Tests the following RPC methods in the app.py module:

capture property,
end turn,
unit creation,
unit move(with x, y coord's),
unit move2(with unit ID),



## View api

    http://localhost:5000/api/browse

## Start a game/view game

    http://localhost:5000/(game)


##TODO

create flow diagram to visualise game flow

Create user/player to join games 

Create secondary weapon and damage table

Add damage calculation to include COM_TOWER (+10% per com tower)

Create all the tiles available in tile.png

CO's and powers

##**nice to have**

Create resupply on demand via context menu for APC and Blackboat

Fix loading multiple units to cargo index value

Mouse or select option to join troops together

Weather inc fog

Stealth mechanic for subs and stealth

Fix fuel consumption for hidden stealth and dived sub units
