# aw-rpc

## Install venv

> python3.9 -m venv flask-env

## start env

> . flask-env/bin/activate

## Install requirements

> pip install -r requirements.txt

## Run locally

> python3 app.py

## Test

> python test_unittest.py

  Unittest tests the following:

  app.py "RPC game engine"

  capture property
  end turn
  unit creation
  unit move(with x, y coord's)
  unit move2(with unit ID)



### View api doc/test

`http://localhost:5000/api/browse`


##TODO

Create secondary weapon and damage table

Add damage calculation to include COM_TOWER

Create all the tiles available in tile.png

CO's and powers

**nice to have**

Create resupply on demand via context menu for APC and Blackboat

Select option to attack, capture, wait, destroy, join

Weather inc fog

Stealth mechanic for subs and stealth

fix fuel consumption for hidden stealth and dived sub units
