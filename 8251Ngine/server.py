import asyncio
import websockets
import json
import time
import random # For random roles

# settings.py에서 필요한 상수들을 임포트해야 합니다.
# 8251Ngine/settings.py에서 TILE_SIZE, NETWORK_PORT, DEFAULT_PHASE_DURATIONS 등을 가져옵니다.
from settings import NETWORK_PORT, DEFAULT_PHASE_DURATIONS

class GameServer:
    def __init__(self):
        self.host = "0.0.0.0"
        self.port = NETWORK_PORT # from settings
        self.connected_clients = {} # {websocket: player_id}
        self.players = {} # {player_id: data}
        self.next_id = 0
        self.game_started = False
        
        # Time Management (from PxANIC! server)
        self.phases = ["DAWN", "MORNING", "NOON", "AFTERNOON", "EVENING", "NIGHT"]
        self.current_phase_idx = 0
        self.day_count = 1
        self.state_timer = DEFAULT_PHASE_DURATIONS[self.phases[0]]
        self.last_tick = time.time()
        self.game_loop_task = None

    async def start(self):
        # 8765 포트로 변경
        self.server = await websockets.serve(self.handle_client, self.host, 8765) # NETWORK_PORT 대신 8765
        print(f"[SERVER] Running on ws://{self.host}:8765") # NETWORK_PORT 대신 8765

        # 게임 루프를 비동기 태스크로 시작
        self.game_loop_task = asyncio.create_task(self._game_loop())

        await self.server.wait_closed()

    async def _game_loop(self):
        while True:
            await asyncio.sleep(0.1) # 100ms 간격
            if not self.game_started: continue
            
            now = time.time()
            dt = now - self.last_tick
            self.last_tick = now
            
            self.state_timer -= dt
            if self.state_timer <= 0:
                self._advance_phase()
                
            # 매 초마다 TIME_SYNC 브로드캐스트 (PxANIC! 서버 로직 참고)
            if int(now * 10) % 10 == 0: # 1초에 한 번 (0.1초 간격으로 체크하므로 10번마다)
                await self._broadcast({"type": "TIME_SYNC", "phase_idx": self.current_phase_idx, "timer": self.state_timer, "day": self.day_count})
            
            # TODO: 다른 서버 측 게임 로직 업데이트 (NPC AI, 이벤트 등)

    async def _advance_phase(self):
        self.current_phase_idx = (self.current_phase_idx + 1) % len(self.phases)
        new_phase = self.phases[self.current_phase_idx]
        if new_phase == "DAWN": self.day_count += 1
        self.state_timer = DEFAULT_PHASE_DURATIONS.get(new_phase, 30) # Default to 30 if not found
        await self._broadcast({"type": "TIME_SYNC", "phase_idx": self.current_phase_idx, "timer": self.state_timer, "day": self.day_count})
        print(f"[SERVER] Phase Advanced: Day {self.day_count}, {new_phase}")

    async def handle_client(self, websocket, path):
        player_id = self.next_id
        self.next_id += 1
        self.connected_clients[websocket] = player_id
        
        # PxANIC! 서버의 초기 플레이어 데이터 구조 참고
        self.players[player_id] = {
            'id': player_id, 'name': f"Player {player_id+1}", 'role': 'CITIZEN',
            'group': 'PLAYER', 'type': 'PLAYER', 'x': -1000, 'y': -1000, 'alive': True
        }

        print(f"[SERVER] Client connected: {player_id}")
        
        try:
            # Welcome message with assigned ID
            await websocket.send(json.dumps({"type": "id_assignment", "id": player_id}))
            
            # Broadcast updated player list to all clients
            await self._broadcast_player_list()

            async for message in websocket:
                try:
                    payload = json.loads(message)
                    await self._process_message(player_id, payload)
                except json.JSONDecodeError as e:
                    print(f"[SERVER] JSON Error from {player_id}: {e}")
                except Exception as e:
                    print(f"[SERVER] Message processing Error from {player_id}: {e}")
        except websockets.exceptions.ConnectionClosed:
            print(f"[SERVER] Client disconnected: {player_id}")
        except Exception as e:
            print(f"[SERVER] Client handling Error for {player_id}: {e}")
        finally:
            del self.connected_clients[websocket]
            if player_id in self.players:
                del self.players[player_id]
            await self._broadcast_player_list() # Update player list after disconnect

    async def _process_message(self, sender_id, data):
        ptype = data.get('type')
        
        # PxANIC! server의 process_packet 로직 이식
        if ptype == 'UPDATE_ROLE':
            target_id = data.get('id', sender_id)
            if target_id in self.players:
                self.players[target_id]['role'] = data.get('role')
                await self._broadcast_player_list()
        elif ptype == 'CHANGE_GROUP':
            tid = data.get('target_id')
            if tid in self.players:
                self.players[tid]['group'] = data.get('group')
                await self._broadcast_player_list()
        elif ptype == 'ADD_BOT':
            # PxANIC! server의 next_id 로직과 유사하게 봇 ID 할당
            bot_id = self.next_id
            self.next_id += 1
            self.players[bot_id] = {
                'id': bot_id, 'name': data.get('name', f"Bot {bot_id+1}"), 'role': 'RANDOM',
                'group': data.get('group', 'BOT'), 'type': 'BOT', 'x': -1000, 'y': -1000, 'alive': True
            }
            await self._broadcast_player_list()
        elif ptype == 'REMOVE_BOT':
            target_id = data.get('target_id')
            if target_id in self.players and self.players[target_id].get('type') == 'BOT':
                del self.players[target_id]
                await self._broadcast_player_list()
        elif ptype == 'START_GAME':
            # PxANIC! server의 pid == 0 (호스트) 체크
            if sender_id == 0: 
                # Game Start Logic
                available_roles = ["FARMER", "MINER", "FISHER", "POLICE", "MAFIA", "DOCTOR"]
                for p_data in self.players.values():
                    if p_data['role'] == 'RANDOM': # Only assign to 'RANDOM' roles
                        p_data['role'] = random.choice(available_roles)
                
                self.game_started = True
                self.last_tick = time.time()
                await self._broadcast({"type": "GAME_START", "players": self.players})
                print("[SERVER] Game Started!")
        elif ptype == 'MOVE':
            mid = data.get('id', sender_id)
            if mid in self.players:
                self.players[mid].update({
                    'x': data['x'], 'y': data['y'], 
                    'facing': data.get('facing', self.players[mid].get('facing')), 
                    'is_moving': data.get('is_moving', False)
                })
                # Exclude sender, as they already know their position
                await self._broadcast(data, exclude_pid=sender_id)
        # TODO: Add other message types from PxANIC! server (e.g., chat, item usage, skill use, etc.)
    
    async def _broadcast_player_list(self):
        await self._broadcast({"type": "PLAYER_LIST", "participants": list(self.players.values())})

    async def _broadcast(self, message, exclude_pid=None):
        if not self.connected_clients: return
        serialized_message = json.dumps(message)
        
        # PxANIC!의 브로드캐스트 로직 이식
        # 웹소켓은 메시지 길이 헤더를 자동으로 처리
        await asyncio.gather(*[
            client.send(serialized_message)
            for client, pid in self.connected_clients.items()
            if pid != exclude_pid
        ])

async def main():
    server = GameServer()
    await server.start()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("[SERVER] Server stopped by user.")