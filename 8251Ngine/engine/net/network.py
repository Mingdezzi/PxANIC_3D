import asyncio
import websockets
import json
import threading
from asyncio import Queue

class NetworkManager:
    def __init__(self, uri):
        self.uri = uri
        self.websocket = None
        self.incoming_messages = Queue()
        self.outgoing_messages = Queue()
        self.client_id = None
        self.loop = None
        self.thread = None
        self.running = False

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._run_event_loop, daemon=True)
        self.thread.start()

    def _run_event_loop(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        try:
            self.loop.run_until_complete(self._run_client())
        except Exception as e:
            pass
        finally:
            self.loop.close()

    async def _run_client(self):
        while self.running:
            try:
                async with websockets.connect(self.uri) as websocket:
                    self.websocket = websocket
                    print("Connected to server.")
                    
                    initial_message = await websocket.recv()
                    data = json.loads(initial_message)
                    if data.get('type') == 'id_assignment':
                        self.client_id = data['id']
                        print(f"Assigned Client ID: {self.client_id}")
                    
                    recv_task = asyncio.create_task(self._receive_handler())
                    send_task = asyncio.create_task(self._send_handler())
                    
                    done, pending = await asyncio.wait(
                        [recv_task, send_task],
                        return_when=asyncio.FIRST_COMPLETED
                    )
                    
                    for task in pending:
                        task.cancel()
                        
            except (websockets.ConnectionClosed, ConnectionRefusedError, OSError):
                if self.running:
                    await asyncio.sleep(2)
            except Exception as e:
                if self.running:
                    await asyncio.sleep(2)
            finally:
                self.websocket = None

    async def _receive_handler(self):
        try:
            async for message in self.websocket:
                await self.incoming_messages.put(json.loads(message))
        except:
            pass

    async def _send_handler(self):
        try:
            while True:
                message = await self.outgoing_messages.get()
                if self.websocket:
                    await self.websocket.send(json.dumps(message))
                self.outgoing_messages.task_done()
        except asyncio.CancelledError:
            pass
        except:
            pass

    def send(self, data):
        if self.loop and self.loop.is_running():
            self.loop.call_soon_threadsafe(self.outgoing_messages.put_nowait, data)

    def get_messages(self):
        messages = []
        while not self.incoming_messages.empty():
            try:
                messages.append(self.incoming_messages.get_nowait())
            except:
                break
        return messages

    def stop(self):
        self.running = False
