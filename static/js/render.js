//
// Setup
//

// constants
const TILESIZE = 16;

// globals
var token = document.getElementById('draw').getAttribute('x-token');
var board = null;
var two = null;

// update board data
update();

// init controls
var buttonrerender = document.getElementsByClassName('buttonrerender');
buttonrerender.onclick = rerender;
var inputshowmap = document.getElementById('inputshowmap');
inputshowmap.onchange = rerender;
var buttonendturn = document.getElementsByClassName('buttonendturn');
buttonendturn.onclick = armyEndTurn;
var buttonstartgame = document.getElementsByClassName('buttonstartgame');
buttonstartgame.onclick = startGame;
var buttonendgame = document.getElementsByClassName('buttonendgame');
buttonendgame.onclick = endGame;
var buttonchat = document.getElementById('buttonchat');
buttonchat.onclick = chat;
var inputchat = document.getElementById('inputchat');
inputchat.onkeypress = chat;
var inputshowchat = document.getElementById('inputshowchat');
inputshowchat.onchange = showChat;
var inputshowjson = document.getElementById('inputshowjson');
inputshowjson.onchange = showJson;

// init socket.io
setTimeout(function() {
    //const socket = io(document.location.scheme + document.location.host + '/');
    const socket = io('/');

    socket.on('connect', () => {
        console.log('socket connected');
        socket.emit('game', token);
    });
    socket.on('disconnect', () => {
        console.log('socket disconnected');
    });
    socket.on('update', (msg) => {
        console.log('update: ' + msg);
        update();
    });
    socket.on('message', (msg) => {
        console.log('message: ' + msg);
        var textareachat = document.getElementById('textareachat');
        textareachat.value = textareachat.value + msg + '\n';
        textareachat.scrollTop = textareachat.scrollHeight;
    });
}, 100);

//
// Helper methods
//

function uuidv4() {
    return ([1e7]+-1e3+-4e3+-8e3+-1e11).replace(/[018]/g, c =>
        (c ^ crypto.getRandomValues(new Uint8Array(1))[0] & 15 >> c / 4).toString(16)
    );
}

function rerender() {
    console.time('rerender');
    two.clear();
    createScene();
    two.update();
    console.timeEnd('rerender');
}

//
// JSON-RPC methods
//

function jsonrpc(method, params, callback) {
    params.token = token;
    console.log('rpc::', method, params);
    var xhr = new XMLHttpRequest();
    xhr.onreadystatechange = function() {
        if (this.readyState === XMLHttpRequest.DONE) {
            if (this.status === 200) {
                if (callback) {
                    callback(JSON.parse(this.responseText).result);
                }
            } else {
                console.error('error calling "' + method + '"');
            }
        }
    };
    xhr.open('POST', '/api');
    xhr.setRequestHeader('Content-Type', 'application/json');
    var data  = {'jsonrpc:': '2.0', 'method': method, 'params': params, 'id': uuidv4()}
    xhr.send(JSON.stringify(data));
}

function update() {
    jsonrpc('game_board', {}, function(res) {
        // init globals
        board = res
        if (two === null) {
            // make an instance of two and place it on the page.
            var elem = document.getElementById('draw');
            var params = { type: Two.Types.canvas, width: board.width * TILESIZE, height: board.height * TILESIZE };
            two = new Two(params).appendTo(elem);
            // canvas mouse handling
            var draw = document.getElementById('draw');
            var canvas = draw.children[0];
            canvas.onmousemove = canvasMove;
            canvas.onclick = canvasClick;
            canvas.ondblclick = canvasdblClick;
        }
        // render
        two.clear();
        createScene();
        two.update();
        // update info

        var gamebox = document.getElementById('gamebox');
        gamebox.innerText =
                           `Game info:
                             - Day: ${board.days}
                             - Current Turn: ${board.current_turn}
                             - Game Active: ${board.game_active}
                             Blue:
                             - Troops: ${board.total_blue_troops}
                             - Income: ${board.total_blue_properties}
                             - Funds: ${board.blue_funds}
                            Red:
                            - Troops: ${board.total_red_troops}
                            - Income: ${board.total_red_properties}
                            - Funds: ${board.red_funds}
                            `;

        var infobox = document.getElementById('infobox');
        infobox.innerText =
                        `Instructions:
                        - Single click: move, attack
                        -  + ctrl: load unit
                        -  + alt: unload unit
                        - Double click: capture, wait`;
        // update code
        var code = document.getElementById('code');
        code.value = JSON.stringify(board, null, 2);
    });
}

