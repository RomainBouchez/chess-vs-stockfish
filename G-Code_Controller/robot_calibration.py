"""
Script de test et calibration pour le robot d'échecs.
Utilisez ce script pour vérifier et ajuster votre configuration.
"""

import serial
import serial.tools.list_ports
import time
import configparser
import os

class RobotCalibration:
    """Outil de calibration et test du robot d'échecs."""
    
    def __init__(self):
        self.serial_conn = None
        self.config = self.load_config()
    
    def load_config(self):
        """Charge la configuration depuis robot_config.ini"""
        config = configparser.ConfigParser()
        
        if os.path.exists('robot_config.ini'):
            config.read('robot_config.ini')
            print("[OK] Configuration chargée depuis robot_config.ini")
        else:
            print("[AVERTISSEMENT] robot_config.ini non trouvé - utilisation des valeurs par défaut")
            # Valeurs par défaut
            config['SERIAL'] = {
                'port': 'COM3',
                'baudrate': '250000',
                'timeout': '2'
            }
            config['BOARD'] = {
                'square_size': '50.0',
                'board_offset_x': '20.0',
                'board_offset_y': '20.0'
            }
            config['HEIGHTS'] = {
                'z_safe': '50.0',
                'z_grab': '5.0',
                'z_lift': '30.0'
            }
        
        return config
    
    def list_serial_ports(self):
        """Liste tous les ports série disponibles."""
        print("\n" + "="*60)
        print("PORTS SÉRIE DISPONIBLES")
        print("="*60)
        
        ports = serial.tools.list_ports.comports()
        
        if not ports:
            print("Aucun port série détecté!")
            return []
        
        for i, port in enumerate(ports, 1):
            print(f"\n{i}. {port.device}")
            print(f"   Description: {port.description}")
            print(f"   Fabricant: {port.manufacturer or 'Inconnu'}")
            if port.hwid:
                print(f"   ID Matériel: {port.hwid}")
        
        return [port.device for port in ports]
    
    def test_connection(self, port, baudrate):
        """Teste la connexion à un port série."""
        print(f"\n[TEST] Connexion à {port} @ {baudrate} bauds...")
        
        try:
            self.serial_conn = serial.Serial(
                port=port,
                baudrate=baudrate,
                timeout=2
            )
            
            time.sleep(2)  # Attendre la réinitialisation
            
            # Lire le message de démarrage
            if self.serial_conn.in_waiting:
                # Ligne corrigée
                startup = self.serial_conn.read_until(b'\n').decode(errors='ignore').strip()
                print(f"[OK] Réponse: {startup}")
            
            # Tester une commande simple
            self.send_test_command("G21")  # Mode millimètres
            time.sleep(0.5)
            self.send_test_command("G90")  # Positionnement absolu
            
            print("[OK] Connexion réussie ✓")
            return True
            
        except serial.SerialException as e:
            print(f"[ERREUR] Connexion impossible: {e}")
            return False
        except Exception as e:
            print(f"[ERREUR] Erreur inattendue: {e}")
            return False
    
    def send_test_command(self, command):
        """Envoie une commande de test."""
        if not self.serial_conn or not self.serial_conn.is_open:
            print("[ERREUR] Pas de connexion active")
            return False
        
        try:
            self.serial_conn.write(f"{command}\n".encode())
            print(f">>> {command}")
            
            # Lire la réponse
            time.sleep(0.2)
            while self.serial_conn.in_waiting:
                # Ligne corrigée
                response = self.serial_conn.readline().decode(errors='ignore').strip()
                if response:
                    print(f"<<< {response}")
            
            return True
            
        except Exception as e:
            print(f"[ERREUR] Envoi commande: {e}")
            return False
    
    def test_movement(self):
        """Teste les mouvements de base."""
        print("\n" + "="*60)
        print("TEST DES MOUVEMENTS")
        print("="*60)
        
        square_size = float(self.config['BOARD']['square_size'])
        offset_x = float(self.config['BOARD']['board_offset_x'])
        offset_y = float(self.config['BOARD']['board_offset_y'])
        z_safe = float(self.config['HEIGHTS']['z_safe'])
        
        # Convention: X = rang (1-8), Y = colonne (a-h)
        tests = [
            ("Position d'origine", f"G0 X0 Y0 Z{z_safe}"),
            ("Case a1 (coin bas-gauche)", f"G0 X{offset_x} Y{offset_y} Z{z_safe}"),
            ("Case h1 (coin bas-droite)", f"G0 X{offset_x} Y{offset_y + 7*square_size} Z{z_safe}"),
            ("Case a8 (coin haut-gauche)", f"G0 X{offset_x + 7*square_size} Y{offset_y} Z{z_safe}"),
            ("Case h8 (coin haut-droite)", f"G0 X{offset_x + 7*square_size} Y{offset_y + 7*square_size} Z{z_safe}"),
            ("Centre (e4)", f"G0 X{offset_x + 3*square_size} Y{offset_y + 4*square_size} Z{z_safe}"),
            ("Retour origine", f"G0 X0 Y0 Z{z_safe}")
        ]
        
        for description, command in tests:
            print(f"\n[TEST] {description}")
            print(f"Commande: {command}")
            
            input("Appuyez sur Entrée pour exécuter (ou Ctrl+C pour arrêter)...")
            self.send_test_command(command)
            time.sleep(1)
    
    def test_gripper(self):
        """Teste le système de préhension."""
        print("\n" + "="*60)
        print("TEST DU SYSTÈME DE PRÉHENSION")
        print("="*60)
        
        grab_cmd = self.config['GRIPPER'].get('grab_command', 'M3 S1000')
        release_cmd = self.config['GRIPPER'].get('release_command', 'M5')
        
        print(f"\nCommande d'activation: {grab_cmd}")
        print(f"Commande de relâchement: {release_cmd}")
        
        input("\nAppuyez sur Entrée pour activer la préhension...")
        self.send_test_command(grab_cmd)
        time.sleep(1)
        
        input("Appuyez sur Entrée pour relâcher...")
        self.send_test_command(release_cmd)
    
    def calibrate_board_corners(self):
        """Aide à calibrer les coins du plateau."""
        print("\n" + "="*60)
        print("CALIBRATION DES COINS DU PLATEAU")
        print("="*60)
        print("\nCe test va vous aider à trouver les bonnes coordonnées")
        print("pour les 4 coins du plateau d'échecs.\n")
        
        corners = {
            'a1': {'name': 'Coin bas-gauche (a1)', 'x': 0, 'y': 0},
            'h1': {'name': 'Coin bas-droite (h1)', 'x': 0, 'y': 0},
            'a8': {'name': 'Coin haut-gauche (a8)', 'x': 0, 'y': 0},
            'h8': {'name': 'Coin haut-droite (h8)', 'x': 0, 'y': 0}
        }
        
        z_safe = float(self.config['HEIGHTS']['z_safe'])
        
        for corner, data in corners.items():
            print(f"\n--- {data['name']} ---")
            print("Déplacez le robot au-dessus du centre de cette case")
            print("Utilisez les commandes suivantes:")
            print("  - G0 X<valeur> Y<valeur>  : Déplacement")
            print("  - +X, -X, +Y, -Y         : Ajustements de 1mm")
            print("  - ok                     : Valider cette position")
            
            current_x, current_y = 0.0, 0.0
            
            while True:
                cmd = input(f"\n{corner}> ").strip()
                
                if cmd == 'ok':
                    data['x'] = current_x
                    data['y'] = current_y
                    print(f"[OK] Position {corner} enregistrée: X={current_x} Y={current_y}")
                    break
                elif cmd.startswith('G0 '):
                    self.send_test_command(cmd)
                    # Parser les coordonnées
                    try:
                        parts = cmd.split()
                        for part in parts[1:]:
                            if part.startswith('X'):
                                current_x = float(part[1:])
                            elif part.startswith('Y'):
                                current_y = float(part[1:])
                    except:
                        pass
                elif cmd == '+X':
                    current_x += 1
                    self.send_test_command(f"G0 X{current_x}")
                elif cmd == '-X':
                    current_x -= 1
                    self.send_test_command(f"G0 X{current_x}")
                elif cmd == '+Y':
                    current_y += 1
                    self.send_test_command(f"G0 Y{current_y}")
                elif cmd == '-Y':
                    current_y -= 1
                    self.send_test_command(f"G0 Y{current_y}")
                else:
                    self.send_test_command(cmd)
        
        # Calculer les paramètres
        print("\n" + "="*60)
        print("RÉSULTATS DE LA CALIBRATION")
        print("="*60)
        
        offset_x = corners['a1']['x']
        offset_y = corners['a1']['y']

        # IMPORTANT: Convention des axes du robot:
        # - Axe X va de a1 à a8 (verticalement sur le plateau)
        # - Axe Y va de a1 à h1 (horizontalement sur le plateau)
        width_x = corners['a8']['x'] - corners['a1']['x']  # Distance X entre a1 et a8
        width_y = corners['h1']['y'] - corners['a1']['y']  # Distance Y entre a1 et h1

        square_size_x = width_x / 7  # 7 cases de a1 à a8 (axe X)
        square_size_y = width_y / 7  # 7 cases de a1 à h1 (axe Y)
        square_size_avg = (square_size_x + square_size_y) / 2

        print(f"\nboard_offset_x = {offset_x}")
        print(f"board_offset_y = {offset_y}")
        print(f"square_size = {square_size_avg:.2f}")
        print(f"\nDistance X (a1→a8): {width_x:.2f} mm")
        print(f"Distance Y (a1→h1): {width_y:.2f} mm")
        
        # Proposer de sauvegarder
        save = input("\nSauvegarder dans robot_config.ini? (o/n): ")
        if save.lower() == 'o':
            self.config['BOARD']['board_offset_x'] = str(offset_x)
            self.config['BOARD']['board_offset_y'] = str(offset_y)
            self.config['BOARD']['square_size'] = str(square_size_avg)
            
            with open('robot_config.ini', 'w') as f:
                self.config.write(f)
            
            print("[OK] Configuration sauvegardée!")
    
    def interactive_mode(self):
        """Mode interactif pour envoyer des commandes G-code."""
        print("\n" + "="*60)
        print("MODE INTERACTIF")
        print("="*60)
        print("\nEntrez des commandes G-code directement")
        print("Commandes spéciales:")
        print("  - help  : Afficher l'aide G-code")
        print("  - quit  : Quitter")
        print()
        
        while True:
            try:
                cmd = input("G-code> ").strip()
                
                if cmd.lower() == 'quit':
                    break
                elif cmd.lower() == 'help':
                    self.show_gcode_help()
                elif cmd:
                    self.send_test_command(cmd)
                    
            except KeyboardInterrupt:
                print("\n[INFO] Interruption détectée")
                break
    
    def show_gcode_help(self):
        """Affiche l'aide G-code."""
        print("\n" + "="*60)
        print("COMMANDES G-CODE COURANTES")
        print("="*60)
        print("""
MOUVEMENTS:
  G0 X<x> Y<y> Z<z>  : Déplacement rapide
  G1 X<x> Y<y> Z<z>  : Déplacement linéaire
  G28                : Retour à l'origine (homing)
  G90                : Mode absolu
  G91                : Mode relatif

BROCHE/PRÉHENSION:
  M3 S<speed>        : Activer broche (électro-aimant)
  M5                 : Arrêter broche
  M280 P<pin> S<angle> : Contrôler servo
  
VITESSE:
  F<speed>           : Définir vitesse (mm/min)
  
SYSTÈME:
  G21                : Mode millimètres
  G20                : Mode pouces
  M114               : Obtenir position actuelle
  M503               : Voir configuration
        """)
    
    def close(self):
        """Ferme la connexion série."""
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
            print("[INFO] Connexion fermée")


