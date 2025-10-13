import pygame
from pygame.locals import *
from settings import StockfishSettings
from universal_settings import UniversalEngineSettings
from engine_menu import EngineMenu

class SettingsMenu:
    """Interface graphique pour configurer Stockfish"""
    
    def __init__(self, screen):
        self.screen = screen
        self.settings = StockfishSettings()  # Garder pour compatibilité
        self.universal_settings = UniversalEngineSettings()
        self.mode = "basic"  # "basic" ou "advanced"
        self.current_engine = self.universal_settings.get_selected_engine()
        
        # Couleurs
        self.WHITE = (255, 255, 255)
        self.BLACK = (0, 0, 0)
        self.GRAY = (200, 200, 200)
        self.BLUE = (50, 100, 200)
        self.GREEN = (50, 200, 100)
        self.RED = (200, 50, 50)
        
        # Polices
        self.title_font = pygame.font.SysFont("comicsansms", 40)
        self.normal_font = pygame.font.SysFont("comicsansms", 20)
        self.small_font = pygame.font.SysFont("comicsansms", 16)
        
        # Sliders
        self.sliders = {}
        self.dragging = None
        
        # Boutons
        self.buttons = {}
        self.setup_buttons()
    
    def setup_buttons(self):
        """Initialise les boutons du menu"""
        self.buttons = {
            "basic": pygame.Rect(50, 100, 150, 40),
            "advanced": pygame.Rect(220, 100, 150, 40),
            "engines": pygame.Rect(390, 100, 150, 40),
            "save": pygame.Rect(50, 650, 120, 50),
            "cancel": pygame.Rect(180, 650, 120, 50),
            "reset": pygame.Rect(310, 650, 120, 50),
            "engines_menu": pygame.Rect(440, 650, 120, 50)
        }
    
    def draw_slider(self, x, y, width, label, value, min_val, max_val, key):
        """Dessine un slider horizontal"""
        # Label
        label_surf = self.small_font.render(label, True, self.BLACK)
        self.screen.blit(label_surf, (x, y))
        
        # Valeur actuelle
        value_text = str(int(value)) if isinstance(value, (int, float)) else str(value)
        value_surf = self.small_font.render(value_text, True, self.BLUE)
        self.screen.blit(value_surf, (x + width + 10, y))
        
        # Barre du slider
        slider_y = y + 25
        slider_rect = pygame.Rect(x, slider_y, width, 6)
        pygame.draw.rect(self.screen, self.GRAY, slider_rect)
        
        # Curseur
        if max_val > min_val:
            ratio = (value - min_val) / (max_val - min_val)
        else:
            ratio = 0
        cursor_x = x + int(ratio * width)
        cursor_rect = pygame.Rect(cursor_x - 5, slider_y - 7, 10, 20)
        pygame.draw.rect(self.screen, self.BLUE, cursor_rect)
        
        # Stocker pour la détection de clic
        self.sliders[key] = {
            "rect": slider_rect,
            "cursor": cursor_rect,
            "min": min_val,
            "max": max_val,
            "width": width,
            "x": x
        }
        
        return slider_rect.bottom + 15
    
    def draw_toggle(self, x, y, label, value, key):
        """Dessine un toggle on/off"""
        # Label
        label_surf = self.small_font.render(label, True, self.BLACK)
        self.screen.blit(label_surf, (x, y))
        
        # Toggle
        toggle_x = x + 300
        toggle_rect = pygame.Rect(toggle_x, y, 60, 25)
        
        # Couleur selon l'état
        color = self.GREEN if value else self.GRAY
        pygame.draw.rect(self.screen, color, toggle_rect, border_radius=12)
        
        # Cercle
        circle_x = toggle_x + 40 if value else toggle_x + 15
        pygame.draw.circle(self.screen, self.WHITE, (circle_x, y + 12), 10)
        
        # Texte
        text = "ON" if value else "OFF"
        text_surf = self.small_font.render(text, True, self.WHITE)
        self.screen.blit(text_surf, (toggle_x + 5, y + 5))
        
        self.sliders[key] = {"rect": toggle_rect, "toggle": True}
        
        return y + 35
    
    def draw_basic_settings(self):
        """Affiche les paramètres basiques (ELO uniquement)"""
        y_pos = 180

        # Actualiser le moteur actuel
        self.current_engine = self.universal_settings.get_selected_engine()

        # Afficher le moteur actuel
        engine_text = self.normal_font.render(f"Moteur actuel: {self.current_engine}", True, self.BLACK)
        self.screen.blit(engine_text, (100, y_pos))
        y_pos += 40

        # ELO slider avec plage dynamique
        current_elo = self.universal_settings.get_elo_for_engine()
        min_elo, max_elo = self.universal_settings.get_elo_range_for_engine()
        y_pos = self.draw_slider(
            100, y_pos, 400,
            f"Niveau ELO (approximatif):",
            current_elo, min_elo, max_elo, "elo"
        )
        
        # Descriptions des niveaux adaptées à la plage du moteur
        range_size = max_elo - min_elo
        quarter = range_size // 4

        descriptions = [
            (f"{min_elo}-{min_elo + quarter}: Débutant", 20),
            (f"{min_elo + quarter}-{min_elo + 2*quarter}: Intermédiaire", 40),
            (f"{min_elo + 2*quarter}-{min_elo + 3*quarter}: Avancé", 60),
            (f"{min_elo + 3*quarter}-{max_elo}: Expert/Maître", 80)
        ]

        for desc, y_offset in descriptions:
            desc_surf = self.small_font.render(desc, True, self.GRAY)
            self.screen.blit(desc_surf, (120, y_pos + y_offset))
    
    def draw_advanced_settings(self):
        """Affiche tous les paramètres avancés selon le moteur actuel"""
        y_pos = 180

        # Actualiser le moteur actuel
        self.current_engine = self.universal_settings.get_selected_engine()

        # Afficher le moteur actuel
        engine_text = self.normal_font.render(f"Moteur actuel: {self.current_engine}", True, self.BLACK)
        self.screen.blit(engine_text, (100, y_pos))
        y_pos += 30

        # Obtenir les paramètres et options disponibles
        current_settings = self.universal_settings.get_engine_settings()
        available_options = self.universal_settings.get_available_options()

        # Afficher les sliders selon les options disponibles
        for option, config in available_options.items():
            current_value = current_settings.get(option, config["default"])
            y_pos = self.draw_slider(
                100, y_pos, 350,
                f"{config['description']}:",
                current_value,
                config["min"], config["max"], option
            )
        
        # Note explicative
        note_y = y_pos + 20
        note_lines = [
            "Note: Certaines options dépendent de la version de Stockfish",
            "(MultiPV/Ponder gérés auto, Contempt retiré dans SF16+)"
        ]
        for i, line in enumerate(note_lines):
            note_text = self.small_font.render(line, True, self.GRAY)
            self.screen.blit(note_text, (100, note_y + i * 20))
    
    def draw_engines_info(self):
        """Affiche les informations sur les moteurs"""
        y_pos = 180
        
        try:
            # Lire le moteur sélectionné
            with open("selected_engine.txt", "r") as f:
                selected_engine = f.read().strip()
        except:
            selected_engine = None
        
        if selected_engine:
            # Afficher le moteur actuel
            engine_text = self.normal_font.render(f"Moteur actuel: {selected_engine}", True, self.BLACK)
            self.screen.blit(engine_text, (100, y_pos))
            y_pos += 40
            
            # Vérifier si le moteur existe
            from engine_manager import EngineManager
            engine_manager = EngineManager()
            engine_path = engine_manager.get_engine_path(selected_engine)
            
            if engine_path:
                status_text = self.small_font.render(f"Chemin: {engine_path}", True, self.GREEN)
                self.screen.blit(status_text, (100, y_pos))
                y_pos += 25
                
                # Test de fonctionnement
                if engine_manager.verify_engine(selected_engine):
                    verify_text = self.small_font.render("✓ Moteur opérationnel", True, self.GREEN)
                else:
                    verify_text = self.small_font.render("✗ Erreur de communication", True, self.RED)
                self.screen.blit(verify_text, (100, y_pos))
                y_pos += 40
            else:
                status_text = self.small_font.render("✗ Moteur non trouvé", True, self.RED)
                self.screen.blit(status_text, (100, y_pos))
                y_pos += 40
        else:
            no_engine_text = self.normal_font.render("Aucun moteur sélectionné", True, self.RED)
            self.screen.blit(no_engine_text, (100, y_pos))
            y_pos += 40
        
        # Instructions
        instructions = [
            "Pour gérer les moteurs (télécharger, installer, sélectionner):",
            "• Cliquez sur 'Gérer Moteurs' en bas de l'écran",
            "• Téléchargez les moteurs officiels disponibles",
            "• Sélectionnez le moteur à utiliser dans vos parties",
            "",
            "Moteurs supportés:",
            "• Stockfish (versions 15 et 16)",
            "• D'autres moteurs peuvent être ajoutés"
        ]
        
        for instruction in instructions:
            if instruction:
                inst_text = self.small_font.render(instruction, True, self.GRAY)
                self.screen.blit(inst_text, (100, y_pos))
            y_pos += 20
    
    def draw_button(self, key, label, color):
        """Dessine un bouton"""
        rect = self.buttons[key]
        pygame.draw.rect(self.screen, color, rect, border_radius=5)
        pygame.draw.rect(self.screen, self.BLACK, rect, 2, border_radius=5)
        
        text_surf = self.normal_font.render(label, True, self.WHITE)
        text_rect = text_surf.get_rect(center=rect.center)
        self.screen.blit(text_surf, text_rect)
    
    def draw(self):
        """Dessine le menu complet"""
        # Fond
        self.screen.fill(self.WHITE)
        
        # Titre adaptatif selon le moteur
        current_engine = self.universal_settings.get_selected_engine()
        title_text = f"Paramètres {current_engine}"
        title = self.title_font.render(title_text, True, self.BLACK)
        self.screen.blit(title, ((self.screen.get_width() - title.get_width()) // 2, 30))
        
        # Boutons de mode
        basic_color = self.BLUE if self.mode == "basic" else self.GRAY
        advanced_color = self.BLUE if self.mode == "advanced" else self.GRAY
        engines_color = self.BLUE if self.mode == "engines" else self.GRAY
        
        self.draw_button("basic", "Basique", basic_color)
        self.draw_button("advanced", "Avancé", advanced_color)
        self.draw_button("engines", "Moteurs", engines_color)
        
        # Paramètres selon le mode
        if self.mode == "basic":
            self.draw_basic_settings()
        elif self.mode == "advanced":
            self.draw_advanced_settings()
        elif self.mode == "engines":
            self.draw_engines_info()
        
        # Boutons d'action
        self.draw_button("save", "Sauvegarder", self.GREEN)
        self.draw_button("cancel", "Annuler", self.RED)
        self.draw_button("reset", "Défaut", self.GRAY)
        self.draw_button("engines_menu", "Gérer Moteurs", self.BLUE)
    
    def handle_click(self, pos):
        """Gère les clics de souris"""
        # Vérifier les boutons de mode
        if self.buttons["basic"].collidepoint(pos):
            self.mode = "basic"
            return None
        
        if self.buttons["advanced"].collidepoint(pos):
            self.mode = "advanced"
            return None
            
        if self.buttons["engines"].collidepoint(pos):
            self.mode = "engines"
            return None
        
        # Boutons d'action
        if self.buttons["save"].collidepoint(pos):
            # Sauvegarder les paramètres universels
            self.universal_settings.save_settings()
            # Aussi sauvegarder les anciens paramètres pour compatibilité
            self.settings.save_settings()
            return "save"

        if self.buttons["cancel"].collidepoint(pos):
            # Recharger les paramètres
            self.universal_settings = UniversalEngineSettings()
            self.settings.load_settings()
            return "cancel"

        if self.buttons["reset"].collidepoint(pos):
            # Reset pour le moteur actuel
            self.universal_settings.reset_engine_to_defaults()
            self.settings.reset_to_defaults()
            return None
            
        if self.buttons["engines_menu"].collidepoint(pos):
            # Ouvrir le menu de gestion des moteurs
            engine_menu = EngineMenu(self.screen)
            result = engine_menu.run()
            # Forcer la réactualisation de l'affichage après retour du menu moteurs
            return None
        
        # Vérifier les sliders
        for key, slider in self.sliders.items():
            if "toggle" in slider:
                # Toggle
                if slider["rect"].collidepoint(pos):
                    self.settings.settings[key] = not self.settings.settings[key]
                    return None
            else:
                # Slider normal
                if slider["cursor"].collidepoint(pos) or slider["rect"].collidepoint(pos):
                    self.dragging = key
                    return None
        
        return None
    
    def handle_drag(self, pos):
        """Gère le déplacement des sliders"""
        if self.dragging and self.dragging in self.sliders:
            slider = self.sliders[self.dragging]
            
            if "toggle" not in slider:
                # Calculer la nouvelle valeur
                x = max(slider["x"], min(pos[0], slider["x"] + slider["width"]))
                ratio = (x - slider["x"]) / slider["width"]
                
                min_val = slider["min"]
                max_val = slider["max"]
                
                new_value = min_val + ratio * (max_val - min_val)
                
                # Arrondir selon le type
                if self.dragging in ["skill_level", "threads", "hash", "depth_limit", 
                                    "move_overhead"]:
                    new_value = int(round(new_value))
                elif self.dragging in ["time_limit"]:
                    new_value = round(new_value, 1)
                
                # Gérer l'ELO (mode basique)
                if self.dragging == "elo":
                    self.universal_settings.set_elo_for_engine(int(new_value))
                    # Aussi mettre à jour l'ancien système pour compatibilité
                    self.settings.set_elo(int(new_value))
                else:
                    # Sauvegarder dans le système universel
                    self.universal_settings.set_engine_setting(self.dragging, new_value)
                    # Aussi dans l'ancien système si c'est un paramètre Stockfish
                    if hasattr(self.settings.settings, '__contains__') and self.dragging in self.settings.settings:
                        self.settings.settings[self.dragging] = new_value
    
    def handle_release(self):
        """Arrête le déplacement"""
        self.dragging = None
    
    def run(self):
        """Boucle principale du menu de paramètres"""
        clock = pygame.time.Clock()
        running = True
        result = None
        
        while running:
            clock.tick(60)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    result = "cancel"
                    running = False
                
                elif event.type == pygame.KEYDOWN:
                    if event.key == K_ESCAPE:
                        result = "cancel"
                        running = False
                
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Clic gauche
                        action = self.handle_click(event.pos)
                        if action in ["save", "cancel"]:
                            result = action
                            running = False
                
                elif event.type == pygame.MOUSEMOTION:
                    if pygame.mouse.get_pressed()[0]:  # Bouton gauche maintenu
                        self.handle_drag(event.pos)
                
                elif event.type == pygame.MOUSEBUTTONUP:
                    self.handle_release()
            
            self.draw()
            pygame.display.flip()
        
        return result