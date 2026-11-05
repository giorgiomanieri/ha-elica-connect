# Elica Connect per Home Assistant

Integrazione personalizzata per comandare le cappe Elica Connect da Home Assistant, tramite il cloud Elica.

> **Progetto non ufficiale.** Non è affiliato, approvato o supportato da Elica S.p.A. "Elica" è un marchio dei rispettivi titolari ed è usato solo per indicare i prodotti compatibili. Usi questa integrazione a tuo rischio: può smettere di funzionare se il cloud cambia, e il suo uso potrebbe non essere conforme alle condizioni del servizio Elica, con il rischio di blocco dell'account.

Provata solo su una Boxin Advance Plus (`dataModelIdx` 9). Su altri modelli può funzionare in parte o non funzionare.

## Cosa aggiunge

| Entità | Funzione |
|---|---|
| Ventola | Spenta e velocità 1, 2 e 3 (33, 67 e 100%) |
| Luce | Accensione e intensità |
| Filtri | Efficienza e stato, come sensori diagnostici |
| Azzera filtro | Pulsante per segnare il filtro come pulito, solo se il cloud lo consente |

Lo stato si aggiorna ogni 30 secondi, quindi un comando dato dal pannello fisico o da Alexa può comparire in HA con un po' di ritardo.

Il boost non è supportato: la cappa in boost appare al 100%, e da HA si può solo passare a una velocità manuale.

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
