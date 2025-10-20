import pygame
from pygame.locals import *
from universal_settings import UniversalEngineSettings
from engine_menu import EngineMenu

class SettingsMenu:
    """Interface graphique pour configurer les moteurs d'échecs (UI moderne)"""
    
    def __init__(self, screen):
        self.screen = screen
        self.universal_settings = UniversalEngineSettings()
        self.mode = "basic"
        self.current_engine = self.universal_settings.get_selected_engine()
        
        # --- UI Style Constants ---
        self.WIDTH = self.screen.get_width()
        self.BG_COLOR = (20, 20, 20)
        self.TEXT_COLOR = (220, 220, 220)
        self.INACTIVE_COLOR = (80, 80, 80)
        self.ACTIVE_COLOR = (0, 120, 215) # A nice blue
        self.SUBTEXT_COLOR = (170, 170, 170)
        self.GREEN = (34, 177, 76)
        self.RED = (237, 28, 36)
        
        # --- Fonts ---
        self.title_font = pygame.font.Font(None, 50)
        self.normal_font = pygame.font.Font(None, 32)
        self.small_font = pygame.font.Font(None, 24)
        
        self.sliders = {}
        self.dragging = None
        self.buttons = {}
        self.setup_buttons()

    def truncate_text(self, font, text, max_width):
        """Return a text possibly truncated with ellipsis to fit into max_width pixels."""
        if font.size(text)[0] <= max_width:
            return text
        ell = '…'
        lo, hi = 0, len(text)
        while lo < hi:
            mid = (lo + hi) // 2
            candidate = text[:mid].rstrip() + ell
            if font.size(candidate)[0] <= max_width:
                lo = mid + 1
            else:
                hi = mid
        return text[:max(0, lo-1)].rstrip() + ell
    
    def setup_buttons(self):
        # Top tabs (fixed positions)
        self.buttons = {
            "basic": pygame.Rect(50, 100, 150, 40),
            "advanced": pygame.Rect(220, 100, 150, 40),
            "engines": pygame.Rect(390, 100, 150, 40),
        }

        # Bottom action buttons: layout dynamically to avoid overlap on narrow windows
        bottom_keys = ["save", "cancel", "reset", "engines_menu"]
        bottom_y = max( self.screen.get_height() - 100, 560 )
        margin = 50
        spacing = 20
        total_width = self.WIDTH - 2 * margin
        # Maximum reasonable width per button
        max_btn_w = 180
        btn_h = 50

        # Compute button width so they fit, otherwise shrink
        btn_w = min(max_btn_w, (total_width - (len(bottom_keys) - 1) * spacing) // len(bottom_keys))

        # If even after shrinking buttons would be too small, wrap into two rows
        min_btn_w = 80
        if btn_w < min_btn_w:
            # two rows layout: split half/half
            first_row = bottom_keys[:2]
            second_row = bottom_keys[2:]
            row_y_offsets = [bottom_y - btn_h - 10, bottom_y]
            for row_idx, row in enumerate([first_row, second_row]):
                row_total = len(row)
                row_btn_w = min(max_btn_w, (total_width - (row_total - 1) * spacing) // row_total)
                start_x = margin + (total_width - (row_btn_w * row_total + spacing * (row_total - 1))) // 2
                for i, key in enumerate(row):
                    x = start_x + i * (row_btn_w + spacing)
                    self.buttons[key] = pygame.Rect(x, row_y_offsets[row_idx], row_btn_w, btn_h)
        else:
            # Single row centered
            start_x = margin + (total_width - (btn_w * len(bottom_keys) + spacing * (len(bottom_keys) - 1))) // 2
            for i, key in enumerate(bottom_keys):
                x = start_x + i * (btn_w + spacing)
                self.buttons[key] = pygame.Rect(x, bottom_y, btn_w, btn_h)
    
    def draw_slider(self, x, y, width, label, value, min_val, max_val, key):
        label_surf = self.normal_font.render(label, True, self.TEXT_COLOR)
        self.screen.blit(label_surf, (x, y))
        
        value_text = str(int(value))
        value_surf = self.normal_font.render(value_text, True, self.ACTIVE_COLOR)
        self.screen.blit(value_surf, (x + width + 20, y + 15))
        
        slider_y = y + 40
        slider_rect = pygame.Rect(x, slider_y, width, 8)
        pygame.draw.rect(self.screen, self.INACTIVE_COLOR, slider_rect, border_radius=4)
        
        ratio = (value - min_val) / (max_val - min_val) if max_val > min_val else 0
        cursor_x = x + int(ratio * width)
        cursor_rect = pygame.Rect(cursor_x - 8, slider_y - 8, 16, 24)
        pygame.draw.rect(self.screen, self.ACTIVE_COLOR, cursor_rect, border_radius=5)
        
        self.sliders[key] = {"rect": slider_rect, "cursor": cursor_rect, "min": min_val, "max": max_val, "width": width, "x": x}
        return slider_rect.bottom + 20
    
    def draw_basic_settings(self):
        y_pos = 180
        self.current_engine = self.universal_settings.get_selected_engine()
        # Truncate engine name if too long for the centered area
        max_name_w = max(100, self.WIDTH - 300)
        engine_name = self.truncate_text(self.normal_font, self.current_engine, max_name_w)
        engine_text = self.normal_font.render(f"Current Engine: {engine_name}", True, self.TEXT_COLOR)
        self.screen.blit(engine_text, engine_text.get_rect(center=(self.WIDTH // 2, y_pos)))
        y_pos += 60

        current_elo = self.universal_settings.get_elo_for_engine()
        min_elo, max_elo = self.universal_settings.get_elo_range_for_engine()
        y_pos = self.draw_slider(100, y_pos, 400, "ELO Level (approximate):", current_elo, min_elo, max_elo, "elo")
        
        range_size = max_elo - min_elo
        q = range_size // 4
        descriptions = [
            (f"{min_elo}-{min_elo + q}: Beginner", 10),
            (f"{min_elo + q}-{min_elo + 2*q}: Intermediate", 30),
            (f"{min_elo + 2*q}-{min_elo + 3*q}: Advanced", 50),
            (f"{min_elo + 3*q}-{max_elo}: Expert/Master", 70)
        ]
        for desc, y_offset in descriptions:
            desc_surf = self.small_font.render(desc, True, self.SUBTEXT_COLOR)
            self.screen.blit(desc_surf, desc_surf.get_rect(center=(self.WIDTH // 2, y_pos + y_offset)))
    
    def draw_advanced_settings(self):
        y_pos = 180
        self.current_engine = self.universal_settings.get_selected_engine()
        engine_text = self.normal_font.render(f"Advanced Settings for: {self.current_engine}", True, self.TEXT_COLOR)
        self.screen.blit(engine_text, engine_text.get_rect(center=(self.WIDTH // 2, y_pos)))
        y_pos += 40

        current_settings = self.universal_settings.get_engine_settings()
        available_options = self.universal_settings.get_available_options()

        for option, config in available_options.items():
            current_value = current_settings.get(option, config["default"])
            y_pos = self.draw_slider(100, y_pos, 350, f"{config['description']}:", current_value, config["min"], config["max"], option)
    
    def draw_engines_info(self):
        y_pos = 180
        from engine_manager import EngineManager
        em = EngineManager()
        selected_engine = self.universal_settings.get_selected_engine()
        
        if selected_engine:
            engine_display = self.truncate_text(self.normal_font, selected_engine, max(80, self.WIDTH - 300))
            engine_text = self.normal_font.render(f"Current Engine: {engine_display}", True, self.TEXT_COLOR)
            self.screen.blit(engine_text, (100, y_pos))
            y_pos += 30
            
            if em.is_engine_installed(selected_engine):
                status_text = self.small_font.render("✓ Engine is installed and ready.", True, self.GREEN)
            else:
                status_text = self.small_font.render("✗ Engine executable not found.", True, self.RED)
            self.screen.blit(status_text, (100, y_pos))
        else:
            no_engine_text = self.normal_font.render("No engine selected.", True, self.RED)
            self.screen.blit(no_engine_text, (100, y_pos))
        y_pos += 60
        
        instructions = [
            "Use this section to verify your current engine.",
            "To download, select, or remove engines,",
            "click the 'Manage Engines' button below."
        ]
        for line in instructions:
            inst_text = self.small_font.render(line, True, self.SUBTEXT_COLOR)
            self.screen.blit(inst_text, inst_text.get_rect(center=(self.WIDTH // 2, y_pos)))
            y_pos += 25

    def draw_button(self, key, label, color):
        rect = self.buttons[key]
        pygame.draw.rect(self.screen, color, rect, border_radius=10)
        # Truncate label to fit inside button
        padding = 10
        max_w = rect.width - padding * 2
        label_to_draw = self.truncate_text(self.normal_font, label, max_w)
        text_surf = self.normal_font.render(label_to_draw, True, self.TEXT_COLOR)
        self.screen.blit(text_surf, text_surf.get_rect(center=rect.center))
    
    def draw(self):
        self.screen.fill(self.BG_COLOR)
        title_text = f"Settings: {self.current_engine}"
        title = self.title_font.render(title_text, True, self.TEXT_COLOR)
        self.screen.blit(title, title.get_rect(center=(self.WIDTH // 2, 50)))
        
        self.draw_button("basic", "Basic", self.ACTIVE_COLOR if self.mode == "basic" else self.INACTIVE_COLOR)
        self.draw_button("advanced", "Advanced", self.ACTIVE_COLOR if self.mode == "advanced" else self.INACTIVE_COLOR)
        self.draw_button("engines", "Engines", self.ACTIVE_COLOR if self.mode == "engines" else self.INACTIVE_COLOR)
        
        if self.mode == "basic": self.draw_basic_settings()
        elif self.mode == "advanced": self.draw_advanced_settings()
        elif self.mode == "engines": self.draw_engines_info()
        
        self.draw_button("save", "Save", self.GREEN)
        self.draw_button("cancel", "Cancel", self.RED)
        self.draw_button("reset", "Defaults", self.INACTIVE_COLOR)
        self.draw_button("engines_menu", "Manage Engines", self.ACTIVE_COLOR)
    
    def handle_click(self, pos):
        if self.buttons["basic"].collidepoint(pos): self.mode = "basic"; return None
        if self.buttons["advanced"].collidepoint(pos): self.mode = "advanced"; return None
        if self.buttons["engines"].collidepoint(pos): self.mode = "engines"; return None
        
        if self.buttons["save"].collidepoint(pos): self.universal_settings.save_settings(); return "save"
        if self.buttons["cancel"].collidepoint(pos): return "cancel"
        if self.buttons["reset"].collidepoint(pos): self.universal_settings.reset_engine_to_defaults(); return None
        if self.buttons["engines_menu"].collidepoint(pos): EngineMenu(self.screen).run(); return None
        
        for key, slider in self.sliders.items():
            if slider["rect"].union(slider["cursor"]).collidepoint(pos): self.dragging = key; return None
        return None
    
    def handle_drag(self, pos):
        if self.dragging and self.dragging in self.sliders:
            slider = self.sliders[self.dragging]
            x = max(slider["x"], min(pos[0], slider["x"] + slider["width"]))
            ratio = (x - slider["x"]) / slider["width"]
            new_value = slider["min"] + ratio * (slider["max"] - slider["min"])
            
            if self.dragging == "elo": self.universal_settings.set_elo_for_engine(int(new_value))
            else: self.universal_settings.set_engine_setting(self.dragging, int(round(new_value)))
    
    def run(self):
        clock, running = pygame.time.Clock(), True
        while running:
            for event in pygame.event.get():
                if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE): running = False
                elif event.type == MOUSEBUTTONDOWN and event.button == 1:
                    action = self.handle_click(event.pos)
                    if action in ["save", "cancel"]: running = False
                elif event.type == MOUSEMOTION and event.buttons[0]: self.handle_drag(event.pos)
                elif event.type == MOUSEBUTTONUP: self.dragging = None
            self.draw()
            pygame.display.flip()
            clock.tick(60)
        return "save" # Assume save on exit unless explicitly cancelled