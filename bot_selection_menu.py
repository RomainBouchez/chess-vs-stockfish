import pygame
from pygame.locals import *
from universal_settings import UniversalEngineSettings
from bot_data import BOT_CATEGORIES
from settings_menu import SettingsMenu

class BotSelectionMenu:
    """Interface de sélection de bots style chess.com"""
    
    def __init__(self, screen):
        self.screen = screen
        self.universal_settings = UniversalEngineSettings()
        
        # Style
        self.WIDTH = self.screen.get_width()
        self.HEIGHT = self.screen.get_height()
        self.BG_COLOR = (20, 21, 22) # Dark grey almost black
        self.SIDEBAR_COLOR = (30, 30, 30)
        self.TEXT_COLOR = (240, 240, 240)
        self.SUBTEXT_COLOR = (160, 160, 160)
        self.HIGHLIGHT_COLOR = (50, 50, 50)
        self.SELECTED_COLOR = (60, 70, 60)
        self.GREEN_BTN = (129, 182, 76) # Chess.com green roughly
        self.HOVER_GREEN = (149, 202, 96)
        
        # Fonts
        self.title_font = pygame.font.SysFont("Segoe UI", 40, bold=True)
        try:
            self.header_font = pygame.font.SysFont("Segoe UI", 28, bold=True)
            self.name_font = pygame.font.SysFont("Segoe UI", 24, bold=True)
            self.desc_font = pygame.font.SysFont("Segoe UI", 18)
        except:
             self.header_font = pygame.font.Font(None, 36)
             self.name_font = pygame.font.Font(None, 32)
             self.desc_font = pygame.font.Font(None, 24)

        # State
        self.selected_category_index = 0
        self.selected_bot = None
        self.scroll_y = 0
        
        # Layout metrics
        self.sidebar_width = 250
        self.bot_list_x = self.sidebar_width + 40
        self.bot_list_w = self.WIDTH - self.sidebar_width - 80
        
        # Try to pre-select current bot if ELO matches
        self.match_current_bot()

    def match_current_bot(self):
        """Tries to find which bot matches the current engine ELO"""
        current_elo = self.universal_settings.get_elo_for_engine("stockfish_latest")
        # Default to first bot of first category
        if not self.selected_bot:
             self.selected_bot = BOT_CATEGORIES[0]["bots"][0]
             
        for cat in BOT_CATEGORIES:
            for bot in cat["bots"]:
                if bot["elo"] == current_elo:
                    self.selected_bot = bot
                    # Open that category
                    self.selected_category_index = BOT_CATEGORIES.index(cat)
                    return

    def get_avatar_rect(self, x, y):
        return pygame.Rect(x, y, 60, 60)

    def draw_sidebar(self):
        sidebar_rect = pygame.Rect(0, 0, self.sidebar_width, self.HEIGHT)
        pygame.draw.rect(self.screen, self.SIDEBAR_COLOR, sidebar_rect)
        
        # Title
        title_surf = self.title_font.render("Play Bots", True, self.TEXT_COLOR)
        self.screen.blit(title_surf, (20, 30))
        
        # Categories
        y = 100
        for i, cat in enumerate(BOT_CATEGORIES):
            rect = pygame.Rect(0, y, self.sidebar_width, 50)
            
            # Hover/Selection
            color = self.SUBTEXT_COLOR
            bg = self.SIDEBAR_COLOR
            if i == self.selected_category_index:
                bg = (45, 45, 45)
                color = self.TEXT_COLOR
                # Little indicator line
                pygame.draw.rect(self.screen, cat["color"], (0, y, 5, 50))
            
            pygame.draw.rect(self.screen, bg, rect)
            if i == self.selected_category_index:
                 pygame.draw.rect(self.screen, (255,255,255), rect, 1)
                 
            text = self.header_font.render(cat["name"], True, color)
            self.screen.blit(text, (30, y + 10))
            y += 50
    
    def draw_bot_list(self):
        cat = BOT_CATEGORIES[self.selected_category_index]
        y = 50
        
        # Category Title
        cat_title = self.title_font.render(cat["name"], True, cat["color"])
        self.screen.blit(cat_title, (self.bot_list_x, y))
        y += 60
        
        for bot in cat["bots"]:
            bot_rect = pygame.Rect(self.bot_list_x, y, self.bot_list_w, 80)
            is_selected = (self.selected_bot == bot)
            
            # Background
            bg_color = self.SELECTED_COLOR if is_selected else self.BG_COLOR
            pygame.draw.rect(self.screen, bg_color, bot_rect, border_radius=8)
            if is_selected:
                pygame.draw.rect(self.screen, cat["color"], bot_rect, 2, border_radius=8)
            
            # Avatar (Placeholder)
            avatar_rect = self.get_avatar_rect(self.bot_list_x + 10, y + 10)
            pygame.draw.rect(self.screen, cat["color"], avatar_rect, border_radius=8)
            # Add simple face or initials
            initials = bot["name"][:2].upper()
            init_surf = self.header_font.render(initials, True, (0,0,0))
            self.screen.blit(init_surf, init_surf.get_rect(center=avatar_rect.center))
            
            # Name & Elo
            name_surf = self.name_font.render(f"{bot['name']} ({bot['elo']})", True, self.TEXT_COLOR)
            self.screen.blit(name_surf, (self.bot_list_x + 85, y + 15))
            
            # Description
            desc_surf = self.desc_font.render(bot['description'], True, self.SUBTEXT_COLOR)
            self.screen.blit(desc_surf, (self.bot_list_x + 85, y + 45))
            
            y += 90

    def draw_footer(self):
        # Footer Bar
        footer_h = 100
        footer_y = self.HEIGHT - footer_h
        pygame.draw.rect(self.screen, self.SIDEBAR_COLOR, (0, footer_y, self.WIDTH, footer_h))
        
        # Play Button
        if self.selected_bot:
            btn_w = 300
            btn_h = 60
            btn_x = (self.WIDTH - btn_w) // 2
            btn_y = footer_y + 20
            self.play_btn_rect = pygame.Rect(btn_x, btn_y, btn_w, btn_h)
            
            mouse_pos = pygame.mouse.get_pos()
            color = self.HOVER_GREEN if self.play_btn_rect.collidepoint(mouse_pos) else self.GREEN_BTN
            
            pygame.draw.rect(self.screen, color, self.play_btn_rect, border_radius=10)
            # White highlight text
            label = f"New Game vs {self.selected_bot['name']}"
            txt = self.header_font.render(label, True, (255,255,255))
            self.screen.blit(txt, txt.get_rect(center=self.play_btn_rect.center))
            
        else:
            self.play_btn_rect = None
            
        # Advanced (Legacy) Settings Link
        adv_text = self.desc_font.render("Advanced Settings / Custom Engine", True, self.SUBTEXT_COLOR)
        self.adv_rect = adv_text.get_rect(bottomright=(self.WIDTH - 20, self.HEIGHT - 10))
        self.screen.blit(adv_text, self.adv_rect)

    def apply_bot_settings(self):
        if not self.selected_bot: return
        
        print(f"Applying bot settings: {self.selected_bot['name']} ({self.selected_bot['elo']})")
        # Set engine to stockfish just in case
        self.universal_settings.select_engine_by_name("Stockfish") # Helper might be needed
        
        # Set Elo (handles UCI LimitStrength logic via our previous fix)
        self.universal_settings.set_elo_for_engine(self.selected_bot["elo"], "stockfish_latest")
        
        # We could also set a "Bot Name" or "Persona" in settings if we wanted to display it in-game
        self.universal_settings.save_settings()

    def run(self):
        clock = pygame.time.Clock()
        run = True
        
        while run:
            self.screen.fill(self.BG_COLOR)
            
            self.draw_sidebar()
            self.draw_bot_list()
            self.draw_footer()
            
            for event in pygame.event.get():
                if event.type == QUIT:
                    return None
                    
                if event.type == MOUSEBUTTONDOWN:
                    if event.button == 1:
                        x, y = event.pos
                        
                        # Click on Sidebar Category
                        if x < self.sidebar_width:
                            cat_h = 50
                            if y > 100:
                                index = (y - 100) // cat_h
                                if 0 <= index < len(BOT_CATEGORIES):
                                    self.selected_category_index = index
                        
                        # Click on Bot List
                        if x > self.bot_list_x:
                            cat = BOT_CATEGORIES[self.selected_category_index]
                            list_y = 50 # Start y of list
                            # Check header skip
                            list_y += 60
                            # Each bot is 80h + 10 margin = 90
                            # Relative click y
                            rel_y = y - list_y
                            if rel_y > 0:
                                bot_idx = rel_y // 90
                                if 0 <= bot_idx < len(cat["bots"]):
                                    self.selected_bot = cat["bots"][bot_idx]
                        
                        # Play Button
                        if self.play_btn_rect and self.play_btn_rect.collidepoint((x,y)):
                            self.apply_bot_settings()
                            return "play"
                            
                        # Advanced Settings
                        if self.adv_rect.collidepoint((x,y)):
                            # Open old menu
                            SettingsMenu(self.screen).run()
                            # Refresh our state in case they changed something manually
                            self.match_current_bot()

            pygame.display.flip()
            clock.tick(30)
            
        return None
