const WebSocket = require('ws');
const { v4: uuidv4 } = require('uuid');

const wss = new WebSocket.Server({ port: 8080 });

wss.on('connection', function connection(ws) {
  const clientId = uuidv4();
  wss.clients.forEach(function each(client) {
    if (client.readyState === WebSocket.OPEN && client !== ws) {
      client.send(JSON.stringify({ type: "new", data: { "id": clientId } }));
    }
  });
  console.log('New client connected');

  ws.on('message', function incoming(message) {
    console.log('received: %s', message);

    if (JSON.parse(message).type === "login") {
        console.log("senddd");
        ws.send(JSON.stringify({ type: "login", data: { "id": clientId } }))
        return
    }

    // Рассылаем сообщение всем подключённым клиентам
    wss.clients.forEach(function each(client) {
      if (client.readyState === WebSocket.OPEN && client !== ws) {
        client.send(message.toString());
      }
    });
  });

  ws.on('close', () => {
    console.log('Client disconnected');
  });
});

console.log('WebSocket server is running on ws://localhost:8080');
