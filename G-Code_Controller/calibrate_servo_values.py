"""
Script de calibration pour trouver les bonnes valeurs M280 pour votre servo
Teste différentes valeurs d'angle pour déterminer UP et DOWN
"""

import serial
import time

def calibrate_servo(port='COM3', baudrate=115200):
    """
    Calibre le servo en testant différentes valeurs d'angle
    """
    print("="*70)
    print("CALIBRATION DU SERVO MOTEUR Z")
    print("="*70)
    print("\nCe script va tester différentes positions du servo.")
    print("Notez les valeurs qui correspondent à vos positions UP et DOWN.\n")

    try:
        # Connexion
        print(f"Connexion au port {port}...")
        ser = serial.Serial(port=port, baudrate=baudrate, timeout=2)
        time.sleep(2)

        # Vider le buffer
        ser.read_all()

        print("[OK] Connecté\n")

        # Positions standard pour servos
        test_positions = [
            (0, "Position minimale (0°)"),
            (30, "Position basse (30°)"),
            (60, "Position mi-basse (60°)"),
            (90, "Position milieu (90°)"),
            (120, "Position mi-haute (120°)"),
            (150, "Position haute (150°)"),
            (180, "Position maximale (180°)")
        ]

        print("="*70)
        print("PHASE 1 : RECHERCHE DE LA POSITION HAUTE (UP)")
        print("="*70)
        print("\nNous allons tester différentes positions.")
        print("Notez la position où le servo est LEVÉ (position de sécurité).\n")

        up_value = None

        for angle, description in test_positions:
            print(f"\n[TEST] {description}")
            cmd = f"M280 P0 S{angle}\n"
            print(f"Commande: {cmd.strip()}")

            ser.write(cmd.encode())
            time.sleep(1.5)  # Laisser le servo bouger

            # Lire la réponse
            response = ser.read_all().decode(errors='ignore').strip()
            if response:
                print(f"[ROBOT] {response}")

            answer = input("Est-ce la position HAUTE/LEVÉE que vous voulez? (o/n): ").lower()
            if answer == 'o':
                up_value = angle
                print(f"\n✓ Position UP enregistrée: S{angle}")
                break

        if up_value is None:
            print("\n[ATTENTION] Aucune position UP trouvée dans les valeurs standards.")
            custom = input("Voulez-vous tester une valeur personnalisée? (o/n): ").lower()
            if custom == 'o':
                up_value = int(input("Entrez la valeur S pour UP (0-180): "))
                cmd = f"M280 P0 S{up_value}\n"
                ser.write(cmd.encode())
                time.sleep(1.5)

        print("\n" + "="*70)
        print("PHASE 2 : RECHERCHE DE LA POSITION BASSE (DOWN)")
        print("="*70)
        print("\nMaintenant, trouvons la position où le servo est BAISSÉ (préhension).\n")

        down_value = None

        for angle, description in test_positions:
            if angle == up_value:
                continue  # Sauter la valeur UP déjà trouvée

            print(f"\n[TEST] {description}")
            cmd = f"M280 P0 S{angle}\n"
            print(f"Commande: {cmd.strip()}")

            ser.write(cmd.encode())
            time.sleep(1.5)

            response = ser.read_all().decode(errors='ignore').strip()
            if response:
                print(f"[ROBOT] {response}")

            answer = input("Est-ce la position BASSE/DESCENDUE que vous voulez? (o/n): ").lower()
            if answer == 'o':
                down_value = angle
                print(f"\n✓ Position DOWN enregistrée: S{angle}")
                break

        if down_value is None:
            print("\n[ATTENTION] Aucune position DOWN trouvée dans les valeurs standards.")
            custom = input("Voulez-vous tester une valeur personnalisée? (o/n): ").lower()
            if custom == 'o':
                down_value = int(input("Entrez la valeur S pour DOWN (0-180): "))
                cmd = f"M280 P0 S{down_value}\n"
                ser.write(cmd.encode())
                time.sleep(1.5)

        # Résumé
        print("\n" + "="*70)
        print("CALIBRATION TERMINÉE")
        print("="*70)

        if up_value is not None and down_value is not None:
            print(f"\n✓ Position UP (levée)   : S{up_value}")
            print(f"✓ Position DOWN (baissée): S{down_value}")

            print(f"\n{'─'*70}")
            print("CONFIGURATION À METTRE DANS robot_config.ini :")
            print(f"{'─'*70}")
            print(f"""
[Z_AXIS]
z_up_command = M280 P0 S{up_value}
z_down_command = M280 P0 S{down_value}
z_move_delay = 0.5
""")

            # Test du cycle
            print("\n" + "="*70)
            print("PHASE 3 : TEST DU CYCLE UP/DOWN")
            print("="*70)
            test = input("\nVoulez-vous tester un cycle complet? (o/n): ").lower()

            if test == 'o':
                cycles = int(input("Nombre de cycles à tester (défaut: 3): ") or "3")

                for i in range(cycles):
                    print(f"\n[CYCLE {i+1}/{cycles}]")

                    print("  → UP...")
                    ser.write(f"M280 P0 S{up_value}\n".encode())
                    time.sleep(1.5)

                    print("  → DOWN...")
                    ser.write(f"M280 P0 S{down_value}\n".encode())
                    time.sleep(1.5)

                print("\n✓ Test du cycle terminé")

            # Proposer de mettre à jour robot_config.ini
            print("\n" + "="*70)
            update = input("\nVoulez-vous mettre à jour robot_config.ini automatiquement? (o/n): ").lower()

            if update == 'o':
                update_config_file(up_value, down_value)

        else:
            print("\n[ERREUR] Calibration incomplète.")
            print("Recommencez le processus ou testez manuellement d'autres valeurs.")

        ser.close()
        print("\n[OK] Connexion fermée")

    except serial.SerialException as e:
        print(f"\n[ERREUR] Problème de connexion: {e}")
    except Exception as e:
        print(f"\n[ERREUR] {e}")
        import traceback
        traceback.print_exc()


