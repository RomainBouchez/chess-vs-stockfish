"""
Script de diagnostic pour le servo moteur Z
Teste les commandes M280 P0 S12 et M280 P0 S168
"""

import serial
import time

def test_servo_z(port='COM3', baudrate=115200):
    """
    Teste le servo moteur Z avec différentes commandes.

    Args:
        port: Port série (ex: COM3)
        baudrate: Vitesse de communication
    """
    print("="*60)
    print("TEST DIAGNOSTIC SERVO MOTEUR Z")
    print("="*60)

    try:
        # Connexion au robot
        print(f"\n[1/6] Connexion au port {port} à {baudrate} bauds...")
        ser = serial.Serial(port=port, baudrate=baudrate, timeout=2)
        time.sleep(2)  # Attendre la réinitialisation

        # Lire le message de démarrage
        startup = ser.read_until(b'\n')
        print(f"[ROBOT] {startup.decode(errors='ignore').strip()}")
        print("[OK] Connexion établie\n")

        # Test 1 : Vérifier la version du firmware
        print("[2/6] Vérification du firmware...")
        ser.write(b'M115\n')  # Commande pour obtenir la version
        time.sleep(0.5)
        response = ser.read_all().decode(errors='ignore')
        print(f"[FIRMWARE] {response}")

        # Test 2 : Vérifier si M280 est supporté
        print("\n[3/6] Test de reconnaissance de M280...")
        ser.write(b'M280\n')
        time.sleep(0.5)
        response = ser.read_all().decode(errors='ignore')
        print(f"[RESPONSE] {response}")

        if 'error' in response.lower() or 'unknown' in response.lower():
            print("\n[ERREUR] M280 n'est pas reconnu par le firmware!")
            print("Solution: Vérifiez que M280 est activé dans Configuration.h")
            ser.close()
            return False

        # Test 3 : Montée du servo (M280 P0 S12)
        print("\n[4/6] Test de montée (M280 P0 S12)...")
        print("Le servo devrait monter...")
        ser.write(b'M280 P0 S12\n')
        time.sleep(1)
        response = ser.read_all().decode(errors='ignore')
        print(f"[RESPONSE] {response}")

        input("Le servo a-t-il bougé? Appuyez sur Entrée pour continuer...")

        # Test 4 : Descente du servo (M280 P0 S168)
        print("\n[5/6] Test de descente (M280 P0 S168)...")
        print("Le servo devrait descendre...")
        ser.write(b'M280 P0 S168\n')
        time.sleep(1)
        response = ser.read_all().decode(errors='ignore')
        print(f"[RESPONSE] {response}")

        input("Le servo a-t-il bougé? Appuyez sur Entrée pour continuer...")

        # Test 5 : Cycle complet
        print("\n[6/6] Test d'un cycle complet (3 répétitions)...")
        for i in range(3):
            print(f"\nCycle {i+1}/3:")

            print("  - Montée...")
            ser.write(b'M280 P0 S12\n')
            time.sleep(1)

            print("  - Descente...")
            ser.write(b'M280 P0 S168\n')
            time.sleep(1)

        print("\n" + "="*60)
        print("TEST TERMINÉ")
        print("="*60)
        print("\nSi le servo n'a pas bougé du tout, vérifiez:")
        print("1. Le branchement du servo (Signal, VCC, GND)")
        print("2. Le numéro de pin dans le firmware (P0 = pin servo 0)")
        print("3. L'alimentation du servo (5V suffisant)")
        print("4. La configuration du firmware (M280 activé)")

        ser.close()
        return True

    except serial.SerialException as e:
        print(f"\n[ERREUR] Impossible de se connecter: {e}")
        print("\nVérifiez:")
        print(f"1. Le port {port} est correct")
        print("2. Le robot est allumé")
        print("3. Le câble USB est branché")
        print("4. Aucun autre programme n'utilise le port")
        return False

    except Exception as e:
        print(f"\n[ERREUR] {e}")
        return False


def test_different_servo_pins():
    """
    Teste différents numéros de pins servo (P0, P1, P2)
    Au cas où le servo ne serait pas sur P0
    """
    print("\n" + "="*60)
    print("TEST DES DIFFÉRENTES PINS SERVO")
    print("="*60)

    port = input("\nPort série (défaut: COM3): ").strip() or "COM3"

    try:
        ser = serial.Serial(port=port, baudrate=115200, timeout=2)
        time.sleep(2)

        for pin in [0, 1, 2]:
            print(f"\n[TEST] Pin P{pin} - Montée (S12)...")
            cmd = f'M280 P{pin} S12\n'
            ser.write(cmd.encode())
            time.sleep(1)

            response = ser.read_all().decode(errors='ignore')
            print(f"[RESPONSE] {response}")

            moved = input(f"Le servo a-t-il bougé sur P{pin}? (o/n): ").lower()
            if moved == 'o':
                print(f"\n[SUCCÈS] Le servo est sur la pin P{pin}!")
                print(f"Modifiez robot_config.ini:")
                print(f"  z_up_command = M280 P{pin} S12")
                print(f"  z_down_command = M280 P{pin} S168")
                ser.close()
                return

        print("\n[ATTENTION] Aucune pin ne fait bouger le servo.")
        print("Le problème est probablement matériel ou de configuration firmware.")
        ser.close()

    except Exception as e:
        print(f"\n[ERREUR] {e}")


def check_firmware_config():
    """
    Affiche les instructions pour vérifier la configuration du firmware
    """
    print("\n" + "="*60)
    print("VÉRIFICATION DE LA CONFIGURATION FIRMWARE")
    print("="*60)

    print("""
Pour que M280 fonctionne, votre firmware doit avoir ces options activées:

MARLIN (Configuration.h):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Activer le support servo:
   #define NUM_SERVOS 1

2. Définir la pin du servo:
   #define SERVO0_PIN 11  // ou votre pin

3. Activer M280:
   // M280 est généralement activé par défaut avec NUM_SERVOS

GRBL:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
GRBL ne supporte PAS M280 par défaut!
Vous devez utiliser:
   - M3/M5 pour contrôler un servo via PWM
   - ou un firmware modifié pour supporter M280

SOLUTION SI M280 NE MARCHE PAS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Option 1: Utiliser M3/M5 avec PWM
   - Montée: M3 S12
   - Descente: M3 S168
   - Arrêt: M5

Option 2: Reflasher le firmware avec M280 activé

Option 3: Utiliser G0 Z si vous avez un moteur pas-à-pas sur Z
   - Montée: G0 Z50
   - Descente: G0 Z5
""")


def main():
    """Menu principal"""
    print("\n" + "="*60)
    print("DIAGNOSTIC SERVO MOTEUR Z")
    print("="*60)

    print("\nChoisissez un test:")
    print("1. Test standard (M280 P0 S12/S168)")
    print("2. Test de toutes les pins servo (P0, P1, P2)")
    print("3. Afficher la documentation firmware")
    print("4. Quitter")

    choice = input("\nVotre choix: ").strip()

    if choice == '1':
        port = input("\nPort série (défaut: COM3): ").strip() or "COM3"
        baudrate = input("Baudrate (défaut: 115200): ").strip() or "115200"
        test_servo_z(port, int(baudrate))

    elif choice == '2':
        test_different_servo_pins()

    elif choice == '3':
        check_firmware_config()

    else:
        print("Au revoir!")


if __name__ == "__main__":
    main()
