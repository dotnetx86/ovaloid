const WebSocket = require('ws');
const { v4: uuidv4 } = require('uuid');

const WIDTH = 1024;
const HEIGHT = 768;
const wss = new WebSocket.Server({ port: 8080 });
let players = {};

wss.on('connection', function connection(ws) {
  const clientId = uuidv4();

  players[clientId] = {
    socket: ws,
    coords: [WIDTH / 2, HEIGHT / 2, WIDTH / 2 + 50, HEIGHT / 2 + 50]
  };
  
  function sendAll(msg) {
    Object.entries(players).forEach(([id, data]) => {
      if (id === clientId) return;
  
      data.socket.send(JSON.stringify(msg));
    })
  }

  sendAll({ type: "new", data: { id: clientId, coords: players[clientId].coords } });
  
  console.log('New client connected');

  ws.on('message', function incoming(message) {
    console.log('received: %s', message);
    msg = JSON.parse(message);

    switch (msg.type) {
      case "login":
        const res = Object.fromEntries(Object.entries(players).map(([id, data]) => {
          const { socket, ...rest } = data;
          return [id, rest];
        }));
        ws.send(JSON.stringify({ type: msg.type, data: { id: clientId, players: res } }));
        break;
      
      case "move":
        players[clientId].coords = msg.data.coords;

        sendAll({ type: msg.type, data: { id: clientId, coords: msg.data.coords } });
        break;
      
      case "projectile":
        sendAll({ type: msg.type, data: { id: clientId, coords: msg.data.coords, direction: msg.data.direction, speed: msg.data.speed } });
        break;
    }
  });

  ws.on('close', () => {
    delete players[clientId]
    console.log(`Client disconnected clients: ${JSON.stringify(players)}`);
  });
});