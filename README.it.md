# Elica Connect per Home Assistant

[English](README.md)

Integrazione personalizzata per comandare le cappe Elica Connect da Home Assistant, tramite il cloud Elica.

> **Progetto non ufficiale.** Non è affiliato, approvato o supportato da Elica S.p.A. "Elica" è un marchio dei rispettivi titolari ed è usato solo per indicare i prodotti compatibili. Usi questa integrazione a tuo rischio: può smettere di funzionare se il cloud cambia, e il suo uso potrebbe non essere conforme alle condizioni del servizio Elica, con il rischio di blocco dell'account.

## Funzioni attive

Tutte le funzioni di questa tabella sono state provate su una cappa reale.

| Entità | Funzione |
|---|---|
| Ventola | Spenta, velocità 1, 2 e 3, boost (25, 50, 75 e 100%) |
| Luce | Accensione, spegnimento e intensità |
| Filtro grassi | Efficienza e stato, come sensori diagnostici |
| Azzera filtro grassi | Pulsante per segnare il filtro come pulito |

Lo stato si aggiorna ogni 30 secondi, quindi un comando dato dal pannello fisico o da Alexa può comparire in HA con un po' di ritardo.

L'interfaccia è disponibile in inglese, italiano, spagnolo, francese e tedesco, secondo la lingua di Home Assistant.

## Compatibilità

Finora l'integrazione è stata provata su una sola cappa:

| Modello | Codice | Modello dati | Installazione |
|---|---|---|---|
| Boxin Advance Plus IX/A/60 | `PRF0191539` | `dataModelIdx` 9 | Aspirante |

Sono stati provati anche l'accesso, il rinnovo del token dopo un riavvio di Home Assistant e la lettura dello stato.

### Non ancora verificato

- Filtro carbone e installazione filtrante: il codice li prevede, ma non sono stati provati.
- Durata del token di rinnovo nel tempo.
- Installazione tramite HACS.
- Altri modelli di cappa e altri modelli dati. Le entità vengono create in base agli attributi che il cloud riporta, ma il comportamento può essere diverso. In particolare, il boost usa i valori osservati sul modello dati 9.
- Purificatori Snap: non sono supportati.

Se la provi su un altro modello, apri una [issue](https://github.com/giorgiomanieri/ha-elica-connect/issues) indicando modello, `dataModelIdx` e cosa funziona. Non includere credenziali, seriali o identificativi del dispositivo.

## Requisiti

- Home Assistant 2026.3 o successivo.
- Un account Elica Connect con la cappa già abbinata nell'app.
- La tua copia dell'app Elica Connect in formato APK, da cui ricavare la credenziale client. Questo repository non la contiene.

## Installazione

Con HACS: aggiungi questo repository come repository personalizzato di tipo **Integration**, installa **Elica Connect** e riavvia Home Assistant.

A mano: copia `custom_components/elica_connect` in `/config/custom_components/` e riavvia Home Assistant.

## Configurazione

1. Copia negli appunti la credenziale client dalla tua copia dell'APK. Il comando funziona su Windows e non la mostra a schermo:

   ```bash
   python elica_probe.py --apk PERCORSO_APK --copy-client-credential
   ```

2. In Home Assistant apri **Impostazioni > Dispositivi e servizi > Aggiungi integrazione** e cerca **Elica Connect**.
3. Inserisci email e password Elica, poi incolla la credenziale client.

La password serve solo per il primo accesso e non viene salvata. HA conserva in `.storage` il token di rinnovo e la credenziale client, quindi tratta quella cartella e i backup come dati sensibili. Se il token scade, HA ti chiederà di nuovo la password.

## Privacy

L'integrazione e `elica_probe.py` comunicano solo con il cloud Elica (`cloudprod.elica.com`), come fa l'app ufficiale. Le credenziali e i comandi vanno a Elica, e da Elica arrivano stato della cappa e dati dei filtri.

Questo progetto non include telemetria e non invia dati all'autore o ad altri servizi. Il trattamento dei dati da parte di Elica è regolato dalla sua informativa privacy.

## Strumenti

`elica_probe.py` è un client da riga di comando per leggere lo stato e provare luce e ventola. Usa solo la libreria standard di Python:

```bash
python elica_probe.py --apk PERCORSO_APK --raw
```

## Licenza

[MIT](LICENSE). La licenza riguarda solo il codice di questo repository.