def main():
    """Menu principal du programme de calibration."""
    
    print("="*60)
    print("OUTIL DE CALIBRATION ROBOT D'ÉCHECS")
    print("="*60)
    
    calibrator = RobotCalibration()
    
    # Étape 1: Sélection du port
    print("\n[ÉTAPE 1] Sélection du port série")
    ports = calibrator.list_serial_ports()
    
    if not ports:
        print("\n[ERREUR] Aucun port série détecté!")
        print("Vérifiez que:")
        print("  - Votre robot est branché via USB")
        print("  - Les drivers sont installés (CH340, FTDI, etc.)")
        return
    
    port_choice = input(f"\nChoisir un port (1-{len(ports)}) ou taper directement (ex: COM3): ")
    
    try:
        if port_choice.isdigit():
            port = ports[int(port_choice) - 1]
        else:
            port = port_choice
    except (ValueError, IndexError):
        print("[ERREUR] Choix invalide")
        return
    
    # Étape 2: Baudrate
    print("\n[ÉTAPE 2] Vitesse de communication")
    print("Vitesses courantes: 9600, 57600, 115200, 250000")
    baudrate_input = input("Baudrate (défaut: 250000): ").strip() or "250000"
    
    try:
        baudrate = int(baudrate_input)
    except ValueError:
        print("[ERREUR] Baudrate invalide")
        return
    
    # Étape 3: Test de connexion
    print("\n[ÉTAPE 3] Test de connexion")
    if not calibrator.test_connection(port, baudrate):
        print("\n[ERREUR] Impossible de se connecter")
        print("Vérifiez:")
        print("  - Le port série")
        print("  - Le baudrate")
        print("  - Que le robot n'est pas utilisé par un autre programme")
        return
    
    # Menu principal
    while True:
        print("\n" + "="*60)
        print("MENU PRINCIPAL")
        print("="*60)
        print("1. Test des mouvements de base")
        print("2. Test du système de préhension")
        print("3. Calibration des coins du plateau")
        print("4. Mode interactif (commandes G-code)")
        print("5. Afficher la configuration actuelle")
        print("6. Tester un coup d'échecs complet")
        print("7. Quitter")
        
        choice = input("\nVotre choix: ").strip()
        
        try:
            if choice == '1':
                calibrator.test_movement()
            elif choice == '2':
                calibrator.test_gripper()
            elif choice == '3':
                calibrator.calibrate_board_corners()
            elif choice == '4':
                calibrator.interactive_mode()
            elif choice == '5':
                print("\n" + "="*60)
                print("CONFIGURATION ACTUELLE")
                print("="*60)
                for section in calibrator.config.sections():
                    print(f"\n[{section}]")
                    for key, value in calibrator.config[section].items():
                        print(f"  {key} = {value}")
            elif choice == '6':
                test_chess_move(calibrator)
            elif choice == '7':
                print("\n[INFO] Fermeture...")
                break
            else:
                print("[ERREUR] Choix invalide")
                
        except KeyboardInterrupt:
            print("\n[INFO] Interruption détectée")
            break
        except Exception as e:
            print(f"[ERREUR] {e}")
    
    calibrator.close()
    print("\n[INFO] Programme terminé")


