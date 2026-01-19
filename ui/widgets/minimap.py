import pygame
from ui.widgets.base import UIWidget
from settings import TILE_SIZE, ZONES # ZONES 추가
from world.tiles import TILE_DATA

# 기본 색상 (TILE_DATA에 없는 경우 대비)
DEFAULT_COLORS = {'floor': (40, 40, 40), 'wall': (100, 100, 100), 'object': (200, 200, 100)}

class MinimapWidget(UIWidget):
    def __init__(self, game):
        super().__init__(game)
        self.minimap_surface = None
        self.cached_minimap = None
        self.radar_timer = 0
        self.radar_blips = []
        self.rect = pygame.Rect(0, 0, 0, 0) # Click detection

    def _generate_surface(self):
        w, h = self.game.map_manager.width, self.game.map_manager.height
        surf = pygame.Surface((w, h))
        surf.fill((20, 20, 25))
        pixels = pygame.PixelArray(surf)
        
        # [수정] 3D 레이어 순회 (Painter's Algorithm)
        # 아래층(0)부터 위층으로 그리면서 덮어씌웁니다.
        # 이렇게 하면 가장 높은 층의 구조물이 미니맵에 표시됩니다.
        for z in range(len(self.game.map_manager.layers)):
            layer = self.game.map_manager.layers[z]
            floors = layer['floor']
            walls = layer['wall']
            objects = layer['object']

            for y in range(h):
                for x in range(w):
                    color = None
                    
                    # 1. Object (최우선)
                    o_val = objects[y][x]
                    o_tid = o_val[0] if isinstance(o_val, (tuple, list)) else o_val
                    if o_tid != 0 and o_tid in TILE_DATA:
                        color = TILE_DATA[o_tid].get('color')
                    
                    # 2. Wall
                    if color is None:
                        w_val = walls[y][x]
                        w_tid = w_val[0] if isinstance(w_val, (tuple, list)) else w_val
                        if w_tid != 0 and w_tid in TILE_DATA:
                            color = TILE_DATA[w_tid].get('color')
                    
                    # 3. Floor
                    if color is None:
                        f_val = floors[y][x]
                        f_tid = f_val[0] if isinstance(f_val, (tuple, list)) else f_val
                        if f_tid != 0 and f_tid in TILE_DATA:
                            color = TILE_DATA[f_tid].get('color')
                    
                    # 픽셀 업데이트 (해당 층에 타일이 있다면 덮어씀)
                    if color:
                        pixels[x, y] = color
                    
                    # [추가] Zone 표시 (Z=0일 때만)
                    if z == 0 and self.game.map_manager.zone_map and \
                       0 <= y < len(self.game.map_manager.zone_map) and \
                       0 <= x < len(self.game.map_manager.zone_map[y]):
                        zid = self.game.map_manager.zone_map[y][x]
                        if zid != 0 and zid in ZONES:
                            # 기존 색상과 블렌딩 (반투명하게)
                            zone_color = ZONES[zid]['color']
                            current_pixel_color = pixels[x, y] # 현재 픽셀 색상 가져오기
                            # RGB만 추출 (알파값 제외)
                            r1, g1, b1, _ = current_pixel_color # PixelArray는 RGBA를 반환
                            r2, g2, b2, a2 = zone_color

                            # 간단한 알파 블렌딩 (덮어쓰는 개념이므로 반투명도 낮춤)
                            alpha_ratio = a2 / 255.0 * 0.5 # 50% 반투명
                            blended_r = int(r1 * (1 - alpha_ratio) + r2 * alpha_ratio)
                            blended_g = int(g1 * (1 - alpha_ratio) + g2 * alpha_ratio)
                            blended_b = int(b1 * (1 - alpha_ratio) + b2 * alpha_ratio)
                            pixels[x,y] = (blended_r, blended_g, blended_b)

        pixels.close()
        return surf

    def draw(self, screen):
        # Spectator check (Optional)
        # if self.game.player.role == "SPECTATOR": return

        w, h = screen.get_size()
        mm_w, mm_h = 220, 220
        x = w - mm_w - 20
        y = h - mm_h - 20 
        
        mm_rect = pygame.Rect(x, y, mm_w, mm_h)
        self.rect = mm_rect 
        
        # Background
        s = pygame.Surface((mm_rect.width, mm_rect.height), pygame.SRCALPHA)
        s.fill((0, 0, 0, 180))
        screen.blit(s, mm_rect.topleft)
        pygame.draw.rect(screen, (100, 100, 120), mm_rect, 2)
        
        # Generate Map if needed
        if not self.minimap_surface:
            self.minimap_surface = self._generate_surface()
            self.cached_minimap = pygame.transform.scale(self.minimap_surface, (mm_w - 4, mm_h - 4))
            
        screen.blit(self.cached_minimap, (mm_rect.x + 2, mm_rect.y + 2))
        
        # Player Dot
        map_w_px = self.game.map_manager.width * TILE_SIZE
        map_h_px = self.game.map_manager.height * TILE_SIZE
        
        if map_w_px > 0:
            # 플레이어 위치 비율 계산
            dot_x = mm_rect.x + 2 + (self.game.player.rect.centerx / map_w_px) * (mm_w - 4)
            dot_y = mm_rect.y + 2 + (self.game.player.rect.centery / map_h_px) * (mm_h - 4)
            
            # 플레이어 색상 (역할별)
            p_col = (0, 255, 0)
            if self.game.player.role == 'MAFIA': p_col = (255, 50, 50)
            elif self.game.player.role == 'POLICE': p_col = (50, 100, 255)
            
            pygame.draw.circle(screen, p_col, (int(dot_x), int(dot_y)), 3)

        # Radar / Special Detection
        self._draw_radar(screen, mm_rect, map_w_px, map_h_px, mm_w, mm_h)

    def _draw_radar(self, screen, mm_rect, map_w, map_h, mm_w, mm_h):
        is_blackout = getattr(self.game, 'is_blackout', False)
        player = self.game.player
        
        # 1. Police CCTV Passive
        if player.role == "POLICE":
            cctv_tid = 7310011
            cctv_locs = self.game.map_manager.tile_cache.get(cctv_tid, [])
            
            for loc in cctv_locs:
                # [수정] 3D 좌표 대응 (x, y, z) -> (x, y) 추출
                if len(loc) == 3: cx, cy, cz = loc
                else: cx, cy = loc; cz = 0
                
                # Minimap Coords
                mx = mm_rect.x + 2 + ((cx + TILE_SIZE//2) / map_w) * (mm_w - 4)
                my = mm_rect.y + 2 + ((cy + TILE_SIZE//2) / map_h) * (mm_h - 4)
                
                # Check motion near CCTV
                motion_detected = False
                for n in self.game.npcs:
                    if n.alive and getattr(n, 'is_moving', False):
                        # 거리 체크 (Z축 무시하고 평면 거리만 체크)
                        dist_sq = (n.rect.centerx - (cx+16))**2 + (n.rect.centery - (cy+16))**2
                        if dist_sq < (5 * TILE_SIZE)**2: 
                            motion_detected = True
                            break
                
                # Draw CCTV Dot
                col = (150, 0, 255) 
                if motion_detected:
                    if (pygame.time.get_ticks() // 200) % 2 == 0:
                        pygame.draw.circle(screen, (255, 100, 255), (int(mx), int(my)), 4)
                        pygame.draw.circle(screen, col, (int(mx), int(my)), 6, 1)
                else:
                    pygame.draw.rect(screen, col, (int(mx)-2, int(my)-2, 4, 4))

        # 2. Mafia Blackout Radar
        elif player.role == "MAFIA" and is_blackout:
            now = pygame.time.get_ticks()
            if now > self.radar_timer:
                self.radar_timer = now + 2000
                self.radar_blips = []
                for n in self.game.npcs:
                    if not n.alive: continue
                    color = (0, 255, 0)
                    if n.role == "POLICE": color = (0, 100, 255)
                    elif n.role == "MAFIA": color = (255, 0, 0)
                    nx = mm_rect.x + 2 + (n.rect.centerx / map_w) * (mm_w - 4)
                    ny = mm_rect.y + 2 + (n.rect.centery / map_h) * (mm_h - 4)
                    self.radar_blips.append(((int(nx), int(ny)), color))
            for pos, col in self.radar_blips: pygame.draw.circle(screen, col, pos, 4)
        
        # 3. Citizen/Doctor Proximity Sensor
        elif player.device_on and player.role in ["CITIZEN", "DOCTOR"]:
             for n in self.game.npcs:
                if not n.alive: continue
                # 같은 층(Z)에 있는 NPC만 감지할지 결정 필요 (여기서는 Z 무시하고 모두 감지)
                dist_sq = (player.rect.centerx - n.rect.centerx)**2 + (player.rect.centery - n.rect.centery)**2
                if dist_sq < 400**2 and getattr(n, 'is_moving', False):
                     nx = mm_rect.x + 2 + (n.rect.centerx / map_w) * (mm_w - 4)
                     ny = mm_rect.y + 2 + (n.rect.centery / map_h) * (mm_h - 4)
                     pygame.draw.circle(screen, (0, 255, 0), (int(nx), int(ny)), 3)
