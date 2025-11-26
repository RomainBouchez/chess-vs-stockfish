"""
Script de calibration des rampes d'accélération pour le robot d'échecs.
Optimise les paramètres de vitesse et accélération pour des mouvements rapides et précis.
"""

import serial
import serial.tools.list_ports
import time
import configparser
import os


class RampCalibrator:
    """Calibrateur de rampes d'accélération pour le robot d'échecs."""
    
    def __init__(self, config_file='robot_config.ini'):
        self.ser = None
        self.config = self.load_config(config_file)
        self.firmware = "MARLIN"  # Par défaut, peut être changé en "GRBL"
        
    def load_config(self, config_file):
        """Charge la configuration depuis robot_config.ini"""
        config = configparser.ConfigParser()
        
        if os.path.exists(config_file):
            config.read(config_file)
            print(f"[OK] Configuration chargée depuis {config_file}")
        else:
            print(f"[AVERTISSEMENT] {config_file} non trouvé - utilisation des valeurs par défaut")
            config['SERIAL'] = {
                'port': 'COM3',
                'baudrate': '250000',
                'timeout': '2'
            }
            config['SPEEDS'] = {
                'feed_rate_travel': '10000',
                'feed_rate_work': '1500'
            }
        
        return config
    
    def connect(self, port=None, baudrate=None):
        """Établit la connexion série."""
        port = port or self.config['SERIAL'].get('port', 'COM3')
        baudrate = baudrate or int(self.config['SERIAL'].get('baudrate', '115200'))
        timeout = float(self.config['SERIAL'].get('timeout', '2'))
        
        print(f"\n[CONNEXION] {port} @ {baudrate} bauds...")
        
        try:
            self.ser = serial.Serial(
                port=port,
                baudrate=baudrate,
                timeout=timeout
            )
            
            # Attendre l'initialisation du contrôleur
            time.sleep(2)
            
            # Vider le buffer
            self.flush_serial()
            
            # Lire le message de démarrage
            if self.ser.in_waiting:
                startup = self.ser.read(self.ser.in_waiting).decode(errors='ignore')
                print(f"[STARTUP] {startup[:100]}...")
            
            # Détecter le firmware
            self.detect_firmware()
            
            print("[OK] Connexion réussie ✓")
            return True
            
        except serial.SerialException as e:
            print(f"[ERREUR] Connexion impossible: {e}")
            return False
    
    def flush_serial(self):
        """Vide les buffers série."""
        if self.ser:
            self.ser.reset_input_buffer()
            self.ser.reset_output_buffer()
    
    def detect_firmware(self):
        """Détecte le type de firmware (GRBL ou Marlin)."""
        # Tester avec une commande GRBL
        response = self.send_gcode("$I", wait_response=True)
        
        if response and ("Grbl" in response or "grbl" in response):
            self.firmware = "GRBL"
            print("[INFO] Firmware détecté: GRBL")
        else:
            # Tester avec Marlin
            response = self.send_gcode("M115", wait_response=True)
            if response and "FIRMWARE" in response.upper():
                self.firmware = "MARLIN"
                print("[INFO] Firmware détecté: MARLIN")
            else:
                print("[INFO] Firmware non détecté, utilisation de MARLIN par défaut")
                self.firmware = "MARLIN"
    
    def send_gcode(self, cmd, wait_response=True):
        """
        Envoie une commande G-code et attend la réponse.
        Utilise decode(errors='ignore') pour éviter les erreurs UTF-8.
        """
        if not self.ser or not self.ser.is_open:
            print("[ERREUR] Pas de connexion active")
            return None
        
        try:
            # Envoyer la commande
            self.ser.write(f"{cmd}\n".encode())
            
            if not wait_response:
                return None
            
            # Attendre et lire la réponse
            time.sleep(0.1)
            response_lines = []
            timeout_count = 0
            
            while timeout_count < 10:  # Max 1 seconde d'attente
                if self.ser.in_waiting:
                    line = self.ser.readline().decode(errors='ignore').strip()
                    if line:
                        response_lines.append(line)
                        # Vérifier si on a reçu un OK ou une erreur
                        if 'ok' in line.lower() or 'error' in line.lower():
                            break
                    timeout_count = 0
                else:
                    time.sleep(0.1)
                    timeout_count += 1
            
            return '\n'.join(response_lines)
            
        except Exception as e:
            print(f"[ERREUR] Envoi commande: {e}")
            return None
    
    def get_current_settings(self):
        """Récupère les paramètres actuels du firmware."""
        print("\n" + "="*60)
        print("PARAMÈTRES ACTUELS")
        print("="*60)
        
        if self.firmware == "GRBL":
            response = self.send_gcode("$$")
            if response:
                print(response)
                return self.parse_grbl_settings(response)
        else:  # MARLIN
            response = self.send_gcode("M503")
            if response:
                print(response)
                return self.parse_marlin_settings(response)
        
        return {}
    
    def parse_grbl_settings(self, response):
        """Parse les paramètres GRBL."""
        settings = {}
        for line in response.split('\n'):
            if line.startswith('$'):
                try:
                    parts = line.split('=')
                    key = parts[0]
                    value = float(parts[1])
                    settings[key] = value
                except:
                    pass
        return settings
    
    def parse_marlin_settings(self, response):
        """Parse les paramètres Marlin."""
        settings = {}
        for line in response.split('\n'):
            line = line.strip()
            if line.startswith('M201'):  # Accélération max
                settings['accel'] = line
            elif line.startswith('M203'):  # Vitesse max
                settings['speed'] = line
            elif line.startswith('M204'):  # Accélération par défaut
                settings['default_accel'] = line
            elif line.startswith('M205'):  # Jerk/Junction
                settings['jerk'] = line
        return settings
    
    def set_acceleration(self, accel_x, accel_y=None):
        """Définit l'accélération."""
        accel_y = accel_y or accel_x
        
        if self.firmware == "GRBL":
            self.send_gcode(f"$120={accel_x}")
            self.send_gcode(f"$121={accel_y}")
        else:  # MARLIN
            self.send_gcode(f"M201 X{accel_x} Y{accel_y}")
        
        print(f"[SET] Accélération: X={accel_x} Y={accel_y} mm/s²")
    
    def set_max_speed(self, speed_x, speed_y=None):
        """Définit la vitesse maximale."""
        speed_y = speed_y or speed_x
        
        if self.firmware == "GRBL":
            self.send_gcode(f"$110={speed_x}")
            self.send_gcode(f"$111={speed_y}")
        else:  # MARLIN
            # Marlin utilise mm/s, convertir si nécessaire
            self.send_gcode(f"M203 X{speed_x} Y{speed_y}")
        
        print(f"[SET] Vitesse max: X={speed_x} Y={speed_y}")
    
    def set_jerk(self, jerk_x, jerk_y=None):
        """Définit le jerk (Marlin) ou junction deviation."""
        jerk_y = jerk_y or jerk_x
        
        if self.firmware == "GRBL":
            print("[INFO] GRBL n'a pas de paramètre jerk direct")
        else:  # MARLIN
            self.send_gcode(f"M205 X{jerk_x} Y{jerk_y}")
            print(f"[SET] Jerk: X={jerk_x} Y={jerk_y} mm/s")
    
    def save_settings(self):
        """Sauvegarde les paramètres en EEPROM."""
        if self.firmware == "GRBL":
            print("[INFO] GRBL sauvegarde automatiquement")
        else:  # MARLIN
            self.send_gcode("M500")
            print("[OK] Paramètres sauvegardés en EEPROM (M500)")
    
    def test_movement(self, distance=100, speed=None):
        """
        Teste un mouvement aller-retour.
        Retourne True si le mouvement semble correct.
        """
        speed = speed or int(self.config['SPEEDS'].get('feed_rate_travel', '5000'))
        
        print(f"\n[TEST] Mouvement {distance}mm @ F{speed}")
        
        # Position de départ
        self.send_gcode("G90")  # Mode absolu
        self.send_gcode("G0 X0 Y0")
        self.wait_idle()
        time.sleep(0.5)
        
        start_time = time.time()
        
        # Aller
        self.send_gcode(f"G0 X{distance} Y{distance} F{speed}")
        self.wait_idle()
        
        # Retour
        self.send_gcode("G0 X0 Y0")
        self.wait_idle()
        
        elapsed = time.time() - start_time
        
        # Calcul du temps théorique
        total_distance = distance * 2 * 1.414  # Diagonale aller-retour
        theoretical_time = (total_distance / speed) * 60  # speed en mm/min
        
        print(f"    Temps réel: {elapsed:.2f}s")
        print(f"    Temps théorique (sans accel): {theoretical_time:.2f}s")
        
        return elapsed, theoretical_time
    
    def wait_idle(self):
        """Attend que le mouvement soit terminé."""
        if self.firmware == "GRBL":
            for _ in range(100):  # Max 10 secondes
                response = self.send_gcode("?")
                if response and "Idle" in response:
                    break
                time.sleep(0.1)
        else:  # MARLIN
            self.send_gcode("M400")  # Attend fin des mouvements
    
    def find_optimal_acceleration(self, min_accel=100, max_accel=5000, step=200):
        """
        Recherche l'accélération optimale par tests successifs.
        """
        print("\n" + "="*60)
        print("RECHERCHE ACCÉLÉRATION OPTIMALE")
        print("="*60)
        
        results = []
        
        for accel in range(min_accel, max_accel + 1, step):
            print(f"\n--- Test accélération: {accel} mm/s² ---")
            
            self.set_acceleration(accel)
            time.sleep(0.3)
            
            try:
                elapsed, theoretical = self.test_movement(distance=50)
                efficiency = theoretical / elapsed * 100 if elapsed > 0 else 0
                
                results.append({
                    'accel': accel,
                    'time': elapsed,
                    'efficiency': efficiency
                })
                
                print(f"    Efficacité: {efficiency:.1f}%")
                
                # Si on entend des bruits anormaux ou perte de pas, s'arrêter
                cont = input("    Continuer? (o/n, défaut=o): ").strip().lower()
                if cont == 'n':
                    break
                    
            except Exception as e:
                print(f"    [ERREUR] {e}")
                break
        
        # Afficher les résultats
        print("\n" + "="*60)
        print("RÉSULTATS")
        print("="*60)
        
        if results:
            best = max(results, key=lambda x: x['efficiency'])
            print(f"\n✓ Meilleure accélération: {best['accel']} mm/s²")
            print(f"  (Efficacité: {best['efficiency']:.1f}%)")
            
            # Recommander 80% pour la sécurité
            safe_accel = int(best['accel'] * 0.8)
            print(f"\n✓ Valeur recommandée (marge 80%): {safe_accel} mm/s²")
            
            return safe_accel
        
        return min_accel
    
    def apply_preset(self, preset_name):
        """Applique un preset de configuration."""
        presets = {
            "safe": {
                "accel": 300,
                "speed": 3000,
                "jerk": 5,
                "desc": "Sûr et silencieux"
            },
            "balanced": {
                "accel": 1000,
                "speed": 8000,
                "jerk": 8,
                "desc": "Équilibré"
            },
            "fast": {
                "accel": 2000,
                "speed": 12000,
                "jerk": 10,
                "desc": "Rapide"
            },
            "aggressive": {
                "accel": 3000,
                "speed": 15000,
                "jerk": 15,
                "desc": "Agressif (risque de perte de pas)"
            }
        }
        
        if preset_name not in presets:
            print(f"[ERREUR] Preset inconnu: {preset_name}")
            print(f"Presets disponibles: {', '.join(presets.keys())}")
            return False
        
        preset = presets[preset_name]
        print(f"\n[PRESET] Application de '{preset_name}' - {preset['desc']}")
        
        self.set_acceleration(preset['accel'])
        self.set_max_speed(preset['speed'])
        self.set_jerk(preset['jerk'])
        
        return True
    
    def interactive_tuning(self):
        """Mode de réglage interactif."""
        print("\n" + "="*60)
        print("RÉGLAGE INTERACTIF DES RAMPES")
        print("="*60)
        print("""
Commandes disponibles:
  accel <valeur>    : Définir l'accélération (mm/s²)
  speed <valeur>    : Définir la vitesse max (mm/min)
  jerk <valeur>     : Définir le jerk (mm/s)
  test              : Tester un mouvement
  test <distance>   : Tester un mouvement de X mm
  preset <nom>      : Appliquer un preset (safe/balanced/fast/aggressive)
  show              : Afficher les paramètres actuels
  save              : Sauvegarder en EEPROM
  help              : Afficher cette aide
  quit              : Quitter
        """)
        
        while True:
            try:
                cmd = input("\nramps> ").strip().lower()
                
                if not cmd:
                    continue
                
                parts = cmd.split()
                action = parts[0]
                
                if action == 'quit':
                    break
                    
                elif action == 'help':
                    print("Voir aide ci-dessus")
                    
                elif action == 'accel' and len(parts) > 1:
                    self.set_acceleration(int(parts[1]))
                    
                elif action == 'speed' and len(parts) > 1:
                    self.set_max_speed(int(parts[1]))
                    
                elif action == 'jerk' and len(parts) > 1:
                    self.set_jerk(float(parts[1]))
                    
                elif action == 'test':
                    distance = int(parts[1]) if len(parts) > 1 else 50
                    self.test_movement(distance)
                    
                elif action == 'preset' and len(parts) > 1:
                    self.apply_preset(parts[1])
                    
                elif action == 'show':
                    self.get_current_settings()
                    
                elif action == 'save':
                    self.save_settings()
                    
                elif action == 'auto':
                    self.find_optimal_acceleration()
                    
                else:
                    # Envoyer comme commande G-code directe
                    response = self.send_gcode(cmd)
                    if response:
                        print(response)
                        
            except KeyboardInterrupt:
                print("\n[INFO] Interruption")
                break
            except ValueError as e:
                print(f"[ERREUR] Valeur invalide: {e}")
            except Exception as e:
                print(f"[ERREUR] {e}")
    
    def close(self):
        """Ferme la connexion série."""
        if self.ser and self.ser.is_open:
            self.ser.close()
            print("[INFO] Connexion fermée")


