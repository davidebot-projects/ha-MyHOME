# BTicino MyHOME per Home Assistant

Integrazione custom per Home Assistant che consente di controllare gli impianti
domotici **BTicino MyHOME** (protocollo OpenWebNet) tramite gateway
MyHOME Server / MH200N / F452V / F453V e compatibili.

> **Versione 2.0** — Riscrittura completa con configurazione interamente via UI.
> Non richiede più alcun file YAML.

## Fork personale — 2.1.1.post1

Questo fork deriva dalla release **2.1.1** di
[Dav41K9/ha-MyHOME](https://github.com/Dav41K9/ha-MyHOME).
La versione **2.1.1.post1** aggiunge una stima dello stato finale delle tapparelle
non avanzate dopo 180 secondi dall'ultimo evento di direzione ricevuto dal gateway.
La modifica è stata testata su Home Assistant **2026.8.2**.

### Funzionamento delle tapparelle

Con **advanced disabilitato** nelle opzioni della tapparella:

- Salita: `opening`, poi `open` con posizione stimata al 100% dopo 180 secondi.
- Discesa: `closing`, poi `closed` con posizione stimata allo 0% dopo 180 secondi.
- Ogni nuovo evento di salita o discesa annulla il conteggio precedente e ne avvia
  uno nuovo, anche se la direzione è la stessa.
- Ogni tapparella ha un conteggio indipendente.

Il conteggio parte dagli eventi del bus, quindi funziona anche con i pulsanti a
parete, HomeKit e altri metodi di comando, purché il gateway ne invii gli eventi
a Home Assistant. Alla scadenza si aggiorna solo lo stato software: non viene
inviato un comando al motore. Gli attuatori avanzati mantengono il feedback nativo.

Le impostazioni sono in `custom_components/myhome/cover.py`:

```python
TRAVEL_SECONDS = 180
CANCEL_ON_STOP = True
```

Con `CANCEL_ON_STOP = True`, uno STOP annulla il conteggio in corso e lascia la
posizione sconosciuta. Con `False`, lo stato finale viene assegnato comunque in
base all'ultima direzione, anche se il motore è stato fermato prima.
Le impostazioni valgono per tutte le tapparelle non avanzate e richiedono un
riavvio di Home Assistant dopo la modifica.

La posizione è stimata, non misurata: non vengono calcolate posizioni intermedie.
Conteggi e stati stimati non vengono conservati al riavvio. Una nuova notifica di
direzione, anche in risposta a una richiesta di stato, riavvia il conteggio.

### Esposizione a HomeKit

Esponi le entità `cover` tramite HomeKit Bridge. La classe `shutter` e i comandi
di apertura, chiusura e stop sono già presenti nell'integrazione. Non serve
aggiungere `type: shutter` alla configurazione HomeKit, né abilitare advanced
per gli attuatori senza feedback di posizione.

HomeKit usa la modalità base delle tapparelle e l'app Casa può anticipare
graficamente la posizione quando invii un comando. Lo stato finale in Home
Assistant viene assegnato alla scadenza dei 180 secondi.

---

## Funzionalità

- 🔌 **Connessione locale** al gateway via TCP (porta 20000 di default)
- 📡 **Event listener persistente** con riconnessione automatica
- 🏠 **Configurazione via UI** — gateway e dispositivi si gestiscono da
  *Impostazioni → Dispositivi e servizi*
- 📦 **Config Subentries** — ogni dispositivo è un sotto-elemento del gateway,
  modificabile singolarmente
- 🔄 **Migrazione automatica** dal vecchio file `myhome.yaml` (v1.x → v2.x)
- 🩺 **Diagnostics** — esporta lo stato dell'integrazione per il debug

### Piattaforme supportate

| Piattaforma | Descrizione | Esempi |
|---|---|---|
| `light` | Luci ON/OFF e dimmerabili | BMSW1005, F418U2 |
| `switch` | Prese e uscite relè | BMSW1005 |
| `cover` | Tapparelle e tende (anche con posizione) | F411/4 |
| `climate` | Zone termoregolate | F430R8 |
| `sensor` | Sensori di potenza | F520 |
| `binary_sensor` | Sensori binari (movimento, porta, finestra…) | — |
| `button` | Invio frame OpenWebNet personalizzati | — |

---

## Requisiti

- Home Assistant **2025.4** o superiore (per il supporto ai Config Subentries)
- Python **3.13+** (incluso in HA 2026.x)
- Un gateway BTicino MyHOME raggiungibile sulla rete locale
- La password OpenWebNet del gateway (default: `12345`)

### Dipendenze

- [OWNd](https://pypi.org/project/OWNd/) `0.7.49` — libreria di comunicazione
  OpenWebNet (installata automaticamente)

---

## Installazione

### Via HACS (consigliato)

1. Apri **HACS → Integrazioni → ⋮ → Repository personalizzati**
2. Aggiungi l'URL del fork:
   ```
   https://github.com/davidebot-projects/ha-MyHOME
   ```
3. Cerca **"BTicino MyHOME"** e installa
4. Riavvia Home Assistant

### Passaggio dal repository di Dav41K9 a questo fork

Entrambi i repository installano i file nella cartella `custom_components/myhome`.
Mantieni una sola sorgente installata in HACS.

1. Fai un backup di Home Assistant e della cartella MyHOME attualmente funzionante.
2. Rimuovi il repository di Dav41K9 **da HACS**.
3. Conserva l'integrazione MyHOME in **Impostazioni → Dispositivi e servizi**:
   non eliminare il gateway o i dispositivi configurati.
4. Aggiungi questo fork come repository personalizzato di tipo **Integration**
   e scarica la release `v2.1.1.post1` quando sarà pubblicata.
5. Riavvia Home Assistant solo dopo aver installato il fork.
6. Verifica dispositivi, tapparelle ed entità HomeKit esistenti.

### Manuale

1. Copia la cartella `custom_components/myhome/` nella tua directory
   `config/custom_components/`
2. Riavvia Home Assistant

---

## Configurazione

### 1. Aggiungi il gateway

1. Vai in **Impostazioni → Dispositivi e servizi → Aggiungi integrazione**
2. Cerca **"MyHOME"** (o "BTicino MyHOME")
3. Compila il form:

   | Campo | Esempio |
   |---|---|
   | Nome gateway | `myhomeserver1` |
   | Indirizzo IP | `192.168.1.50` |
   | Porta | `20000` |
   | Password | `12345` |
   | MAC | `00:03:50:00:00:00` |

4. Ripeti per ogni gateway (es. un secondo appartamento)

> Il gateway viene anche rilevato automaticamente via **SSDP** se presente
> sulla rete.

### 2. Aggiungi i dispositivi

1. Nella pagina dell'integrazione, clicca sul gateway → **Aggiungi sotto-elemento**
2. Scegli il tipo (Luce, Switch, Tapparella, Termostato, Sensore, ecc.)
3. Compila i campi specifici:
   - **Where**: l'indirizzo A/PL del dispositivo (es. `23`, `0115`, `0010`)
   - **Nome**: il nome visualizzato in HA
   - Campi opzionali: dimmerabile, advanced, zona, classe, produttore, modello

### 3. Migrazione da v1.x (YAML)

Se hai già un file `/config/myhome.yaml` dalla versione precedente:

1. Installa la v2.0 e aggiungi i gateway via UI (punto 1)
2. Vai in **Strumenti per sviluppatori → Azioni**
3. Esegui il servizio **`myhome.migrate_yaml`**
4. Tutti i dispositivi vengono importati automaticamente come subentries
5. Verifica in **Impostazioni → MyHOME → Config entry → Sotto-elementi**
6. Cancella `/config/myhome.yaml`

---

## Servizi

| Servizio | Descrizione |
|---|---|
| `myhome.sync_time` | Sincronizza l'orologio del gateway con HA |
| `myhome.send_message` | Invia un frame OpenWebNet raw al gateway |
| `myhome.migrate_yaml` | Importa i dispositivi dal vecchio `myhome.yaml` |

### Esempio: invio frame raw

```yaml
service: myhome.send_message
data:
  gateway_mac: "00:03:50:00:00:00"
  message: "*1*1*21##"
```

---

## Formato degli indirizzi "Where"

Il protocollo OpenWebNet identifica ogni dispositivo con un indirizzo
**A/PL** (Ambiente / Punto Luce):

| Formato | Significato | Esempio |
|---|---|---|
| `23` | PL 23, nessun ambiente | Luce semplice |
| `0115` | A=01, PL=15 | Luce in ambiente 1 |
| `0010` | A=00, PL=10 | Luce in ambiente 0 |

Per i **termostati**, il campo `where` corrisponde al numero di **zona**
(es. `1`, `2`, `3`…).

---

## Note sulla compatibilità

- ✅ HA **2026.7.x** — testato
- ✅ Python **3.13 / 3.14** — compatibile
- ⚠️ Il vecchio warning `manufacturer as list` è **risolto**
- ⚠️ I vecchi errori `Could not send message *#1*XX##` sono **risolti**
  (il polling iniziale ora avviene per-entity dopo la connessione)
- 🔜 Compatibile con HA **2026.12** (nessun pattern deprecato)

---

## Struttura dei file

```
custom_components/myhome/
├── __init__.py          # Setup integrazione, ConfigEntryNotReady
├── manifest.json        # Metadati, dipendenze, SSDP
├── const.py             # Costanti
├── config_flow.py       # Config flow gateway + subentry flow dispositivi
├── coordinator.py       # Connessione OWNd, listener, riconnessione
├── entity.py            # Base entity con DeviceInfo
├── light.py             # Luci ON/OFF e dimmer
├── switch.py            # Prese / relè
├── cover.py             # Tapparelle / tende
├── climate.py           # Termostati / zone
├── sensor.py            # Sensori di potenza
├── binary_sensor.py     # Sensori binari
├── services.py          # Servizi (sync_time, send_message, migrate_yaml)
├── services.yaml        # Descrizioni servizi per la UI
├── diagnostics.py       # Export diagnostico
├── migrate_yaml.py      # Script migrazione da v1.x
├── strings.json         # Traduzioni (fallback)
└── translations/
    └── it.json          # Traduzioni italiane
    └── en.json          # Traduzioni inglesi
```

---

## Troubleshooting

### Il gateway non si connette

- Verifica che l'IP e la porta siano corretti
- Verifica la password OpenWebNet (default `12345`)
- Assicurati che il gateway sia raggiungibile:
  ```bash
  ping 192.168.1.50
  ```
- L'integrazione riprova automaticamente ogni 10 secondi

### Un dispositivo non risponde

- Verifica il campo **Where** nel subentry
- Controlla i log: **Strumenti per sviluppatori → Log** → filtra `myhome`
- Usa il servizio `myhome.send_message` per testare il frame manualmente

---

## Pubblicazione e aggiornamento del fork

### Pubblicare la versione 2.1.1.post1

Dopo aver creato il commit e inviato le modifiche al branch `master` del fork,
pubblica una release GitHub con tag **`v2.1.1.post1`**, titolo **`2.1.1.post1`**
e destinazione il commit che contiene le modifiche. Il campo `version` in
`custom_components/myhome/manifest.json` deve essere `2.1.1.post1`.

Pubblica una release completa, non soltanto un tag: HACS deve scaricare la
versione che contiene la modifica alle tapparelle.

### Integrare la futura 2.1.2 di Dav41K9

HACS segue le release di questo fork. Le modifiche del repository originale
vanno prima unite al codice del fork e poi pubblicate in una nuova release.

1. Salva qualsiasi modifica locale in un commit. Nel clone del fork esegui:

   ```bash
   git switch master
   git pull --ff-only origin master
   git status
   git remote -v
   ```

   Continua solo con la cartella di lavoro pulita. `origin` deve puntare al tuo
   fork e `upstream` a `https://github.com/Dav41K9/ha-MyHOME.git`.
   Se `upstream` non è ancora presente, aggiungilo una sola volta:

   ```bash
   git remote add upstream https://github.com/Dav41K9/ha-MyHOME.git
   ```

2. Scarica i riferimenti del repository originale:

   ```bash
   git fetch upstream --tags
   ```

   Controlla il tag esatto nella pagina delle
   [release di Dav41K9](https://github.com/Dav41K9/ha-MyHOME/releases).
   Il formato può cambiare: il tag originale della 2.1.1 è `v.2.1.1`.
   Sostituisci `UPSTREAM_TAG` con il tag esatto della nuova 2.1.2 ed esegui:

   ```bash
   git merge --no-ff --no-commit refs/tags/UPSTREAM_TAG
   ```

3. Controlla il risultato e risolvi eventuali conflitti, eliminando i marcatori
   inseriti da Git. Conserva sia le correzioni dell'autore sia la logica dei
   180 secondi. **Non sostituire il nuovo `cover.py` con una vecchia copia**:
   potresti perdere le correzioni introdotte dalla nuova versione.
   Mantieni invariati dominio `myhome`, ID dei dispositivi e identificativi
   univoci delle entità. Se l'autore ha già incluso la stessa funzione, valuta
   se la modifica locale serve ancora.
4. Imposta la versione nel manifest a **`2.1.2.post1`**. Conserva i link alla
   documentazione e alle segnalazioni di questo fork. Aggiorna anche la versione
   e i riferimenti alla versione di base in questo README.
5. Controlla le modifiche ed esegui gli eventuali controlli pertinenti del
   repository originale:

   ```bash
   git diff HEAD -- custom_components/myhome/cover.py custom_components/myhome/manifest.json README.md
   git diff --check
   git status
   ```

   Per annullare un merge ancora in corso, usa `git merge --abort`.
6. Quando il merge è pronto, crea il commit e invialo al fork:

   ```bash
   git add -u
   git commit -m "Merge upstream 2.1.2 and retain shutter timing"
   git push origin master
   ```

7. Pubblica una release GitHub con tag **`v2.1.2.post1`** che punti al commit
   risultante su `master`.
8. Fai un backup di Home Assistant, installa la nuova release da HACS e riavvia.
   Controlla i log e verifica luci e altri dispositivi, apertura dal pulsante a
   parete, chiusura da HomeKit, stati dopo 180 secondi, inversione di direzione,
   STOP e conteggi indipendenti delle due tapparelle.

Ripeti la procedura per le versioni successive dell'originale. Per un'altra
revisione locale della stessa versione di base, aumenta il suffisso, ad esempio
`2.1.2.post2`.

---

## Crediti

- Integrazione originale: [anotherjulien/MyHOME](https://github.com/anotherjulien/MyHOME)
- Libreria OWNd: [anotherjulien/OWNd](https://pypi.org/project/OWNd/)
- Riscrittura v2.0: questo fork
- Base della versione personale: [Dav41K9/ha-MyHOME](https://github.com/Dav41K9/ha-MyHOME)
- Fork personale e conteggio tapparelle: [davidebot-projects](https://github.com/davidebot-projects/ha-MyHOME)

---

## Licenza

Vedi [LICENSE](LICENSE).

---
