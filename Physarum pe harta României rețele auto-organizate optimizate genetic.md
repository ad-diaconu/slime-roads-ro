# Physarum pe harta României: rețele auto-organizate optimizate genetic

Nov 7, 2026 · @Andrei

## Proiectul ales

Simulăm mucegaiul *Physarum polycephalum* pe harta reliefului României, folosim un algoritm genetic ca să găsim parametrii care produc cea mai bună rețea, apoi comparăm rețeaua rezultată cu drumurile reale.

**Ideea centrală:** un sistem fără creier, fără plan și fără control central, care urmează doar reguli locale simple, poate produce o rețea de transport comparabilă cu cea proiectată de oameni în zeci de ani. Nicio particulă nu știe unde e Clujul, și totuși rețeaua finală leagă orașele inteligent.

Proiectul are trei piloni:

- **Sistem auto-organizat:** simularea Physarum, unde ordinea globală apare din interacțiuni locale.
- **Inteligență artificială:** un algoritm genetic care optimizează parametrii simulării.
- **Repere clasice (opțional):** MST și A\* pe relief, pentru context.

## Inspirație

Punctul de plecare este experimentul Tero et al. (2010, *Science*): mucegai real, cu fulgi de ovăz așezați în pozițiile orașelor din jurul Tokyo, a format o rețea foarte asemănătoare cu rețeaua feroviară reală.

Pentru simulare există două modele:

| Model | Cum funcționează | La ce îl folosim |
| --- | --- | --- |
| Agent-based (Jeff Jones) | Mii de particule care depun și urmăresc feromoni | Vizualizare live, vene organice, „efectul wow” |
| Modelul Tero (tuburi) | Rețea de tuburi; fluxul întărește tuburile folosite și le subțiază pe celelalte | Rezultate cantitative, ușor de comparat |

Ideal le folosim pe amândouă: primul pentru demonstrație, al doilea pentru măsurători.

**Întrebarea noastră:** se aplică ideea și României, care are Carpații la mijloc?

## Întrebări de cercetare

Proiectul răspunde la cinci întrebări; diferențele dintre mucegai și realitate sunt la fel de valoroase ca asemănările.

1. **Seamănă rețeaua mucegaiului cu cea reală?** Măsurăm ce procent din legăturile reale dintre orașe regăsește mucegaiul. O potrivire mare arată că drumurile reale urmează principii naturale de eficiență.
2. **Unde diferă, și de ce?**
   - Legături pe care mucegaiul le face, dar România nu le are: candidați pentru infrastructură lipsă. Exemplu de verificat: conexiunea Moldovei peste Carpați cu Transilvania.
   - Drumuri reale pe care mucegaiul nu le face: semn de factori non-naturali (istorie, politică, buget, turism). Exemplu de discuție: Transfăgărășanul.
3. **Este rețeaua reală eficientă?** Comparăm lungimea totală, distanțele dintre orașe și robustețea.
4. **Cum se adaptează rețeaua?** Creștere pornind dintr-un singur oraș, reorganizare după blocarea unui coridor, îngroșarea venelor când un oraș crește.
5. **Ce reguli locale aproximează cel mai bine realitatea?** Răspunsul îl dă algoritmul genetic: „dacă inginerii români ar fi fost mucegai, cu ce parametri ar fi lucrat?”

## Metodologie

Regula de aur: **drumurile reale sunt doar „foaia cu răspunsuri”, nu intrare pentru simulare.** Mucegaiul crește pe o hartă „goală”, ca și cum România n-ar avea încă infrastructură.

| Mucegaiul primește | Mucegaiul NU primește |
| --- | --- |
| Orașele, ca surse de hrană (ponderate cu populația) | Niciun drum |
| Relieful, ca teren greu sau ușor de traversat | Nicio informație despre traseele reale |
| Apa (Dunărea, Marea Neagră), ca obstacol |  |

Drumurile reale apar abia la final, pentru evaluare, la fel ca etichetele de test în machine learning.

Tocmai pentru că pornește de la zero, mucegaiul poate:

- **regăsi** drumuri reale, dovadă că sunt „naturale” și eficiente;
- **propune** legături care nu există;
- **ignora** drumuri reale, construite din alte motive decât eficiența.

&#91;embedded content: fluxul proiectului · bucla algoritmului genetic și evaluarea\]

Bucla de sus se repetă la fiecare generație; drumurile reale intră în joc o singură dată, la comparația finală.

## Date și harta de altitudine

Toate sursele sunt gratuite, oficiale și folosesc același sistem de coordonate (WGS84, EPSG:4326), deci se aliniază direct.