def main():
    """Point d'entrée principal."""
    print("="*60)
    print("CALIBRATION DES RAMPES D'ACCÉLÉRATION")
    print("="*60)
    print("""
Ce script vous aide à optimiser les paramètres de mouvement
pour des déplacements rapides ET précis.

Paramètres clés:
  - Accélération : Vitesse de montée en régime (mm/s²)
  - Vitesse max  : Vitesse de croisière (mm/min)
  - Jerk         : Changement instantané de vitesse (mm/s)
    """)
    
    calibrator = RampCalibrator()
    
    # Connexion
    if not calibrator.connect():
        print("\n[ERREUR] Impossible de se connecter")
        print("Vérifiez robot_config.ini ou les paramètres de connexion")
        return
    
    # Menu principal
    while True:
        print("\n" + "="*60)
        print("MENU")
        print("="*60)
        print("1. Afficher paramètres actuels")
        print("2. Appliquer un preset")
        print("3. Recherche automatique (accélération optimale)")
        print("4. Réglage interactif")
        print("5. Test de mouvement")
        print("6. Sauvegarder en EEPROM")
        print("7. Quitter")
        
        choice = input("\nVotre choix: ").strip()
        
        try:
            if choice == '1':
                calibrator.get_current_settings()
                
            elif choice == '2':
                print("\nPresets disponibles:")
                print("  safe       - Sûr et silencieux (300 mm/s²)")
                print("  balanced   - Équilibré (1000 mm/s²)")
                print("  fast       - Rapide (2000 mm/s²)")
                print("  aggressive - Agressif (3000 mm/s²)")
                preset = input("Choisir un preset: ").strip().lower()
                calibrator.apply_preset(preset)
                
            elif choice == '3':
                print("\nATTENTION: Ce test va effectuer plusieurs mouvements.")
                print("Assurez-vous que la zone est dégagée!")
                input("Appuyez sur Entrée pour continuer...")
                calibrator.find_optimal_acceleration()
                
            elif choice == '4':
                calibrator.interactive_tuning()
                
            elif choice == '5':
                distance = input("Distance de test (mm, défaut=50): ").strip()
                distance = int(distance) if distance else 50
                calibrator.test_movement(distance)
                
            elif choice == '6':
                calibrator.save_settings()
                
            elif choice == '7':
                break
                
        except KeyboardInterrupt:
            print("\n[INFO] Interruption")
        except Exception as e:
            print(f"[ERREUR] {e}")
    
    calibrator.close()
    print("\n[INFO] Programme terminé")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[INFO] Programme interrompu")
    except Exception as e:
        print(f"\n[ERREUR FATALE] {e}")
        import traceback
        traceback.print_exc()