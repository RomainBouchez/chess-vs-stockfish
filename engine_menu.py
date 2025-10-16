import pygame
import threading
from pygame.locals import *
from engine_manager import EngineManager

class EngineMenu:
    """Interface graphique pour gérer les moteurs d'échecs (UI moderne)"""
    
    def __init__(self, screen):
        self.screen = screen
        self.engine_manager = EngineManager()
        
        # --- UI Style Constants ---
        self.WIDTH = self.screen.get_width()
        self.BG_COLOR = (20, 20, 20)
        self.ITEM_BG_COLOR = (40, 40, 40)
        self.TEXT_COLOR = (220, 220, 220)
        self.SUBTEXT_COLOR = (170, 170, 170)
        self.INACTIVE_COLOR = (80, 80, 80)
        self.ACTIVE_COLOR = (0, 120, 215)
        self.GREEN = (34, 177, 76)
        self.RED = (237, 28, 36)
        
        # --- Fonts ---
        self.title_font = pygame.font.Font(None, 40)
        self.normal_font = pygame.font.Font(None, 28)
        self.small_font = pygame.font.Font(None, 22)
        
        self.downloading, self.download_progress, self.download_engine, self.download_error = False, 0, None, None
        self.refresh_lists()
        self.scroll_y, self.max_scroll = 0, 0
        
    def refresh_lists(self):
        self.available_engines = self.engine_manager.get_available_engines()
        self.installed_engines = self.engine_manager.get_installed_engines()
        self.selected_engine = self.engine_manager.get_default_engine()

    def save_selected_engine(self, engine_id):
        self.engine_manager.select_engine(engine_id)
        self.selected_engine = engine_id
    
    def draw_engine_item(self, engine_id, engine_info, y_pos, is_installed=False):
        item_rect = pygame.Rect(50, y_pos, self.WIDTH - 100, 80)
        pygame.draw.rect(self.screen, self.ITEM_BG_COLOR, item_rect, border_radius=8)
        
        # Highlight border if selected or installed
        if is_installed:
            color = self.GREEN if engine_id == self.selected_engine else self.ACTIVE_COLOR
            pygame.draw.rect(self.screen, color, item_rect, 2, border_radius=8)
        
        name_text = self.normal_font.render(engine_info.get("name", engine_id), True, self.TEXT_COLOR)
        self.screen.blit(name_text, (70, y_pos + 10))
        
        desc_text = self.small_font.render(f"Version: {engine_info.get('version', 'N/A')}", True, self.SUBTEXT_COLOR)
        self.screen.blit(desc_text, (70, y_pos + 40))
        
        # Action Buttons
        button_x = self.WIDTH - 200
        if is_installed:
            if engine_id != self.selected_engine:
                select_btn = self.draw_small_button("Select", (button_x, y_pos + 10), self.ACTIVE_COLOR)
            uninstall_btn = self.draw_small_button("Uninstall", (button_x, y_pos + 45), self.RED)
        else:
            if self.downloading and self.download_engine == engine_id:
                progress_text = f"{int(self.download_progress)}%"
                self.draw_small_button(progress_text, (button_x, y_pos + 25), self.INACTIVE_COLOR)
            else:
                self.draw_small_button("Download", (button_x, y_pos + 25), self.GREEN)
        
        return item_rect.bottom + 10

    def draw_small_button(self, label, pos, color):
        rect = pygame.Rect(pos[0], pos[1], 140, 30)
        pygame.draw.rect(self.screen, color, rect, border_radius=5)
        text_surf = self.small_font.render(label, True, self.TEXT_COLOR)
        self.screen.blit(text_surf, text_surf.get_rect(center=rect.center))
        return rect

    def draw_header(self):
        title = self.title_font.render("Manage Chess Engines", True, self.TEXT_COLOR)
        self.screen.blit(title, title.get_rect(center=(self.WIDTH // 2, 40)))
        
        if self.download_error:
            error_surf = self.normal_font.render(f"Error: {self.download_error}", True, self.RED)
            self.screen.blit(error_surf, error_surf.get_rect(center=(self.WIDTH // 2, 80)))
    
    def draw_engines_list(self):
        y_pos = 120 - self.scroll_y
        
        # Installed Engines
        if self.installed_engines:
            title = self.normal_font.render("Installed Engines:", True, self.TEXT_COLOR)
            if y_pos > 0 and y_pos < self.screen.get_height(): self.screen.blit(title, (50, y_pos))
            y_pos += 40
            for engine_id, info in self.installed_engines.items():
                if y_pos > -90 and y_pos < self.screen.get_height(): y_pos = self.draw_engine_item(engine_id, info, y_pos, True)
                else: y_pos += 90
            y_pos += 20
        
        # Available Engines
        available = {k: v for k, v in self.available_engines.items() if k not in self.installed_engines}
        if available:
            title = self.normal_font.render("Available for Download:", True, self.TEXT_COLOR)
            if y_pos > 0 and y_pos < self.screen.get_height(): self.screen.blit(title, (50, y_pos))
            y_pos += 40
            for engine_id, info in available.items():
                if y_pos > -90 and y_pos < self.screen.get_height(): y_pos = self.draw_engine_item(engine_id, info, y_pos, False)
                else: y_pos += 90
        
        self.max_scroll = max(0, y_pos + self.scroll_y - self.screen.get_height() + 80)
    
    def draw_footer_buttons(self):
        self.draw_small_button("Back (ESC)", (50, self.screen.get_height() - 50), self.INACTIVE_COLOR)
        self.draw_small_button("Refresh", (self.WIDTH - 190, self.screen.get_height() - 50), self.ACTIVE_COLOR)

    def draw(self):
        self.screen.fill(self.BG_COLOR)
        self.draw_header()
        self.draw_engines_list()
        self.draw_footer_buttons()

    def download_engine_thread(self, engine_id):
        try:
            self.downloading, self.download_engine, self.download_error, self.download_progress = True, engine_id, None, 0
            self.engine_manager.download_engine(engine_id, lambda p: setattr(self, 'download_progress', p))
            self.refresh_lists()
        except Exception as e: self.download_error = str(e)
        finally: self.downloading = False

    def handle_click(self, pos):
        # Footer buttons
        if pygame.Rect(50, self.screen.get_height() - 50, 140, 30).collidepoint(pos): return "back"
        if pygame.Rect(self.WIDTH - 190, self.screen.get_height() - 50, 140, 30).collidepoint(pos): self.refresh_lists(); return
        
        y_pos = 120 - self.scroll_y
        if self.installed_engines:
            y_pos += 40
            for engine_id, info in self.installed_engines.items():
                if pygame.Rect(50, y_pos, self.WIDTH - 100, 80).collidepoint(pos):
                    btn_x = self.WIDTH - 200
                    if engine_id != self.selected_engine and pygame.Rect(btn_x, y_pos + 10, 140, 30).collidepoint(pos):
                        self.save_selected_engine(engine_id)
                    elif pygame.Rect(btn_x, y_pos + 45, 140, 30).collidepoint(pos):
                        self.engine_manager.uninstall_engine(engine_id); self.refresh_lists()
                y_pos += 90
            y_pos += 20
        
        available = {k: v for k, v in self.available_engines.items() if k not in self.installed_engines}
        if available:
            y_pos += 40
            for engine_id, info in available.items():
                if pygame.Rect(50, y_pos, self.WIDTH - 100, 80).collidepoint(pos) and not self.downloading:
                    if pygame.Rect(self.WIDTH - 200, y_pos + 25, 140, 30).collidepoint(pos):
                        threading.Thread(target=self.download_engine_thread, args=(engine_id,), daemon=True).start()
                y_pos += 90

    def run(self):
        clock, running = pygame.time.Clock(), True
        while running:
            for event in pygame.event.get():
                if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE): running = False
                elif event.type == MOUSEBUTTONDOWN:
                    if event.button == 1 and self.handle_click(event.pos) == "back": running = False
                    elif event.button == 4: self.scroll_y = max(0, self.scroll_y - 30)
                    elif event.button == 5: self.scroll_y = min(self.max_scroll, self.scroll_y + 30)
            self.draw()
            pygame.display.flip()
            clock.tick(60)
        return "back"