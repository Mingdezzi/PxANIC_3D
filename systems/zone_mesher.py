import pygame

class ZoneMesher:
    """
    Scans the map zones and generates merged polygons for building footprints.
    Used for creating unified building shadows.
    """
    def __init__(self, map_manager):
        self.map_manager = map_manager
        self.building_polygons = [] # List of list of points [(x,y), ...]
        self.tile_size = 32 # Constant
        
        self.INDOOR_ZONES = [6, 7, 8] # House, Hospital, Building
        
        self._build_meshes()

    def _build_meshes(self):
        """Scans the zone map and builds polygons for connected indoor zones."""
        zone_map = self.map_manager.zone_map
        width = self.map_manager.width
        height = self.map_manager.height
        
        visited = set()
        
        for y in range(height):
            for x in range(width):
                if (x, y) in visited:
                    continue
                
                zid = zone_map[y][x]
                if zid in self.INDOOR_ZONES:
                    # Found a new building block, perform flood fill to find all connected tiles
                    # Then generate contour
                    building_tiles = self._flood_fill(x, y, zid, visited)
                    if building_tiles:
                        polygons = self._generate_contour_polygons(building_tiles)
                        self.building_polygons.extend(polygons)

    def _flood_fill(self, start_x, start_y, target_zid, visited):
        """Finds all connected tiles of the same zone."""
        tiles = set()
        stack = [(start_x, start_y)]
        
        while stack:
            cx, cy = stack.pop()
            if (cx, cy) in tiles: continue
            
            tiles.add((cx, cy))
            visited.add((cx, cy))
            
            # Check 4 neighbors
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nx, ny = cx + dx, cy + dy
                if 0 <= nx < self.map_manager.width and 0 <= ny < self.map_manager.height:
                    if (nx, ny) not in visited and (nx, ny) not in tiles:
                        if self.map_manager.zone_map[ny][nx] == target_zid:
                            stack.append((nx, ny))
        return tiles

    def _generate_contour_polygons(self, tiles):
        """
        Generates a polygon outline for a set of grid tiles.
        Simple 'Marching Squares' or just Edge Tracing.
        
        Simpler approach: "Union of Rects" logic for shadows.
        But for true shadow projection, we want the outline.
        
        Actually, for this game perspective, simply iterating rows and merging 
        (like previous Greedy Meshing but for the WHOLE building) is easier and sufficient 
        for generating the base "footprint" rects.
        
        Let's stick to returning a list of Rects that cover the building,
        merged as much as possible horizontally. 
        Shadow renderer will draw shadows for these big rects.
        
        If we want a SINGLE polygon, it's complex. 
        Let's return a list of MERGED RECTS for the building.
        Drawing shadows for these large rects is usually visually close enough to a single polygon 
        if we draw them to a mask.
        """
        
        rects = []
        # Convert tiles set to sorted list
        sorted_tiles = sorted(list(tiles), key=lambda t: (t[1], t[0])) # Sort by Y, then X
        
        if not sorted_tiles: return []
        
        # Group by Y
        rows = {}
        for tx, ty in sorted_tiles:
            if ty not in rows: rows[ty] = []
            rows[ty].append(tx)
            
        # Greedy merge X in each row
        merged_rects = []
        for y, xs in rows.items():
            xs.sort()
            if not xs: continue
            
            curr_x = xs[0]
            width = 1
            
            for i in range(1, len(xs)):
                if xs[i] == curr_x + width:
                    width += 1
                else:
                    merged_rects.append(pygame.Rect(curr_x * self.tile_size, y * self.tile_size, width * self.tile_size, self.tile_size))
                    curr_x = xs[i]
                    width = 1
            merged_rects.append(pygame.Rect(curr_x * self.tile_size, y * self.tile_size, width * self.tile_size, self.tile_size))
            
        # Vertical Merge
        # Sort by X, then Y to find vertical stacks
        merged_rects.sort(key=lambda r: (r.x, r.y))
        
        final_rects = []
        if merged_rects:
            curr_rect = merged_rects[0]
            
            for i in range(1, len(merged_rects)):
                next_rect = merged_rects[i]
                
                # Check alignment and adjacency
                if (curr_rect.x == next_rect.x and 
                    curr_rect.width == next_rect.width and 
                    curr_rect.bottom == next_rect.y):
                    
                    # Merge down
                    curr_rect.height += next_rect.height
                else:
                    final_rects.append(curr_rect)
                    curr_rect = next_rect
            
            final_rects.append(curr_rect)
            
        return final_rects