def test_chess_move(calibrator):
    """Teste un mouvement d'échecs complet."""
    print("\n" + "="*60)
    print("TEST D'UN COUP D'ÉCHECS COMPLET")
    print("="*60)
    
    move = input("\nEntrez un coup UCI (ex: e2e4): ").strip().lower()
    
    if len(move) < 4:
        print("[ERREUR] Format invalide")
        return
    
    from_square = move[:2]
    to_square = move[2:4]
    
    # Convertir en coordonnées
    square_size = float(calibrator.config['BOARD']['square_size'])
    offset_x = float(calibrator.config['BOARD']['board_offset_x'])
    offset_y = float(calibrator.config['BOARD']['board_offset_y'])
    
    def square_to_coords(square):
        file = ord(square[0]) - ord('a')  # 0-7 pour a-h
        rank = int(square[1]) - 1          # 0-7 pour 1-8
        # Convention: X = rang (1-8), Y = colonne (a-h)
        x = offset_x + (rank * square_size) + (square_size / 2)
        y = offset_y + (file * square_size) + (square_size / 2)
        return x, y
    
    from_x, from_y = square_to_coords(from_square)
    to_x, to_y = square_to_coords(to_square)
    
    z_safe = float(calibrator.config['HEIGHTS']['z_safe'])
    z_grab = float(calibrator.config['HEIGHTS']['z_grab'])
    z_lift = float(calibrator.config['HEIGHTS']['z_lift'])
    
    grab_cmd = calibrator.config['GRIPPER'].get('grab_command', 'M3 S1000')
    release_cmd = calibrator.config['GRIPPER'].get('release_command', 'M5')
    
    print(f"\nDéplacement: {from_square} ({from_x:.1f}, {from_y:.1f}) → {to_square} ({to_x:.1f}, {to_y:.1f})")
    input("Appuyez sur Entrée pour commencer...")
    
    # Séquence de mouvement
    steps = [
        (f"Aller au-dessus de {from_square}", f"G0 X{from_x:.2f} Y{from_y:.2f} Z{z_safe}"),
        ("Descendre", f"G0 Z{z_grab}"),
        ("Attraper la pièce", grab_cmd),
        ("Lever", f"G0 Z{z_lift}"),
        (f"Se déplacer vers {to_square}", f"G0 X{to_x:.2f} Y{to_y:.2f} Z{z_lift}"),
        ("Descendre", f"G0 Z{z_grab}"),
        ("Relâcher la pièce", release_cmd),
        ("Remonter", f"G0 Z{z_safe}"),
    ]
    
    for i, (description, command) in enumerate(steps, 1):
        print(f"\n[{i}/{len(steps)}] {description}")
        print(f"Commande: {command}")
        input("Entrée pour continuer...")
        calibrator.send_test_command(command)
        time.sleep(0.5)
    
    print("\n[OK] Test terminé!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[INFO] Programme interrompu par l'utilisateur")
    except Exception as e:
        print(f"\n[ERREUR FATALE] {e}")
        import traceback
        traceback.print_exc()