function chat(ev) {
    if ('key' in ev && ev.key != 'Enter')
        return;
    var inputchat = document.getElementById('inputchat');
    var msg = inputchat.value;
    inputchat.value = '';
    if (msg == '')
        return;
    jsonrpc('message', {msg: msg});
}

function armyEndTurn() {
    jsonrpc('army_end_turn', {});
}

function startGame() {
    jsonrpc('start_game', {});
}

function endGame() {
    jsonrpc('end_game', {});
}

function unitCreate(tile) {
    var modal = document.getElementById('modalcreate');
    var span = document.getElementsByClassName('close')[0];
    span.onclick = function() {
        modal.style.display = 'none';
    };
    window.onclick = function(ev) {
        if (ev.target == modal) {
            modal.style.display = 'none';
        }
    };
    var select = document.getElementById('selectcreate');
    select.innerHTML = '<option>INFANTRY</option><option>MECH</option><option>RECON</option><option>TANK</option><option>MEDIUMTANK</option><option>ANTIAIR</option><option>ARTILLERY</option><option>MISSILE</option><option>ROCKET</option><option>NEOTANK</option><option>MEGATANK</option><option>PIPERUNNER</option><option>APC</option>';

    var btn = document.getElementById('buttoncreate');
    btn.onclick = function() {
        modal.style.display = 'none';
        var unitType = select.options[select.selectedIndex].value;;
        var army = tile.mapTile.army;
        jsonrpc('unit_create_rpc', {army: army, unit_type: unitType, x: tile.x, y: tile.y});
    };
    modal.style.display = 'block';
}

function airunitCreate(tile) {
    var modal = document.getElementById('modalcreate');
    var span = document.getElementsByClassName('close')[0];
    span.onclick = function() {
        modal.style.display = 'none';
    };
    window.onclick = function(ev) {
        if (ev.target == modal) {
            modal.style.display = 'none';
        }
    };
    var select = document.getElementById('selectcreate');
    select.innerHTML = '<option>BCOPTER</option><option>TCOPTER</option><option>FIGHTER</option><option>BOMBER</option>';

    var btn = document.getElementById('buttoncreate');
    btn.onclick = function() {
        modal.style.display = 'none';
        var unitType = select.options[select.selectedIndex].value;;
        var army = tile.mapTile.army;
        jsonrpc('unit_create_rpc', {army: army, unit_type: unitType, x: tile.x, y: tile.y});
    };
    modal.style.display = 'block';
}

function seaunitCreate(tile) {
    var modal = document.getElementById('modalcreate');
    var span = document.getElementsByClassName('close')[0];
    span.onclick = function() {
        modal.style.display = 'none';
    };
    window.onclick = function(ev) {
        if (ev.target == modal) {
            modal.style.display = 'none';
        }
    };
    var select = document.getElementById('selectcreate');
    select.innerHTML = '<option>LANDER</option><option>BATTLESHIP</option><option>CRUISER</option><option>SUB</option><option>CARRIER</option><option>BLACKBOAT</option>';

    var btn = document.getElementById('buttoncreate');
    btn.onclick = function() {
        modal.style.display = 'none';
        var unitType = select.options[select.selectedIndex].value;;
        var army = tile.mapTile.army;
        jsonrpc('unit_create_rpc', {army: army, unit_type: unitType, x: tile.x, y: tile.y});
    };
    modal.style.display = 'block';
}

function unitSelect(tile) {
    jsonrpc('unit_select', {x: tile.x, y: tile.y});
}

function unitCapture(tile) {
    jsonrpc('capture_tile', {x: tile.x, y: tile.y});
}

function unitWait(tile) {
    jsonrpc('unit_wait', {x: tile.x, y: tile.y});
}

function unitAttack(tile) {
    jsonrpc('unit_attack', {x: board.selected.x, y: board.selected.y, x2: tile.x, y2: tile.y});
}

function unitLoad(tile) {
    jsonrpc('unit_load', {x: board.selected.x, y: board.selected.y, x2: tile.x, y2: tile.y});
}

function unitUnload(tile) {
    idx = 0
    jsonrpc('unit_unload', {x: board.selected.x, y: board.selected.y, x2: tile.x, y2: tile.y , index: idx});
}

function unitJoin(tile) {
    jsonrpc('unit_join', {x: board.selected.x, y: board.selected.y, x2: tile.x, y2: tile.y});
}

