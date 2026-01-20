import asyncio
import websockets
import json
import uuid

connected_clients = {}

async def handler(websocket):
    client_id = str(uuid.uuid4())
    connected_clients[client_id] = websocket
    print(f"Client {client_id} connected.")

    try:
        await websocket.send(json.dumps({"type": "id_assignment", "id": client_id}))

        async for message in websocket:
            # 모든 다른 클라이언트에게 메시지 브로드캐스트
            for cid, ws in connected_clients.items():
                if ws != websocket:
                    await ws.send(message)
    except websockets.ConnectionClosed:
        print(f"Client {client_id} disconnected.")
    finally:
        del connected_clients[client_id]
        # 다른 클라이언트에게 연결 종료 알림
        for ws in connected_clients.values():
            await ws.send(json.dumps({"type": "disconnect", "id": client_id}))

async def main():
    server = await websockets.serve(handler, "localhost", 8765)
    print("Server is running on ws://localhost:8765")
    await server.wait_closed()

if __name__ == "__main__":
    asyncio.run(main())
