const WebSocket = require('ws');
const { v4: uuidv4 } = require('uuid');

const WIDTH = 1024;
const HEIGHT = 768;
const wss = new WebSocket.Server({ port: 8080 });
let players = {};

wss.on('connection', function connection(ws) {
  const clientId = uuidv4();
  
  function sendAll(msg, all=false) {
    Object.entries(players).forEach(([id, data]) => {
      if (id === clientId && !all) return;
  
      data.socket.send(JSON.stringify(msg));
    })
  }

  console.log('New client connected');

  ws.on('message', function incoming(message) {
    console.log('received: %s', message);
    msg = JSON.parse(message);

    switch (msg.type) {
      case "login":
        players[clientId] = {
          socket: ws,
          coords: [WIDTH / 2, HEIGHT / 2],
          health: 100,
          class: msg.class
        };
        
        const res = Object.fromEntries(Object.entries(players).map(([id, data]) => {
          const { socket, ...rest } = data;
          return [id, rest];
        }));


        sendAll({ type: "new", data: { id: clientId, coords: players[clientId].coords, class: players[clientId].class } });
        ws.send(JSON.stringify({ type: msg.type, data: { id: clientId, players: res } }));
        break;
      
      case "move":
        players[clientId].coords = msg.data.coords;

        sendAll({ type: msg.type, data: { id: clientId, coords: msg.data.coords } });
        break;
      
      case "projectile":
        sendAll({ type: msg.type, data: { id: clientId, coords: msg.data.coords, direction: msg.data.direction, speed: msg.data.speed } });
        break;

      case "health":
        if (msg.data.health <= 0) {
          players[clientId].health = 0
          sendAll({ type: "death", data: { id: clientId } }, true)
          setTimeout(() => {
            if (!players[clientId]) return
            console.log("respawnin");
            players[clientId].health = 100
            players[clientId].coords = [WIDTH / 2, HEIGHT / 2]
            sendAll({ type: "respawn", data: { id: clientId, coords: players[clientId].coords } }, true)
          }, 2000);
        }

        players[clientId].health = msg.data.health
        sendAll({ type: msg.type, data: { id: clientId, health: msg.data.health } })
        break;
    }
  });

  ws.on('close', () => {
    delete players[clientId]
    sendAll({ type: "leave", data: { id: clientId } })
    console.log(`Client disconnected clients: ${JSON.stringify(players)}`);
  });
});