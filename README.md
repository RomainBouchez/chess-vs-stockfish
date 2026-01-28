# Configuration Marlin pour le Robot d'Échecs

Ce dossier doit contenir les fichiers de configuration Marlin utilisés pour ce projet.

## Fichiers requis

Veuillez ajouter les fichiers suivants depuis votre installation Marlin :

```
Marlin_Config/
├── Configuration.h          # Configuration principale (OBLIGATOIRE)
├── Configuration_adv.h      # Configuration avancée (OBLIGATOIRE)
├── platformio.ini           # Si modifié (optionnel)
└── README.md                # Ce fichier
```

## Pourquoi c'est important ?

**Les fichiers de configuration ne peuvent PAS être récupérés depuis la carte MKS Gen V1.4 une fois le firmware uploadé.**

Si ces fichiers sont perdus, il faudra reconfigurer Marlin depuis zéro, ce qui représente plusieurs heures de travail.

## Comment récupérer ces fichiers ?

1. Ouvrir votre projet Marlin dans VSCode/PlatformIO
2. Les fichiers se trouvent dans `Marlin/` :
   - `Marlin/Configuration.h`
   - `Marlin/Configuration_adv.h`
3. Copier ces fichiers dans ce dossier
4. Committer les changements

## Paramètres importants à documenter

Lors de l'ajout des fichiers, prenez note des paramètres suivants qui ont été modifiés :

### Configuration.h

- [ ] `MOTHERBOARD` : Type de carte (BOARD_MKS_GEN_V14)
- [ ] `BAUDRATE` : Vitesse de communication (250000)
- [ ] `DEFAULT_AXIS_STEPS_PER_UNIT` : Steps par mm pour X, Y, Z
- [ ] `DEFAULT_MAX_FEEDRATE` : Vitesses maximales
- [ ] `DEFAULT_MAX_ACCELERATION` : Accélérations
- [ ] Paramètres des endstops (X_MIN, Y_MIN, Z_MIN)
- [ ] Dimensions de la zone de travail

### Configuration_adv.h

- [ ] Paramètres des servos (si utilisés)
- [ ] Paramètres avancés des moteurs

## Checklist avant upload

- [ ] Fichiers Configuration.h et Configuration_adv.h présents
- [ ] Baudrate correspond à robot_config.ini (250000)
- [ ] Steps/mm calibrés correctement
- [ ] Endstops configurés (X et Y minimum)