function unitMove(tile) {
    var source = board.selected;
    var target = tile;
    jsonrpc('unit_move', {x: source.x, y: source.y, x2: target.x, y2: target.y});
}

//
// two.js rendering methods
//

function tileAt(px, py) {
    var tileX = Math.floor(px / TILESIZE);
    var tileY = Math.floor(py / TILESIZE);
    var tile = board.grid[tileX + tileY * board.width];
    return tile;
}

function canvasMove(ev) {
    var x = ev.offsetX;
    var y = ev.offsetY;
    var tile = tileAt(x, y);
    draw.style.cursor = 'default';
    if (tile && tile.can_be_moved_to)
        draw.style.cursor = 'pointer';
    else if (tile.can_be_attacked)
             draw.style.cursor = 'crosshair';
    else if (tile.unit != null && tile.unit.army == board.current_turn)
             draw.style.cursor = 'pointer';
    else if (tile.mapTile.army == board.current_turn)
             if (tile.mapTile.type == 'FACTORY' ||
                 tile.mapTile.type == 'AIRPORT' ||
                 tile.mapTile.type == 'PORT')
                 draw.style.cursor = 'pointer';
}

function canvasClick(ev) {
    var x = ev.offsetX;
    var y = ev.offsetY;
    var tile = tileAt(x, y);
    if (ev.detail == 1){
      if (ev.ctrlKey) {
          unitLoad(tile);
      } else if (ev.altKey) {
                 unitUnload(tile);
      }
      if (tile.can_be_attacked) {
          unitAttack(tile);
      }
      else if (tile.unit != null &&
               tile.unit.army == board.current_turn) {
               if (tile.unit.can_attack ||
                   tile.unit.can_move ||
                   tile.unit.can_capture) {
                   unitSelect(tile);
                   }
              }
      if (tile.can_be_moved_to) {
          unitMove(tile);
        }
      else if (tile.mapTile.type == 'FACTORY' &&
               tile.mapTile.army == board.current_turn &&
               tile.unit == null) {
               unitCreate(tile);
               }
      else if (tile.mapTile.type == 'AIRPORT' &&
              tile.mapTile.army == board.current_turn &&
              tile.unit == null) {
              airunitCreate(tile);
              }
      else if (tile.mapTile.type == 'PORT' &&
              tile.mapTile.army == board.current_turn &&
              tile.unit == null) {
              seaunitCreate(tile);
              }
    }
}

function canvasdblClick(ev) {
    var x = ev.offsetX;
    var y = ev.offsetY;
    var tile = tileAt(x, y);
    if (tile.mapTile.type === 'CITY' ||
               tile.mapTile.type === 'BASE_TOWER_1' ||
               tile.mapTile.type === 'FACTORY' ||
               tile.mapTile.type === 'PORT' ||
               tile.mapTile.type ==='AIRPORT') {
               if (tile.unit &&
                   tile.unit.can_capture) {
                   if (tile.unit.type == 'INFANTRY' ||
                       tile.unit.type == 'MECH') {
                       unitCapture(tile);
                       }
                   }
    } else if (tile.unit) {
            unitWait(tile);
            }
}

var textureLoadId = null;
function ontextureLoad(src) {
    if (textureLoadId != null) {
        clearTimeout(textureLoadId);
        textureLoadId = null;
    }
    textureLoadId = setTimeout(() => two.update(), 100);
}

function showJson() {
  var showJsonArea = document.getElementById('inputshowjson').checked;
  if (showJsonArea) {
    code.hidden = "";
  } else {
    code.hidden = "true";
  }
}

function showChat() {
  var showChatArea = document.getElementById('inputshowchat').checked;
  if (showChatArea) {
    textareachat.hidden = "";
    inputchat.hidden = "";
    buttonchat.hidden = "";
  } else {
    textareachat.hidden = "true";
    inputchat.hidden = "true";
    buttonchat.hidden = "true";
  }
}


