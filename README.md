# CINEBUS

Aquest projecte permet als barcelonins trobar una pel·lícula d'acord a les seves preferències i ensenyar-los com arribar al cinema que la mostri el més aviat possible en desplaçaments en bus i a peu.

## Comencem

Aquestes instruccions et permetran obtenir una còpia del projecte en funcionament en la teva màquina local per propòsits de proves i desarollament. Per a saber com desplegar el projecte, ves a **Deployment**.

### Prerequisits:

Per a aquest projecte calen les següents llibreries:

* `requests` per baixar-vos fitxers de dades.
* `beatifulsoup` per llegir els arbres HTML.
* `networkx` per a manipular grafs.
* `osmnx` per a obtenir grafs de llocs (Barcelona en aquest cas).
* `haversine` per a calcular distàncies entre coordenades.
* `staticmap` per pintar mapes.
* `datetime` per a accedir a l'hora de l'usuari.
* `matplotlib` per al plot dels garfs.
* `platform` per a saber el sistema operatiu. No cal instal·lar-lo, però es necessari per fer els clears de la shell amb la comanda corresponent.

I com a addició d'aquestes cal instal·lar també:

* `lmxl` Per al web scraping.
* `scikit_learn` per a dibuixar grafs.

Aquestes últimes dues no cal importar-les, però sí que són mòduls usats per altres llibreries necessàries.
Per instal·lar-los cal executar la següent comanda:

```
pip install (nom de la llibreria)
```

### Instal·lar el projecte:

Per instal·lar el projecte cal baixar i descomprimir la carpeta zip.

## Com funciona?

Per a utilizar el programa, cal executar el programa `demo.py` des de la consola. Un cop s'executi, és possible que altres documents s'afegeixin a la carpeta per a reduïr el temps d'execució en futurs usos.

L'interfície compta amb diferents apartats, un per accedir i buscar pel·lícules segons el seu títol o gèneres o bé pel nom d'un actor o director. Un cop es troben les coincidències es dona l'opció de continuar buscant o bé d'indagar més una pel·lícula. Aquí es dona l'opció de mostrar la ruta fins la pròxima projecció o bé obtenir més informació sobre la pel·lícula. El següent apartat permet veure la cartellera del dia d'avui, donant informació sobre la pel·lícula (títol, director, gèneres, actors, idioma i horaris.) El tercer apartat dona accés al graf de busos, on es pot demanar un graf interactiu de les línies d'autobusos de Barcelona o que es descarregui una imatge de les línies sobre el mapa de Barcelona. El quart apartat és el mateix que l'anterior, però en aquest cas afegint-hi els carrers i cruïlles de Barcelona. Finalment hi ha les opcions de l'autor i una última per sortir.

### Detalls:

El projecte s'ha fet considerant que sempre hi ha un autobús disponible, a més que el temps entre parada i parada s'ha fet considerant el 55% de la velocitat d'aquell carrer, de manera que el temps per arribar no és el que seria en la realitat.

En introduïr el nom del carrer en què un s'hi troba cal ser ben específic; els determinant de, del..., han de ser els adeqüats, ja que hi ha carrers molt similars o amb el mateix nom.

Un cop es tanca la finestra interactiva del camí fins al cinema, apareix per pantalla la ruta escrita.

### Gràfics:

Quan es demana que es mostri un graf, s'obrirà una nova finestra amb el graf corresponent. A més, si és el graf sobre Barcelona es guardarà a la mateixa carpeta la imatge amb el nom de fitxer que decideixi l'usuari.

 En el cas de la imatge que mostra el camí des de la localització de l'usuari fins al cinema, les línies negres corresponen al trajecte a peu, mentre que les línies blaves al trajecte en bus i els punts blaus les parades. El punt vermell és la sortida i el verd és l'arribada.

## Fet amb:

* Python 3.11 (https://www.python.org/downloads/release/python-3110/)


## Autor

* **Arnau Pons** 