def update_config_file(up_value, down_value):
    """
    Met à jour le fichier robot_config.ini avec les nouvelles valeurs
    """
    import os
    import configparser

    config_path = os.path.join(os.path.dirname(__file__), 'robot_config.ini')

    if not os.path.exists(config_path):
        print(f"[ERREUR] Fichier {config_path} introuvable")
        return

    try:
        config = configparser.ConfigParser()
        config.read(config_path)

        # Sauvegarder l'ancienne config
        backup_path = config_path + '.backup'
        with open(config_path, 'r') as f:
            with open(backup_path, 'w') as backup:
                backup.write(f.read())
        print(f"[OK] Sauvegarde créée: {backup_path}")

        # Mettre à jour les valeurs
        if 'Z_AXIS' not in config:
            config['Z_AXIS'] = {}

        config['Z_AXIS']['z_up_command'] = f'M280 P0 S{up_value}'
        config['Z_AXIS']['z_down_command'] = f'M280 P0 S{down_value}'

        # Sauvegarder
        with open(config_path, 'w') as f:
            config.write(f)

        print(f"[OK] robot_config.ini mis à jour avec:")
        print(f"     z_up_command = M280 P0 S{up_value}")
        print(f"     z_down_command = M280 P0 S{down_value}")

    except Exception as e:
        print(f"[ERREUR] Impossible de mettre à jour le fichier: {e}")


def manual_test(port='COM3', baudrate=115200):
    """
    Mode manuel pour tester des valeurs spécifiques
    """
    print("="*70)
    print("MODE MANUEL - TEST DE VALEURS PERSONNALISÉES")
    print("="*70)

    try:
        ser = serial.Serial(port=port, baudrate=baudrate, timeout=2)
        time.sleep(2)
        ser.read_all()

        print("\nConnecté. Entrez des valeurs S (0-180) pour tester.")
        print("Tapez 'quit' pour quitter.\n")

        while True:
            value = input("Valeur S (0-180) ou 'quit': ").strip()

            if value.lower() == 'quit':
                break

            try:
                s_value = int(value)
                if 0 <= s_value <= 180:
                    cmd = f"M280 P0 S{s_value}\n"
                    print(f"Envoi: {cmd.strip()}")
                    ser.write(cmd.encode())
                    time.sleep(1)

                    response = ser.read_all().decode(errors='ignore').strip()
                    if response:
                        print(f"[ROBOT] {response}")
                else:
                    print("Valeur hors limites (0-180)")
            except ValueError:
                print("Valeur invalide")

        ser.close()

    except Exception as e:
        print(f"[ERREUR] {e}")


def main():
    """Menu principal"""
    print("\n" + "="*70)
    print("CALIBRATION SERVO MOTEUR Z")
    print("="*70)

    print("\nChoisissez un mode:")
    print("1. Calibration automatique (recommandé)")
    print("2. Test manuel de valeurs")
    print("3. Quitter")

    choice = input("\nVotre choix: ").strip()

    port = input("\nPort série (défaut: COM3): ").strip() or "COM3"
    baudrate = input("Baudrate (défaut: 115200): ").strip() or "115200"

    if choice == '1':
        calibrate_servo(port, int(baudrate))
    elif choice == '2':
        manual_test(port, int(baudrate))
    else:
        print("Au revoir!")


if __name__ == "__main__":
    main()