function makeMapTile(tile) {
    var showMapTiles = document.getElementById('inputshowmap').checked;
    if (showMapTiles) {
        // tile sprite
        var spriteSheetWidth = 445;
        var spriteSheetHeight = 1163;
        const SPRITESIZE = 16;
        var x = spriteSheetWidth/2 - SPRITESIZE/2;
        var y = spriteSheetHeight/2 - SPRITESIZE/2;
        var _2xHeight = false;
        switch (tile.mapTile.type) {
            case 'PLAIN':
                x = x - 8;
                y = y - 64;
                break;
            case 'WOOD':
                x = x - 352;
                y = y - 56;
                _2xHeight = true;
                break;
            case 'MOUNTAIN':
                x = x - 25;
                y = y - 39;
                _2xHeight = true;
                break;
            case 'ROAD_HORT':
                x = x - 42;
                y = y - 64;
                break;
            case 'ROAD_VERT':
                x = x - 59;
                y = y - 64;
                break;
            case 'ROAD_NW':
                x = x - 42;
                y = y - 13;
                break;
            case 'ROAD_NE':
                x = x - 76;
                y = y - 13;
                break;
            case 'ROAD_SE':
                x = x - 76;
                y = y - 47;
                break;
            case 'ROAD_SW':
                x = x - 42;
                y = y - 47;
                break;
            case 'SWNRoad':
                x = x - 156;
                y = y - 31;
                break;
            case 'ESWRoad':
                x = x - 59;
                y = y - 13;
                break;
            case 'WNERoad':
                x = x - 110;
                y = y - 47;
                break;
            case 'NESRoad':
                x = x - 110;
                y = y - 47;
                break;
            case 'CRoad':
                x = x - 59;
                y = y - 30;
                break;
            case 'CITY':
                x = x - 87;
                switch (tile.mapTile.army) {
                    case 'RED':
                        y = y - 812;
                        break;
                    case 'BLUE':
                        y = y - 847;
                        break;
                    default:
                        y = y - 766;
                        break;
                }
                _2xHeight = true;
                break;
            case 'FACTORY':
                x = x - 102;
                switch (tile.mapTile.army) {
                    case 'RED':
                        y = y - 818;
                        break;
                    case 'BLUE':
                        y = y - 851;
                        break;
                    default:
                        y = y - 772;
                        break;
                }
                break;
            case 'AIRPORT':
                x = x - 120;
                switch (tile.mapTile.army) {
                    case 'RED':
                        y = y - 818;
                        break;
                    case 'BLUE':
                        y = y - 851;
                        break;
                    default:
                        y = y - 773;
                        break;
                }
                break;
            case 'PORT':
                x = x - 137;
                switch (tile.mapTile.army) {
                    case 'RED':
                        y = y - 811;
                        _2xHeight = true;
                        break;
                    case 'BLUE':
                        y = y - 844;
                        _2xHeight = true;
                        break;
                    default:
                        y = y - 765;
                        _2xHeight = true;
                        break;
                }
                break;
            case 'COM_TOWER':
                x = x - 154;
                switch (tile.mapTile.army) {
                    case 'RED':
                        y = y - 811;
                        break;
                        _2xHeight = true;
                    case 'BLUE':
                        y = y - 844;
                        _2xHeight = true;
                        break;
                    default:
                        y = y - 765;
                        break;
                }
                _2xHeight = true;
                break;
            case 'BASE_TOWER_0':
                x = x - 1;
                switch (tile.mapTile.army) {
                    case 'RED':
                        y = y - 812;
                        break;
                        _2xHeight = true;
                    case 'BLUE':
                        y = y - 845;
                        _2xHeight = true;
                        break;
                    default:
                        y = y - 757;
                        break;
                }
                _2xHeight = true;
                break;
            case 'BASE_TOWER_1':
                x = x - 1;
                switch (tile.mapTile.army) {
                    case 'RED':
                        y = y - 812;
                        break;
                        _2xHeight = true;
                    case 'BLUE':
                        y = y - 845;
                        _2xHeight = true;
                        break;
                    default:
                        y = y - 757;
                        break;
                }
                _2xHeight = true;
                break;
            case 'BASE_TOWER_2':
                x = x - 38;
                switch (tile.mapTile.army) {
                    case 'RED':
                        y = y - 1040;
                        break;
                    case 'BLUE':
                        y = y - 1073;
                        break;
                    default:
                        y = y - 1218;
                        break;
                }
                _2xHeight = true;
                break;
            case 'LAB':
                x = x - 171;
                switch (tile.mapTile.army) {
                    case 'RED':
                        y = y - 812;
                        break;
                        _2xHeight = true;
                    case 'BLUE':
                        y = y - 845;
                        _2xHeight = true;
                        break;
                    default:
                        y = y - 765;
                        break;
                }
                _2xHeight = true;
                break;
            case 'RIVER_HORT':
                x = x - 386;
                y = y - 145;
                break;
            case 'RIVER_VERT':
                x = x - 420;
                y = y - 111;
                break;
            case 'RIVER_NE':
                x = x - 369;
                y = y - 94;
                break;
            case 'RIVER_NW':
                x = x - 403;
                y = y - 94;
                break;
            case 'RIVER_SE':
                x = x - 403;
                y = y - 128;
                break;
            case 'RIVER_SW':
                x = x - 369;
                y = y - 128;
                break;
            case 'ESWRiver':
                x = x - 161;
                y = y - 338;
                break;
            case 'NESRiver':
                x = x - 110;
                y = y - 251;
                break;
            case 'WNERiver':
                x = x - 160;
                y = y - 285;
                break;
            case 'SWNRiver':
                x = x - 160;
                y = y - 285;
                break;
            case 'BEACH_NE':
                x = x - 333;
                y = y - 198;
                break;
            case 'BEACH_NW':
                x = x - 282;
                y = y - 355;
                break;
            case 'BEACH_SW':
                x = x - 350;
                y = y - 355;
                break;
            case 'BEACH_SE':
                x = x - 333;
                y = y - 145;
                break;
            case 'BEACH_N':
                x = x - 265;
                y = y - 111;
                break;
            case 'BEACH_E':
                x = x - 214;
                y = y - 321;
                break;
            case 'BEACH_S':
                x = x - 265;
                y = y - 304;
                break;
            case 'BEACH_W':
                x = x - 231;
                y = y - 321;
                break;
            case 'BEACH_END_N':
                x = x - 248;
                y = y - 145;
                break;
            case 'BEACH_END_E':
                x = x - 316;
                y = y - 111;
                break;
            case 'BEACH_END_S':
                x = x - 248;
                y = y - 128;
                break;
            case 'BEACH_END_W':
                x = x - 316;
                y = y - 94;
                break;
            case 'PIPE_VERT':
                x = x - 212;
                y = y - 30;
                break;
            case 'PIPE_END_N':
                x = x - 178;
                y = y - 30;
                break;
            case 'PIPE_END_S':
                x = x - 178;
                y = y - 47;
                break;
            case 'PIPE_END_W':
                x = x - 144;
                y = y - 64;
                break;
            case 'PIPE_END_E':
                x = x - 161;
                y = y - 64;
                break;
            case 'PIPE_END_NE':
                x = x - 161;
                y = y - 30;
                break;
            case 'PIPE_END_NW':
                x = x - 144;
                y = y - 30;
                break;
            case 'PIPE_END_SW':
                x = x - 144;
                y = y - 47;
                break;
            case 'PIPE_END_SE':
                x = x - 161;
                y = y - 47;
                break;
            case 'PIPE_HORT':
                x = x - 195;
                y = y - 30;
                break;
            case 'SEA':
                x = x - 76;
                y = y - 94;
                break;
            case 'HBridge':
                x = x - 76;
                y = y - 64;
                break;
            case 'VBridge':
                x = x - 94;
                y = y - 64;
                break;
            case 'REEF':
                x = x - 224;
                y = y - 146;
                break;
            case 'MISSILE_SILO':
                x = x - 188;
                y = y - 766;
                _2xHeight = true;
                break;
            case 'EMPTY_SILO':
                x = x - 205;
                y = y - 767;
                _2xHeight = true;
                break;
            default:
                console.log(tile.mapTile.type);
                return;
        }
        var tilesetSrc = '/static/img/Advance_Wars_Dual_Strike_Tileset_Normal_Transparent.png';
        var spriteTexture = new Two.Texture(tilesetSrc, () => ontextureLoad(tilesetSrc));
        spriteTexture.offset = new Two.Vector(x, y);
        var rect = null;
        if (_2xHeight) {
            rect = two.makeRectangle(tile.x * TILESIZE + TILESIZE/2, tile.y * TILESIZE , SPRITESIZE, SPRITESIZE * 2);
        } else {
            rect = two.makeRectangle(tile.x * TILESIZE + TILESIZE/2, tile.y * TILESIZE + TILESIZE/2, SPRITESIZE, SPRITESIZE);
        }
        rect.fill = spriteTexture;
        rect.stroke = 'transparent';
    }
    // tile overlay
    rect = two.makeRectangle(tile.x * TILESIZE + TILESIZE/2, tile.y * TILESIZE + TILESIZE/2, TILESIZE, TILESIZE);
    rect.stroke = 'black';
    rect.fill = 'transparent';
    rect.opacity = 0.50;
    if (tile.can_be_moved_to) {
        rect.fill = 'lightyellow';
    }
    if (tile.can_be_attacked) {
        rect.fill = 'red';
    }
    if (board.selected && board.selected.unit && tile.unit && tile.unit.id == board.selected.unit.id) {
        rect.fill = 'lightsalmon';
    }
}

