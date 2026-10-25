# Modificări

## 0.2.7-beta.1 — 25 octombrie 2026

- Dimensiunea paginii de servicii este 20, conform apelului GetServicesPage din
  portalul oficial, în loc de 100. Paginarea cu cursor se păstrează.
- Erorile serviciilor precizează filtrul și dimensiunea paginii; erorile API pot
  include coduri numerice și numele parametrului validat, fără texte brute sau date de cont.
- Remediere candidată pentru HTTP 400 observat pe contul utilizatorului;
  cauza exactă și rezultatul trebuie confirmate după instalare.

## 0.2.6-beta.1 — 25 octombrie 2026

- Corectat „Last successful update”: afișează ultima citire de bază reușită și
  când o secțiune opțională eșuează. Ora citirii complete rămâne în `last_full_update`.
- Atribute noi `update_complete` și `section_errors`; erori sanitizate pe secțiuni
  disponibile și în diagnosticul integrării.
- Erorile serviciilor nu sunt mascate: senzorii afectați rămân indisponibili.

## 0.2.5-beta.1 — 25 octombrie 2026

- Senzor per vehicul pentru următoarea expirare a peajelor cu treceri nefolosite.
- Senzor de cont pentru ultima actualizare complet reușită; păstrează ora precedentă
  dacă o citire ulterioară eșuează sau este parțială.
- Date afișate în `DD/MM/YYYY HH:mm`, cu atribute ISO pentru automatizări.
- Nu sunt necesare cereri API suplimentare.

## 0.2.4-beta.1 — 25 octombrie 2026

- „Vehicle category” afișează codul, denumirea și descrierea completă în română.
- Folosește etichetele portalului oficial și limitele MTMA actuale pentru A–D/I–III.
- Codul simplu rămâne disponibil în atributul `category_code`; ID-ul este păstrat.

## 0.2.3-beta.1 — 25 octombrie 2026

- „Vignette valid until” afișează data și ora în format `DD/MM/YYYY HH:mm`,
  de exemplu `07/08/2027 23:59`, cu fusul orar Europe/Bucharest.
- Se păstrează ID-ul entității și iconul adăugat în 0.2.2.

## 0.2.2-beta.1 — 25 octombrie 2026

- Adăugat iconul furnizat de utilizator în `brand/`, pentru temele light/dark
  și variantele normale/@2x. Fișierul original este păstrat fără modificări.

## 0.2.1-beta.1 — 25 octombrie 2026

- „Vignette days remaining” devine „Vignette valid until”, cu ziua expirării
  în Europe/Bucharest (senzor DATE, fără unitate de măsură).
- ID-ul existent este păstrat; valoarea se schimbă din număr în dată.
- Traducerea română: „Rovinietă valabilă până la”.

## 0.2.0-beta.1 — 25 octombrie 2026

- Dispozitiv de cont cu 5 senzori: număr vehicule, notificări necitite, starea
  portalului, ultima factură și total plătit în anul curent.
- 7 entități per vehicul: cele 4 existente, plus date vehicul, cheltuieli și peaje.
- VIN, certificat, normă de poluare, țară, MTMA, categorie peaj și alte atribute
  disponibile local pe entitatea Date vehicul; fără export în diagnostic.
- Detalii rovinietă din serviciul care corespunde expirării raportate de vehicul.
- Cheltuieli defalcate și istoric pe 5 ani; TVA, metodă de plată și număr factură.
- Pagini de servicii cerute explicit pentru ACTIVE, EXPIRED și CONSUMED.
- Secțiunile opționale pot eșua independent; nu se publică totaluri parțiale.
- Statistici HA pentru totalurile monetare, cu reset anual în Europe/Bucharest.
- Traduceri română/engleză și exemplu de dashboard nativ.
- ID-urile unice ale celor 4 entități vechi sunt păstrate.

Extensiile sunt testate local cu date sintetice; validarea completă a datelor
autentificate și a runtime-ului Home Assistant rămâne necesară.

## 0.1.0-beta.1

Prima versiune: categorie vehicul, expirare rovinietă, zile rămase și valabilitate.
