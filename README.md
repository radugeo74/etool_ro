# eToll România — Home Assistant

Integrare independentă, fără cheie de activare, trial, abonament sau telemetrie.
Codul nou este disponibil sub licența MIT. Nu este afiliat CNAIR sau proiectului
`cnecrea/tollro` și nu include cod din acel proiect. Iconul a fost furnizat de
utilizator; licența MIT a codului nu stabilește drepturile asupra acestui material grafic.

**Stare: 0.2.7-beta.1.** Clientul este testat automat cu răspunsuri sintetice și
un server HTTP local. Autentificarea cu un cont real, schema răspunsurilor
autentificate și încărcarea într-o instalare Home Assistant nu sunt încă validate.
Nu considera această versiune confirmată pentru utilizare zilnică înaintea
testului de acceptanță descris mai jos.

## Funcții incluse

Iconul furnizat este inclus în `brand/`, pentru teme luminoase și întunecate,
în rezoluția originală. Imaginile locale sunt acceptate de Home Assistant 2026.3+
([documentație](https://contributors.home-assistant.io/core/integrations/brands/)).

- Configurare și reautentificare din interfața Home Assistant.
- Profilul curent eToll, vehicule paginate și descoperirea vehiculelor nou adăugate.
- Categorie vehicul, momentul expirării rovinietei, data/ora formatată și valabilitate.
- Actualizare eToll la 30 de minute; recalculare locală la fiecare minut.
- Reînnoirea tokenului în memorie și reconectare dacă refresh tokenul a expirat.
- Diferențiere între date necunoscute, rovinietă lipsă și serviciu indisponibil.
- Diagnostic fără email, număr de înmatriculare, VIN, parolă sau token.
- Interfață în română și engleză.

Versiunea 0.2 adaugă detalii tehnice, cheltuieli, peaje, facturi și notificări.
Alertele se configurează prin automatizările Home Assistant; un exemplu este în
`examples/alerts.yaml`. Un card de dashboard nativ, fără alte pluginuri, este în
`examples/dashboard.yaml`. Înlocuiește ID-urile demonstrative cu cele reale din HA.

## Entități și detalii în versiunea 0.2

| Dispozitiv | Entitate | Detalii în atribute |
| --- | --- | --- |
| Cont | Număr vehicule | — |
| Cont | Ultima actualizare reușită | Ora ultimei citiri de bază, starea și erorile secțiunilor |
| Cont | Notificări necitite | — |
| Cont | Starea portalului eToll | Componenta și actualizarea stării |
| Cont | Ultima factură | Număr, dată, metodă de plată, servicii, net, TVA |
| Cont | Total plătit în anul curent | An, istoric pe 5 ani, număr facturi, net, TVA |
| Vehicul | Categorie vehicul | Cod, denumire și descriere; codul simplu rămâne în `category_code` |
| Vehicul | Expirare rovinietă | Valabilă de la, perioadă, stare, serie, preț și achiziție, dacă există serviciul corespunzător în cont |
| Vehicul | Rovinietă valabilă până la | Data și ora în format `07/08/2027 23:59`, Europe/Bucharest |
| Vehicul | Rovinietă valabilă | — |
| Vehicul | Date vehicul | Număr, VIN, certificat, normă de poluare, cod țară, MTMA, categorie peaj, tip, favorit și număr provizoriu |
| Vehicul | Cheltuieli vehicul în anul curent | Roviniete, peaje, tichete de rută, istoric, achiziții și ultima achiziție |
| Vehicul | Treceri de pod rămase | Pachete active, pod, sold inițial/rămas și expirare |
| Vehicul | Următoarea expirare a peajelor | Prima expirare a unui pachet cu treceri nefolosite; atribut ISO `expires_at` |

Atributele se găsesc în dialogul entității. VIN-ul și seria certificatului sunt
păstrate local în starea HA și pot apărea în Recorder; diagnosticul integrării
nu le exportă. Nu sunt colectate trasee sau coordonate.

Cei doi senzori adăugați în 0.2.5 afișează `DD/MM/YYYY HH:mm` în Europe/Bucharest.
„Următoarea expirare a peajelor” ignoră pachetele consumate și expirate; devine
`unknown` dacă nu mai sunt treceri disponibile sau dacă lipsește data unui pachet
neconsumat. La eroarea secțiunii de servicii devine `unavailable`.

Din 0.2.6, „Ultima actualizare reușită” avansează după citirea de bază a vehiculelor,
cu profilul verificat, chiar dacă o secțiune opțională eșuează. La eșecul citirii
de bază păstrează ora precedentă. `update_complete` arată dacă au reușit și toate
secțiunile; `last_full_update` păstrează separat ora ultimei citiri complete.
`section_errors` indică etapa (`fetch` sau `parse`) și motivul sanitizat, fără
date de cont ori răspunsuri API brute. Atributele `updated_at` (ISO),
`last_poll_succeeded` și `sections_available` rămân disponibile.
Orele sunt ținute în memorie: după restart rămân necunoscute până la succesul
corespunzător. O eroare a serviciilor nu mai ascunde actualizarea vehiculelor.

Din 0.2.4, „Vehicle category” afișează denumirea completă în română, de exemplu
`A — Autoturisme (sub 8+1 locuri)`, folosind etichetele portalului eToll și limitele
MTMA verificate la 25 octombrie 2026. Codul tehnic este păstrat în atributul
`category_code`. Dacă o automatizare compara starea cu `A`, folosește acum acest
atribut. Categoriile nerecunoscute se afișează cu codul original.

## Actualizare de la 0.1.0-beta.1

Păstrează o copie a folderului vechi în afara `custom_components`, suprascrie
fișierele din `/config/custom_components/etoll_ro` cu cele din arhiva nouă și
repornește Core. Nu elimina intrarea integrării: datele de acces, ID-urile celor
4 entități existente și istoricul se păstrează. Entitățile noi se adaugă automat.
Rollback: restaurează folderul vechi și repornește Core; entitățile noi pot rămâne
indisponibile în registru până la eliminarea lor manuală.

## Instalare manuală a versiunii beta

1. Folosește Home Assistant Core 2025.11 sau mai nou (țintă de compatibilitate,
   încă neverificată într-un runtime HA).
2. Din arhiva de instalare copiază directorul `custom_components/etoll_ro` în
   `/config/custom_components/etoll_ro` pe sistemul Home Assistant.
3. Repornește Home Assistant.
4. Setări → Dispozitive și servicii → Adaugă integrare → **eToll România**.
5. Introdu local emailul/telefonul și parola contului eToll. Selectează în prealabil
   profilul dorit în portalul oficial și verifică existența vehiculelor.

Home Assistant persistă datele de acces în stocarea sa de configurare; protejează
accesul la sistem și backupuri. Integrarea nu scrie parole sau tokenuri în loguri.
Tokenurile sunt ținute doar în memorie și se regenerează după restart.

## Instalare prin HACS

Structura repository-ului include `hacs.json` și un singur domeniu de integrare.
**Nu există încă un repository publicat pentru acest proiect.** Instalarea HACS
prin URL devine disponibilă după publicarea surselor într-un repository GitHub:

1. Actualizează `documentation` din manifest cu URL-ul noului repository și
   completează `codeowners` cu administratorul real; nu folosi URL-ul proiectului
   `cnecrea/tollro` pentru această integrare.
2. Publică sursele, `hacs.json`, README și licența, fără `.venv`, `.research` sau date locale.
3. În HACS → Custom repositories adaugă URL-ul repository-ului, tip **Integration**.
4. Instalează și urmează pașii de configurare de mai sus.

Nu este necesară listarea în catalogul implicit HACS pentru un custom repository.
Validarea HACS/hassfest rămâne de făcut după completarea metadatelor GitHub.

## Semantica senzorilor

`Rovinietă valabilă` este `on` cât timp momentul curent nu depășește expirarea
confirmată. Dacă API-ul returnează explicit expirare `null` pentru o categorie
A–D, starea este `off`. Dacă eligibilitatea lipsește sau categoria nu este A–D,
starea este `unknown`. La erori de rețea/API, entitățile devin `unavailable`.
Senzorul datei de expirare este `unknown` când API-ul nu furnizează o dată.

Din 0.2.1, senzorul „Vignette days remaining” devine „Vignette valid until”
(„Rovinietă valabilă până la”). Din 0.2.3 afișează data și ora ca text în format
`DD/MM/YYYY HH:mm`, de exemplu `07/08/2027 23:59`, în Europe/Bucharest.
ID-ul existent este păstrat, inclusiv sufixul vechi `days_remaining` dacă HA l-a
generat astfel; valoarea lui este acum text formatat, nu un număr. Automatizările proprii
care comparau acest senzor numeric trebuie adaptate. Cardurile cu nume scris manual
trebuie redenumite manual. Senzorul separat „Expirare rovinietă” păstrează data și ora.

Timestampurile cu offset sunt respectate. Pentru timestampuri fără offset se
presupune Europe/Bucharest; această presupunere necesită verificare pe un cont real.
Home Assistant afișează data în fusul orar configurat în interfața sa.

Integrarea nu schimbă profilul curent și nu cumpără, șterge sau modifică date.
Dacă profilul este schimbat din portal/aplicația mobilă, actualizarea este oprită
până când profilul inițial este restabilit. Nu se amestecă datele celor două profile.
Vehiculele dispărute rămân indisponibile în registrul HA; nu se șterge istoricul.

`Date vehicul` folosește clasa HA Problem: `on` înseamnă date marcate invalide de
eToll, `off` date valide, iar `unknown` înseamnă că API-ul nu precizează.

Cheltuielile pe vehicul includ serviciile ACTIVE, EXPIRED și CONSUMED, după
`firstTransactionDate`. DRAFT, CANCELLED și REFUNDED sunt excluse. Plățile din
facturi sunt grupate după `paymentDate` și includ alimentările PER_KM; prin
urmare pot diferi de cheltuielile pe vehicul. Istoricul cuprinde anul curent și
cei 4 ani anteriori. Calendarul folosește Europe/Bucharest; banii sunt însumați
cu Decimal înainte de rotunjire. Totalurile monetare au `state_class: total`
și reset explicit la 1 ianuarie pentru statisticile HA, inclusiv corecții în minus.

La eșecul unui endpoint opțional, numai secțiunea lui devine indisponibilă.
Se resping paginile incomplete, ID-urile duplicate și statusurile necunoscute:
nu se publică totaluri parțiale. Zero înseamnă răspuns complet fără sume/treceri;
o eroare nu se transformă în zero. Rovinieta nu depinde de aceste secțiuni.

Peajele afișate provin din serviciile contului; nu se promite descoperirea
trecerilor cumpărate în alte conturi. Statusul public urmărește portalul,
componenta 1; nu este o verificare individuală a tuturor API-urilor.

## Test de acceptanță pe Home Assistant

1. Confirmă că integrarea se încarcă și că autentificarea reușește.
2. Compară numărul vehiculelor, categoria și expirarea cu portalul oficial.
3. Verifică o rovinietă absentă și, dacă există, o categorie fără rovinietă.
4. Așteaptă cel puțin 35 de minute pentru a verifica reîmprospătarea sesiunii.
5. Repornește Home Assistant: aceeași identitate de dispozitive și aceiași senzori.
6. Verifică reautentificarea și revenirea din indisponibilitate fără alerte false.
7. Configurează alertele numai după confirmarea datelor afișate.
8. Compară ultima factură, totalurile anuale și soldul peajelor cu portalul.
9. În diagnostic verifică `sections_available`; o secțiune `false` necesită
   investigare. Poți trimite diagnosticul integrării, fără exporturi brute de cont.

Nu trimite parole, tokenuri sau exporturi HAR nesanitizate în chat ori în issues.
Un eșec trebuie raportat prin mesajul generic afișat, versiunea HA și diagnosticul
integrării. Dacă SSO respinge `password` grant, este necesar un flux de autentificare
suportat de furnizor; nu există ocolirea autentificării.

## Dezvoltare și verificări

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements-dev.txt
.venv\Scripts\python -m pytest -q
.venv\Scripts\ruff check custom_components tests
.venv\Scripts\python -m compileall -q custom_components
```

Testele clientului rulează fără Home Assistant, inclusiv pe Windows. Ele nu înlocuiesc
testele config flow, entity lifecycle și reauth în Home Assistant. Detaliile despre
sursele protocolului și limitele validării sunt în `docs/PROTOCOL.md`.

Dezinstalare: elimină integrarea din Dispozitive și servicii, șterge numai directorul
`/config/custom_components/etoll_ro` și repornește. Contul și datele eToll nu se modifică.

### Indicatorul pentru taxele de pod (0.2.8)

Configurația publică `portal-extern/appsettings.json` este citită la fiecare
actualizare (30 minute). Dacă `REMOVESERVICES` conține tokenul `BRIDGE`,
**Bridge crossings remaining** afișează **Taxă anulată din 01.10.2026**.
Textul și data sunt cele solicitate de utilizator; configurația portalului indică
retragerea serviciului și nu furnizează o dată sau domeniul legal al anulării.
Când indicatorul dispare din șir, senzorul revine la numărul de treceri valabile.
O configurație lipsă, invalidă sau inaccesibilă face senzorul indisponibil.
Istoricul cheltuielilor și ID-ul entității rămân neschimbate.
