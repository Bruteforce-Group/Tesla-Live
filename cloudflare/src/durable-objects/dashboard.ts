export class DashboardDO {
  private sessions: Map<WebSocket, { id: string; vehicleFilter?: string }> = new Map();
  private state: DurableObjectState;

  constructor(state: DurableObjectState) {
    this.state = state;
  }

  async fetch(request: Request): Promise<Response> {
    const url = new URL(request.url);

    if (request.headers.get('Upgrade') === 'websocket') {
      const pair = new WebSocketPair();
      const [client, server] = Object.values(pair);

      this.handleSession(server);

      return new Response(null, {
        status: 101,
        webSocket: client,
      });
    }

    if (url.pathname === '/broadcast' && request.method === 'POST') {
      const message = await request.json();
      this.broadcast(JSON.stringify(message));
      return new Response('OK');
    }

    return new Response('Not found', { status: 404 });
  }

  private handleSession(ws: WebSocket) {
    ws.accept();

    const sessionId = crypto.randomUUID();
    this.sessions.set(ws, { id: sessionId });

    ws.addEventListener('message', async (event) => {
      try {
        const message = JSON.parse(event.data as string);

        switch (message.type) {
          case 'subscribe': {
            const session = this.sessions.get(ws);
            if (session) {
              session.vehicleFilter = message.vehicle_id;
            }
            break;
          }
          case 'ping':
            ws.send(JSON.stringify({ type: 'pong' }));
            break;
        }
      } catch (e) {
        console.error('WebSocket message error:', e);
      }
    });

    ws.addEventListener('close', () => {
      this.sessions.delete(ws);
    });

    ws.addEventListener('error', () => {
      this.sessions.delete(ws);
    });
  }

  private broadcast(message: string) {
    const parsed = JSON.parse(message);

    for (const [ws, session] of this.sessions) {
      try {
        if (session.vehicleFilter && parsed.data?.vehicle_id) {
          if (session.vehicleFilter !== parsed.data.vehicle_id) {
            continue;
          }
        }

        ws.send(message);
      } catch (_e) {
        this.sessions.delete(ws);
      }
    }
  }
}
