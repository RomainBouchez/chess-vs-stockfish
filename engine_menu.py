import pygame
import threading
import time
from pygame.locals import *
from engine_manager import EngineManager

class EngineMenu:
    """Interface graphique pour gérer les moteurs d'échecs"""
    
    def __init__(self, screen):
        self.screen = screen
        self.engine_manager = EngineManager()
        
        # Couleurs
        self.WHITE = (255, 255, 255)
        self.BLACK = (0, 0, 0)
        self.GRAY = (200, 200, 200)
        self.LIGHT_GRAY = (240, 240, 240)
        self.BLUE = (50, 100, 200)
        self.GREEN = (50, 200, 100)
        self.RED = (200, 50, 50)
        self.ORANGE = (255, 165, 0)
        
        # Polices
        self.title_font = pygame.font.SysFont("comicsansms", 30)
        self.normal_font = pygame.font.SysFont("comicsansms", 18)
        self.small_font = pygame.font.SysFont("comicsansms", 14)
        
        # État du téléchargement
        self.downloading = False
        self.download_progress = 0
        self.download_engine = None
        self.download_error = None
        
        # Liste des moteurs
        self.available_engines = self.engine_manager.get_available_engines()
        self.installed_engines = self.engine_manager.get_installed_engines()
        
        # Défilement
        self.scroll_y = 0
        self.max_scroll = 0
        
        # Moteur sélectionné
        self.selected_engine = self.load_selected_engine()
        
    def load_selected_engine(self):
        """Charge le moteur actuellement sélectionné"""
        try:
            with open("selected_engine.txt", "r") as f:
                engine_id = f.read().strip()
                if self.engine_manager.is_engine_installed(engine_id):
                    return engine_id
        except:
            pass
        
        # Par défaut, prendre le premier moteur installé
        default = self.engine_manager.get_default_engine()
        if default:
            self.save_selected_engine(default)
        return default
        
    def save_selected_engine(self, engine_id):
        """Sauvegarde le moteur sélectionné"""
        try:
            with open("selected_engine.txt", "w") as f:
                f.write(engine_id)
            self.selected_engine = engine_id
        except Exception as e:
            print(f"Erreur lors de la sauvegarde du moteur sélectionné: {e}")
    
    def draw_engine_item(self, engine_id, engine_info, y_pos, is_installed=False):
        """Dessine un élément de moteur dans la liste"""
        # Rectangle de fond
        item_rect = pygame.Rect(50, y_pos, 540, 80)
        
        # Couleur selon l'état
        if is_installed:
            if engine_id == self.selected_engine:
                bg_color = (200, 255, 200)  # Vert clair pour sélectionné
            else:
                bg_color = (220, 220, 255)  # Bleu clair pour installé
        else:
            bg_color = self.LIGHT_GRAY
            
        pygame.draw.rect(self.screen, bg_color, item_rect)
        pygame.draw.rect(self.screen, self.BLACK, item_rect, 2)
        
        # Icône d'état
        status_x = 60
        if is_installed:
            if engine_id == self.selected_engine:
                pygame.draw.circle(self.screen, self.GREEN, (status_x, y_pos + 15), 8)
                status_text = "✓ ACTIF"
                status_color = self.GREEN
            else:
                pygame.draw.circle(self.screen, self.BLUE, (status_x, y_pos + 15), 8)
                status_text = "INSTALLÉ"
                status_color = self.BLUE
        else:
            pygame.draw.circle(self.screen, self.GRAY, (status_x, y_pos + 15), 8)
            status_text = "NON INSTALLÉ"
            status_color = self.GRAY
            
        # Nom du moteur
        name_text = self.normal_font.render(engine_info.get("name", engine_id), True, self.BLACK)
        self.screen.blit(name_text, (status_x + 20, y_pos + 5))
        
        # Version
        version_text = self.small_font.render(f"Version: {engine_info.get('version', 'N/A')}", True, self.GRAY)
        self.screen.blit(version_text, (status_x + 20, y_pos + 25))
        
        # Description
        description = engine_info.get("description", "")
        if description:
            desc_text = self.small_font.render(description, True, self.GRAY)
            self.screen.blit(desc_text, (status_x + 20, y_pos + 40))
        
        # Statut
        status_text_surf = self.small_font.render(status_text, True, status_color)
        self.screen.blit(status_text_surf, (status_x + 20, y_pos + 55))
        
        # Boutons d'action
        button_x = 450
        
        if is_installed:
            # Bouton Sélectionner/Désinstaller
            if engine_id != self.selected_engine:
                select_btn = pygame.Rect(button_x, y_pos + 10, 80, 25)
                pygame.draw.rect(self.screen, self.BLUE, select_btn)
                select_text = self.small_font.render("Sélectionner", True, self.WHITE)
                text_rect = select_text.get_rect(center=select_btn.center)
                self.screen.blit(select_text, text_rect)
                
            uninstall_btn = pygame.Rect(button_x, y_pos + 40, 80, 25)
            pygame.draw.rect(self.screen, self.RED, uninstall_btn)
            uninstall_text = self.small_font.render("Désinstaller", True, self.WHITE)
            text_rect = uninstall_text.get_rect(center=uninstall_btn.center)
            self.screen.blit(uninstall_text, text_rect)
            
        else:
            # Bouton Télécharger
            download_btn = pygame.Rect(button_x, y_pos + 25, 80, 30)
            btn_color = self.GRAY if self.downloading else self.GREEN
            pygame.draw.rect(self.screen, btn_color, download_btn)
            
            if self.downloading and self.download_engine == engine_id:
                btn_text = f"{int(self.download_progress)}%"
            else:
                btn_text = "Télécharger"
                
            download_text = self.small_font.render(btn_text, True, self.WHITE)
            text_rect = download_text.get_rect(center=download_btn.center)
            self.screen.blit(download_text, text_rect)
        
        return item_rect.bottom + 10
    
    def draw_header(self):
        """Dessine l'en-tête du menu"""
        # Titre
        title = self.title_font.render("Gestion des Moteurs d'Échecs", True, self.BLACK)
        self.screen.blit(title, ((self.screen.get_width() - title.get_width()) // 2, 20))
        
        # Moteur actuel
        if self.selected_engine:
            engine_info = self.installed_engines.get(self.selected_engine, {})
            current_text = f"Moteur actuel: {engine_info.get('name', self.selected_engine)}"
        else:
            current_text = "Aucun moteur sélectionné"
            
        current_surf = self.normal_font.render(current_text, True, self.BLUE)
        self.screen.blit(current_surf, (50, 60))
        
        # Message d'erreur
        if self.download_error:
            error_surf = self.normal_font.render(f"Erreur: {self.download_error}", True, self.RED)
            self.screen.blit(error_surf, (50, 80))
    
    def draw_engines_list(self):
        """Dessine la liste des moteurs"""
        y_pos = 120 - self.scroll_y
        
        # Section moteurs installés
        if self.installed_engines:
            section_title = self.normal_font.render("Moteurs Installés:", True, self.BLACK)
            self.screen.blit(section_title, (50, y_pos))
            y_pos += 30
            
            for engine_id, engine_info in self.installed_engines.items():
                if y_pos > -100 and y_pos < self.screen.get_height():
                    y_pos = self.draw_engine_item(engine_id, engine_info, y_pos, True)
                else:
                    y_pos += 90
            
            y_pos += 20
        
        # Section moteurs disponibles
        available_not_installed = {k: v for k, v in self.available_engines.items() 
                                 if k not in self.installed_engines}
        
        if available_not_installed:
            section_title = self.normal_font.render("Moteurs Disponibles:", True, self.BLACK)
            if y_pos > -30 and y_pos < self.screen.get_height():
                self.screen.blit(section_title, (50, y_pos))
            y_pos += 30
            
            for engine_id, engine_info in available_not_installed.items():
                if y_pos > -100 and y_pos < self.screen.get_height():
                    y_pos = self.draw_engine_item(engine_id, engine_info, y_pos, False)
                else:
                    y_pos += 90
        
        # Calculer le défilement max
        self.max_scroll = max(0, y_pos + self.scroll_y - self.screen.get_height() + 150)
    
    def draw_buttons(self):
        """Dessine les boutons de navigation"""
        # Bouton Retour
        back_btn = pygame.Rect(50, self.screen.get_height() - 60, 100, 40)
        pygame.draw.rect(self.screen, self.GRAY, back_btn)
        back_text = self.normal_font.render("Retour", True, self.WHITE)
        text_rect = back_text.get_rect(center=back_btn.center)
        self.screen.blit(back_text, text_rect)
        
        # Bouton Actualiser
        refresh_btn = pygame.Rect(self.screen.get_width() - 150, self.screen.get_height() - 60, 100, 40)
        pygame.draw.rect(self.screen, self.BLUE, refresh_btn)
        refresh_text = self.normal_font.render("Actualiser", True, self.WHITE)
        text_rect = refresh_text.get_rect(center=refresh_btn.center)
        self.screen.blit(refresh_text, text_rect)
    
    def draw(self):
        """Dessine le menu complet"""
        self.screen.fill(self.WHITE)
        self.draw_header()
        self.draw_engines_list()
        self.draw_buttons()
    
    def download_progress_callback(self, progress):
        """Callback pour le progrès du téléchargement"""
        self.download_progress = progress
    
    def download_engine_thread(self, engine_id):
        """Thread pour télécharger un moteur"""
        try:
            self.downloading = True
            self.download_engine = engine_id
            self.download_error = None
            self.download_progress = 0
            
            self.engine_manager.download_engine(engine_id, self.download_progress_callback)
            
            # Actualiser la liste des moteurs installés
            self.installed_engines = self.engine_manager.get_installed_engines()
            
            # Sélectionner automatiquement si c'est le premier moteur
            if not self.selected_engine:
                self.save_selected_engine(engine_id)
                
        except Exception as e:
            self.download_error = str(e)
        finally:
            self.downloading = False
            self.download_engine = None
            self.download_progress = 0
    
    def handle_click(self, pos):
        """Gère les clics de souris"""
        # Boutons de navigation
        back_btn = pygame.Rect(50, self.screen.get_height() - 60, 100, 40)
        refresh_btn = pygame.Rect(self.screen.get_width() - 150, self.screen.get_height() - 60, 100, 40)
        
        if back_btn.collidepoint(pos):
            return "back"
        
        if refresh_btn.collidepoint(pos):
            self.installed_engines = self.engine_manager.get_installed_engines()
            self.available_engines = self.engine_manager.get_available_engines()
            return None
        
        # Clics sur les moteurs
        y_pos = 120 - self.scroll_y
        
        # Moteurs installés
        if self.installed_engines:
            y_pos += 30
            for engine_id, engine_info in self.installed_engines.items():
                item_rect = pygame.Rect(50, y_pos, 540, 80)
                
                if item_rect.collidepoint(pos):
                    # Vérifier les boutons dans l'item
                    button_x = 450
                    
                    if engine_id != self.selected_engine:
                        select_btn = pygame.Rect(button_x, y_pos + 10, 80, 25)
                        if select_btn.collidepoint(pos):
                            self.save_selected_engine(engine_id)
                            return None
                    
                    uninstall_btn = pygame.Rect(button_x, y_pos + 40, 80, 25)
                    if uninstall_btn.collidepoint(pos):
                        try:
                            if engine_id == self.selected_engine:
                                # Choisir un autre moteur par défaut
                                remaining = [k for k in self.installed_engines.keys() if k != engine_id]
                                if remaining:
                                    self.save_selected_engine(remaining[0])
                                else:
                                    self.selected_engine = None
                                    try:
                                        import os
                                        os.remove("selected_engine.txt")
                                    except:
                                        pass
                            
                            self.engine_manager.uninstall_engine(engine_id)
                            self.installed_engines = self.engine_manager.get_installed_engines()
                        except Exception as e:
                            self.download_error = f"Erreur désinstallation: {e}"
                        return None
                
                y_pos += 90
            y_pos += 20
        
        # Moteurs disponibles
        available_not_installed = {k: v for k, v in self.available_engines.items() 
                                 if k not in self.installed_engines}
        
        if available_not_installed:
            y_pos += 30
            for engine_id, engine_info in available_not_installed.items():
                item_rect = pygame.Rect(50, y_pos, 540, 80)
                
                if item_rect.collidepoint(pos) and not self.downloading:
                    button_x = 450
                    download_btn = pygame.Rect(button_x, y_pos + 25, 80, 30)
                    
                    if download_btn.collidepoint(pos):
                        # Démarrer le téléchargement dans un thread
                        thread = threading.Thread(target=self.download_engine_thread, args=(engine_id,))
                        thread.daemon = True
                        thread.start()
                        return None
                
                y_pos += 90
        
        return None
    
    def handle_scroll(self, direction):
        """Gère le défilement"""
        scroll_speed = 30
        if direction > 0:  # Scroll up
            self.scroll_y = max(0, self.scroll_y - scroll_speed)
        else:  # Scroll down
            self.scroll_y = min(self.max_scroll, self.scroll_y + scroll_speed)
    
    def run(self):
        """Boucle principale du menu des moteurs"""
        clock = pygame.time.Clock()
        running = True
        result = None
        
        while running:
            clock.tick(60)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    result = "back"
                    running = False
                
                elif event.type == pygame.KEYDOWN:
                    if event.key == K_ESCAPE:
                        result = "back"
                        running = False
                
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Clic gauche
                        action = self.handle_click(event.pos)
                        if action == "back":
                            result = action
                            running = False
                    elif event.button == 4:  # Molette haut
                        self.handle_scroll(1)
                    elif event.button == 5:  # Molette bas
                        self.handle_scroll(-1)
            
            self.draw()
            pygame.display.flip()
        
        return result