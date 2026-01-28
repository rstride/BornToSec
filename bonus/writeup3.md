# Writeup 3 : Accès Physique (GRUB Exploit)

## Contexte

Cette méthode suppose un accès physique à la machine (ou via la console de virtualisation). L'objectif est d'exploiter le chargeur de démarrage (GRUB) pour obtenir un accès root direct sans authentification.

L'ISO fournie est exécutée dans *VirtualBox*.

## Collecte d’informations

### Analyse de la VM

VirtualBox fournit des outils en ligne de commande permettant de requêter certaines informations à propos de la VM. Il est possible dans un premier temps de récupérer la version du **kernel/release** ainsi que son IP associée via de simples commandes :

```bash
VBoxManage guestproperty enumerate $VM_NAME | grep "OS/Release"
VBoxManage guestproperty enumerate $VM_NAME | grep "V4/IP"
```

Ce qui nous donne (exemple) :

```
Name: /VirtualBox/GuestInfo/OS/Release, value: 3.2.0-91-generic-pae [...]
Name: /VirtualBox/GuestInfo/Net/0/V4/IP, value: 10.11.200.46 [...]
```

Si les Guest Additions ne sont pas installées, on peut scanner le réseau local pour trouver l'IP :

```bash
ANALYSER_IP=$(hostname -I | cut -d" " -f1)
netdiscover -r $ANALYSER_IP/24
```

### Identification des Services

Un scan Nmap rapide permet d'identifier les services :

```bash
nmap -A -T4 -Pn $TARGET
```

Services identifiés :
- **OpenSSH** : 5.9p1 Debian 5ubuntu1.7
- **VSFTPD** : 2.0.8 or later
- **Apache** : 2.2.22 (Ubuntu)
- **Dovecot** : IMAP

## Recherche de Vulnérabilités

Une recherche rapide via `searchsploit` sur les versions identifiées ne donne pas d'exploit RCE direct et trivial sans authentification pour ces versions spécifiques, nous orientant vers une approche différente si l'on possède l'accès physique.

## L’Exploitation (Root via GRUB)

Puisque nous avons accès à la séquence de démarrage ("Accès Physique"), nous pouvons modifier les paramètres passés au noyau Linux par GRUB.

1.  Redémarrer la machine virtuelle.
2.  Maintenir la touche **Shift** enfoncée lors du démarrage pour afficher le menu GRUB.
3.  Appuyer sur **'e'** pour éditer l'entrée de démarrage par défaut.
4.  Chercher la ligne commençant par `linux`.
5.  Modifier cette ligne pour changer le processus d'initialisation (`init`). Par défaut, c'est `/sbin/init`, mais nous pouvons le remplacer par un shell.
6.  Ajouter `rw` (pour monter le système de fichiers en lecture/écriture) et `init=/bin/bash` à la fin de la ligne.

Exemple de ligne modifiée :
```bash
linux /boot/vmlinuz-3.2.0-91-generic-pae root=... ro quiet splash rw init=/bin/bash
```

7.  Appuyer sur **F10** (ou Ctrl+x) pour démarrer avec ces paramètres.

## Conclusion

Le système démarre et lance directement `/bin/bash` avec les privilèges **root**, sans demander de mot de passe.

Nous sommes désormais **root**.

**Remédiation :**
Pour empêcher cela, il est nécessaire de protéger le menu GRUB par un mot de passe et de sécuriser le BIOS/UEFI pour empêcher le démarrage sur des périphériques externes.