function makeSprite(tile) {
    var spriteSheetWidth = 781;
    var spriteSheetHeight = 1790;
    const SPRITESIZE = 16;
    var x = spriteSheetWidth/2 - SPRITESIZE/2;
    var y = spriteSheetHeight/2 - SPRITESIZE/2;
    switch (tile.unit.army) {
        case 'RED':
            x = x - 4;
            y = y - 105;
            break;
        case 'BLUE':
            x = x - 393;
            y = y - 105;
            break;
        case 'GREEN':
            x = x - 4;
            y = y - 672;
            break;
        case 'YELLOW':
            x = x - 393;
            y = y - 672;
            break;
        case 'GREY':
            x = x - 4;
            y = y - 1240;
            break;
    }
    switch (tile.unit.type) {
        case 'MECH':
            y = y - 95;
            break;
        case 'RECON':
            y = y - 190;
            break;
        case 'TANK':
            y = y - 209;
            break;
        case 'MEDIUMTANK':
            y = y - 228;
            break;
        case 'ANTIAIR':
            y = y - 285;
            break;
        case 'ARTILLERY':
            y = y - 303;
            break;
        case 'MISSILE':
            y = y - 342;
            break;
        case 'ROCKET':
            y = y - 322;
            break;
        case 'APC':
            y = y - 265;
            break;
        case 'NEOTANK':
            y = y - 247;
            break;
        case 'FIGHTER':
            y = y - 361;
            break;
        case 'BCOPTER':
            y = y - 400;
            break;
        case 'TCOPTER':
            y = y - 418;
            break;
        case 'BATTLESHIP':
            y = y - 437;
            break;
        case 'LANDER':
            y = y - 475;
            break;
        case 'CRUISER':
            y = y - 455;
            break;
        case 'SUB':
            y = y - 495;
            break;
        case 'BOMBER':
            y = y - 380;
            break;
        case 'CARRIER':
            y = y - 512;
            break;
        case 'BLACKBOAT':
            y = y - 512;
            x = x - 17
            break;
        case 'MEGATANK':
            y = y - 512;
            x = x - 33
            break;
        case 'PIPERUNNER':
            y = y - 538;
            break;
    }
    if (!tile.unit.can_move && !tile.unit.can_attack)
        x = x - 336; // unavailable sprite
    var unitsSrc = '/static/img/aw2_blackhole_units_map_transparent.png';
    var spriteTexture = new Two.Texture(unitsSrc, () => ontextureLoad(unitsSrc));
    spriteTexture.offset = new Two.Vector(x, y);
    var rect = two.makeRectangle(tile.x * TILESIZE + TILESIZE/2, tile.y * TILESIZE + TILESIZE/2, SPRITESIZE, SPRITESIZE);
    rect.fill = spriteTexture;
    rect.stroke = 'transparent';
    var health = null;
    var fuel = null;
    var ammo = null;
    if (tile.unit.status.hp <= 90 && tile.unit.can_move ) {
        const HEALTHSIZE = SPRITESIZE/2;
        x = spriteSheetWidth/2 - HEALTHSIZE/2;
        y = spriteSheetHeight/2 - HEALTHSIZE/2;
        x = x - 557;
        y = y - 1234;
        var xMult = Math.ceil(tile.unit.status.hp / 10) - 1;
        x = x - xMult - xMult * HEALTHSIZE;
        var healthTexture = new Two.Texture(unitsSrc, () => ontextureLoad(unitsSrc));
        healthTexture.offset = new Two.Vector(x, y);
        health = two.makeRectangle(tile.x * TILESIZE + TILESIZE - HEALTHSIZE/2, tile.y * TILESIZE + TILESIZE - HEALTHSIZE/2, HEALTHSIZE, HEALTHSIZE);
        health.fill = healthTexture;
        health.stroke = 'transparent';
    }
    if (tile.unit.status.hp <= 90 && !tile.unit.can_move ) {
        const HEALTHSIZE = SPRITESIZE/2;
        x = spriteSheetWidth/2 - HEALTHSIZE/2;
        y = spriteSheetHeight/2 - HEALTHSIZE/2;
        x = x - 428;
        y = y - 1234;
        var xMult = Math.ceil(tile.unit.status.hp / 10) - 1;
        x = x - xMult - xMult * HEALTHSIZE;
        var healthTexture = new Two.Texture(unitsSrc, () => ontextureLoad(unitsSrc));
        healthTexture.offset = new Two.Vector(x, y);
        health = two.makeRectangle(tile.x * TILESIZE + TILESIZE - HEALTHSIZE/2, tile.y * TILESIZE + TILESIZE - HEALTHSIZE/2, HEALTHSIZE, HEALTHSIZE);
        health.fill = healthTexture;
        health.stroke = 'transparent';
    }
    if (tile.unit.status.fuel <= 30) {
        const FUELSIZE = SPRITESIZE/2;
        x = spriteSheetWidth/2 - FUELSIZE/2;
        y = spriteSheetHeight/2 - FUELSIZE/2;
        x = x - 651;
        y = y - 1241;
        var fuelTexture = new Two.Texture(unitsSrc, () => ontextureLoad(unitsSrc));
        fuelTexture.offset = new Two.Vector(x, y);
        fuel = two.makeRectangle(tile.x * TILESIZE + TILESIZE - FUELSIZE/2 - 8, tile.y * TILESIZE + TILESIZE - FUELSIZE/2 - 8, FUELSIZE, FUELSIZE);
        fuel.fill = fuelTexture;
        fuel.stroke = 'transparent';
    }
    if (!tile.unit.UnitType == 0 && tile.unit.status.ammo <= 3) {
        const AMMOSIZE = SPRITESIZE/2;
        x = spriteSheetWidth/2 - AMMOSIZE/2;
        y = spriteSheetHeight/2 - AMMOSIZE/2;
        x = x - 651;
        y = y - 1251;
        var ammoTexture = new Two.Texture(unitsSrc, () => ontextureLoad(unitsSrc));
        ammoTexture.offset = new Two.Vector(x, y);
        ammo = two.makeRectangle(tile.x * TILESIZE + TILESIZE - AMMOSIZE/2, tile.y * TILESIZE + TILESIZE - AMMOSIZE/2 - 8, AMMOSIZE -2, AMMOSIZE -2);
        ammo.fill = ammoTexture;
        ammo.stroke = 'transparent';
    }
    if (tile.capture_hp <= 19) {
        const FLAGSIZE = SPRITESIZE/2;
        x = spriteSheetWidth/2 - FLAGSIZE/2;
        y = spriteSheetHeight/2 - FLAGSIZE/2;
        x = x - 530;
        y = y - 1233;
        var flagTexture = new Two.Texture(unitsSrc, () => ontextureLoad(unitsSrc));
        flagTexture.offset = new Two.Vector(x, y);
        flag = two.makeRectangle(tile.x * TILESIZE + TILESIZE - FLAGSIZE/2 - 8, tile.y * TILESIZE + TILESIZE - FLAGSIZE/2, FLAGSIZE, FLAGSIZE);
        flag.fill = flagTexture;
        flag.stroke = 'transparent';
    }
    if (tile.unit.status.cargo[0] ||
        tile.unit.status.cargo[1]) {
        const LOADSIZE = SPRITESIZE/2;
        x = spriteSheetWidth/2 - LOADSIZE/2;
        y = spriteSheetHeight/2 - LOADSIZE/2;
        x = x - 520;
        y = y - 1233;
        var loadTexture = new Two.Texture(unitsSrc, () => ontextureLoad(unitsSrc));
        loadTexture.offset = new Two.Vector(x, y);
        load = two.makeRectangle(tile.x * TILESIZE + TILESIZE - LOADSIZE/2 - 8, tile.y * TILESIZE + TILESIZE - LOADSIZE/2, LOADSIZE, LOADSIZE);
        load.fill = loadTexture;
        load.stroke = 'transparent';
    }
    return rect;
}

function createScene() {
    // create game tiles
    for (var i = 0; i < board.height; i++) {
        for (var j = 0; j < board.width; j++) {
            var tile = board.grid[j + i * board.width];
            // create map file
            makeMapTile(tile);
            // create sprite
            if (tile.unit !== null) {
                makeSprite(tile);
            }
        }
    }
}