| Ce | Sursă | Librărie | Note |
| --- | --- | --- | --- |
| Orașe + populație | Wikipedia sau simplemaps.com | pandas | 20–40 de orașe sunt suficiente |
| Drumuri reale | [Geofabrik](https://download.geofabrik.de), fișierul `romania-latest.osm.pbf` | [pyrosm](https://pypi.org/project/pyrosm/) | Citește local, fără server extern; filtru `motorway`, `trunk`, `primary` |
| Drumuri (alternativă) | OpenStreetMap prin Overpass | [OSMnx](https://nbviewer.org/github/gboeing/osmnx-examples/blob/v2.0.2/notebooks/08-custom-filters-infrastructure.ipynb) | Funcționează, dar e lent pentru o țară întreagă |
| Relief | [Copernicus DEM](https://dataspace.copernicus.eu/explore-data/data-collections/copernicus-contributing-missions/collections-description/COP-DEM) GLO-90 (90 m) sau GLO-30 (30 m) | rasterio | Descărcare fără cont din [AWS Open Data](https://registry.opendata.aws/copernicus-dem/); România nu e restricționată |

**Alinierea hărților, pas cu pas:**

1. Încărcăm DEM-ul cu `rasterio` și drumurile cu `pyrosm` / `geopandas`.
2. Reproiectăm totul într-un sistem în metri: UTM 35N (EPSG:32635) sau Stereo 70 (EPSG:3844).
3. Aducem totul pe grila simulării (de exemplu 1 pixel = 2 km): DEM-ul cu `rasterio.warp.reproject`, drumurile cu `rasterio.features.rasterize`.
4. Rezultat: relief, drumuri, orașe și simulare sunt matrice NumPy de aceeași dimensiune, perfect suprapuse.

**Test de validare:** desenăm drumurile peste relief. Dacă alinierea e corectă, DN1 urcă pe Valea Prahovei și DN7 trece prin Defileul Oltului.

Detalii fără impact la 2 km/pixel: Copernicus DEM este un model de suprafață (include clădiri și vegetație), iar altitudinea e raportată la geoidul EGM2008.

## Simularea Physarum

Fiecare particulă urmează o regulă locală: „miros feromon în față, față-stânga și față-dreapta; mă întorc spre cel mai puternic, înaintez, depun feromon”. Feromonul se difuzează și se evaporă la fiecare pas.

**Parametrii care schimbă comportamentul** (aceștia formează cromozomul algoritmului genetic):

| Parametru | Efect |
| --- | --- |
| Unghiul senzorilor | Cât de „lat” se uită particula |
| Distanța senzorilor | Cât de departe vede |
| Unghiul de rotație | Cât de brusc virează |
| Rata de evaporare | Cât de repede dispar drumurile nefolosite |
| Cantitatea depusă | Cât de puternic întărește un drum |
| Numărul de particule | Densitatea „mucegaiului” |

**Relieful ca cost:** zonele înalte sau abrupte încetinesc particulele sau reduc depunerea de feromon, așa că rețeaua ocolește Carpații prin văi, ca drumurile reale. Fără acest pas, mucegaiul ar traversa munții în linie dreaptă și comparația ar ieși prost.

**Vizualizare live:**

- fereastră `pygame` sau animație `matplotlib` cu particulele și venele care se formează;
- grilă de aproximativ 300×300 cu zeci de mii de particule, fluidă cu NumPy vectorizat;
- export GIF / video pentru prezentare.

## Algoritmul genetic

Algoritmul genetic caută parametrii cu care simularea produce cea mai bună rețea; nimeni nu știe dinainte care sunt valorile bune.

- **Cromozom:** vectorul celor aproximativ 6 parametri ai simulării.
- **Evaluare:** rulăm simularea câteva sute de pași, extragem rețeaua și îi calculăm fitness-ul.
- **Operatori:** selecție turneu, crossover aritmetic, mutație gaussiană, elitism.
- **Vizualizare live:** după fiecare generație afișăm rețeaua celui mai bun individ și graficul fitness-ului.

**Capcana fitness-ului.** Dacă fitness-ul este „cât seamănă cu drumurile reale”, drumurile se strecoară indirect în parametri. Două soluții curate:

| Variantă | Fitness | Concluzia pe care o permite |
| --- | --- | --- |
| 1 (recomandată) | Doar calitatea rețelei: lungime mică, orașe bine conectate, robustețe | „Am optimizat doar eficiența și a ieșit ceva care seamănă cu drumurile României” |
| 2 | Asemănarea cu drumurile reale, dar doar pe o regiune (de exemplu Transilvania) | Testăm pe restul țării: regulile găsite sunt generale, nu o hartă memorată |

**Cost computațional:** populație 30 × 50 de generații = 1.500 de simulări. Soluții: grilă mică (aproximativ 200×200) în timpul evoluției, NumPy vectorizat sau Numba, simulări scurte la evoluție și o rulare lungă doar pentru rezultatul final.

## Extragerea rețelei și metrici

Comparația se face la nivel de **graf de orașe**, nu pixel cu pixel: două drumuri paralele la 3 km distanță ar ieși altfel „diferite”.

**Extragerea grafului din simulare:**

1. Prag (threshold) pe harta de feromoni.
2. Subțiere cu `skeletonize` din `scikit-image`.
3. Transformare în graf `networkx`, cu orașele ca noduri.

**Metrici:**

| Metrică | Ce măsoară |
| --- | --- |
| Precision / recall / F1 pe legături | Câte legături reale regăsește mucegaiul și câte inventează |
| Lungime totală | Costul rețelei |
| Eficiență | Cât de scurte sunt drumurile între orașe față de linia dreaptă |
| Toleranță la defecte | Cât de conectată rămâne rețeaua după tăierea unei muchii aleatoare |

Pentru comparația vizuală folosim o toleranță: o venă „se potrivește” dacă trece la mai puțin de aproximativ 10 km de un drum real. Ultimele trei metrici sunt cele din articolul Tero et al.

## Repere de comparație (opțional)

Povestea principală este **natură vs. oameni**; reperele algoritmice adaugă context, dar proiectul stă în picioare și fără ele.

A\* găsește drumul cel mai scurt între **două** orașe, iar Physarum construiește o **rețea** întreagă. Ca să fie comparabile, rulăm A\* pe relief (costul crește cu panta) pentru fiecare pereche de orașe și reunim drumurile găsite.

| Rețea | Ce optimizează | Rezultat așteptat |
| --- | --- | --- |
| MST (arbore minim de acoperire) | Lungime totală minimă | Ieftină, dar fragilă |
| Reuniune de drumuri A\* | Drumuri cât mai scurte între toate orașele | Eficientă, dar foarte scumpă |
| Physarum + GA | Echilibru, apărut spontan | Undeva la mijloc |
| Drumurile reale (OSM) | Istorie, bani, politică | Probabil tot la mijloc |

Toate rețelele se pun pe același grafic cost vs. eficiență. Se pot compara și rute individuale, de exemplu București → Brașov: DN1 real vs. A\* pe relief vs. traseul mucegaiului.

Implementare: `networkx.astar_path` (sau o implementare proprie de aproximativ 40 de linii) și `networkx.minimum_spanning_tree`.

## Experimente propuse

Șapte experimente, de la obligatoriu la bonus:

| # | Experiment | Ce arată | Prioritate |
| --- | --- | --- | --- |
| E1 | Mucegai pe hartă plată vs. hartă cu relief | Cât contează Carpații pentru forma rețelei | Obligatoriu |
| E2 | Evoluția GA (fitness pe generații, rețeaua celui mai bun individ în generațiile 1, 10, 50) | Cum algoritmul genetic îmbunătățește rețeaua | Obligatoriu |
| E3 | Rețeaua optimizată vs. drumurile reale (F1, metrici, suprapunere vizuală) | Cât seamănă natura cu planificarea umană | Obligatoriu |
| E4 | Legături propuse și legături ignorate | Infrastructură potențial lipsă și drumuri „non-naturale” | Obligatoriu |
| E5 | Train/test pe regiuni (optimizare pe Transilvania, test pe restul țării) | Regulile găsite sunt generale | Recomandat |
| E6 | Reziliență: blocarea unui coridor (de exemplu Valea Oltului) în timpul simulării | Auto-reorganizarea rețelei, live | Recomandat |
| E7 | Comparație cu MST și reuniunea A\* pe graficul cost vs. eficiență | Unde se află mucegaiul și drumurile reale între extreme | Opțional |

Pentru fiecare experiment: mai multe rulări cu seed-uri diferite, cu media și abaterea standard, ca rezultatele să nu depindă de noroc.

## Extensii și idei suplimentare

- **Optimizare multi-obiectiv (NSGA-II):** în loc de un singur scor, un front Pareto de rețele, de la „ieftine, dar fragile” la „scumpe, dar robuste”; verificăm unde se află rețeaua reală a României pe front.
- **GA „pur” ca reper:** un al doilea algoritm genetic în care fiecare genă spune dacă există sau nu muchia între două orașe; comparăm ce găsește direct cu ce găsește mucegaiul optimizat.
- **Creștere dintr-un singur oraș:** pornim din București și urmărim cum mucegaiul „colonizează” țara, ca o istorie accelerată a infrastructurii.
- **Schimbarea populației:** creștem ponderea unui oraș și urmărim îngroșarea venelor spre el.
- **Ambele modele de simulare:** agent-based pentru demonstrație, modelul Tero pentru rezultate cantitative.

## Riscuri, ajustări și validări timpurii

Nicio componentă nu e riscantă; cel mai mare risc tehnic este extragerea grafului din harta de feromoni, așa că o validăm devreme.

| Risc | Ajustare |
| --- | --- |
| Mucegaiul traversează munții în linie dreaptă | Relieful ca cost (Copernicus DEM) |
| Comparația pixel cu pixel penalizează drumuri paralele apropiate | Comparație pe graful de orașe + toleranță de aproximativ 10 km |
| Drumurile reale se strecoară în parametri prin fitness | Fitness fără drumuri (varianta 1) sau train/test pe regiuni (varianta 2) |
| Evoluția durează prea mult | Grilă mică, cod vectorizat, simulări scurte în timpul evoluției |
| Extragerea grafului dă noduri și muchii parazite | Prag reglat, skeletonize, lipirea nodurilor de cel mai apropiat oraș |
| Așteptări nerealiste | Nu urmărim 100% potrivire; diferențele sunt un rezultat în sine |

**Validări în prima oră de lucru:**

- [ ] Descarcă `romania-latest.osm.pbf`, extrage `motorway|trunk|primary` și desenează-le; trebuie să apară A1, A2, DN1.
- [ ] Desenează drumurile peste relief; DN1 trebuie să urce pe Valea Prahovei, DN7 prin Defileul Oltului.
- [ ] Rulează o simulare minimă și extrage un graf din ea, chiar și urât.

## Plan de lucru și prezentare

**Etape de implementare:**

1. **Date:** orașe, drumuri (pyrosm), relief (Copernicus DEM), toate aliniate pe aceeași grilă.
2. **Simulare:** modelul agent-based cu relief ca cost, plus vizualizare live.
3. **Extragere graf:** threshold, skeletonize, graf de orașe.
4. **Metrici:** F1 pe legături, lungime, eficiență, toleranță la defecte.
5. **Algoritm genetic:** cromozom, fitness (varianta 1), operatori, vizualizare pe generații.
6. **Experimente:** E1–E4 obligatoriu, apoi E5–E7 dacă e timp.
7. **Vizualizări finale:** GIF-uri, suprapuneri, grafice.
8. **Raport și prezentare.**

**Structura prezentării:**

1. Motivație: experimentul real din Tokyo.
2. Întrebarea: se aplică și României, cu Carpații la mijloc?
3. Demo live: mucegaiul crescând pe harta reliefului.
4. Algoritmul genetic: cum s-au găsit cei mai buni parametri.
5. Rezultate: suprapunerea cu drumurile reale și metricile.
6. Discuție: unde e mucegaiul „mai deștept” decât planificarea reală și unde nu.
7. Bonus: reziliența la blocări.

## Stack tehnic și surse

**Repo:** `romania-physarum` (alternativă: `physarum-ga-romania`, unde GA = Genetic Algorithm). Descriere: *Physarum simulation on Romania's terrain, tuned by a genetic algorithm and compared with the real road network.*

| Rol | Librării |
| --- | --- |
| Simulare și calcul | Python, NumPy, Numba (opțional) |
| Vizualizare live | pygame, matplotlib |
| Date geografice | pyrosm, geopandas, rasterio, pyproj |
| Grafuri și metrici | networkx, scikit-image |

**Surse:**

- [Geofabrik, extrase OpenStreetMap](https://download.geofabrik.de)
- [pyrosm pe PyPI](https://pypi.org/project/pyrosm/)
- [OSMnx, filtre personalizate pentru infrastructură](https://nbviewer.org/github/gboeing/osmnx-examples/blob/v2.0.2/notebooks/08-custom-filters-infrastructure.ipynb)
- [Copernicus DEM, Copernicus Data Space](https://dataspace.copernicus.eu/explore-data/data-collections/copernicus-contributing-missions/collections-description/COP-DEM)
- [Copernicus DEM pe AWS Open Data](https://registry.opendata.aws/copernicus-dem/)
- [GeoPandas, sisteme de coordonate](https://geopandas.org/en/stable/docs/user_guide/projections.html)
- Tero, A. et al. (2010). *Rules for Biologically Inspired Adaptive Network Design.* Science 327(5964), 439–442.
- Jones, J. (2010). *Characteristics of Pattern Formation and Evolution in Approximations of Physarum Transport Networks.* Artificial Life 16(2), 127–153.
