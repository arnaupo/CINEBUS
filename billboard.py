from dataclasses import dataclass
from typing import TypeAlias, Optional
from bs4 import BeautifulSoup
import requests
import json
import city


class Film:
    title: str
    genre: list[str]
    director: list[str]
    actors: list[str]

    def __init__(
            self,
            title: str,
            genre: list[str],
            director: list[str],
            actors: list[str]) -> None:
        self.title = title
        self.genre = genre
        self.director = director
        self.actors = actors
        self.tradueix_generes()

    def __hash__(self) -> int:
        return sum(ord(c) for c in self.title) * len(self.title)

    def __repr__(self) -> str:
        return f"{self.title}"

    def __eq__(self, other: object) -> bool:
        return self.title == other.title

    def __ne__(self, other: object) -> bool:
        return not self.title == other.title

    def tradueix_generes(self) -> None:
        """Tradueix els gèneres de la pel·lícula al català."""

        i = 0
        while i < len(self.genre):
            self.genre[i] = self.genre[i].replace(
                "Acción",
                "Acció").replace(
                "Ciencia ficción",
                "Ciència ficció").replace(
                "Fantasía",
                "Fantasia").replace(
                "Comedia",
                "Comèdia").replace(
                    "Animación",
                    "Animació").replace(
                        "Familia",
                        "Família").replace(
                            "Suspense",
                            "Suspens").replace(
                                "Crimen",
                                "Crim").replace(
                                    "Biografía",
                                    "Biografia").replace(
                                        "Romántico",
                                        "Romàntic").replace(
                                            "Comedia dramática",
                                            "Comèdia dramàtica")
            i += 1


@dataclass
class Cinema:
    name: str
    address: str
    coord: tuple[float, float]

    def __repr__(self) -> str:
        return f"{self.name}"

    def __eq__(self, other: object) -> bool:
        return self.name == other.name

    def __ne__(self, other: object) -> bool:
        return self.name != other.name


@dataclass
class Projection:
    film: Film
    cinema: Cinema
    time: tuple[str, str]   # hora:minut
    language: str


@dataclass
class Billboard:
    films: list[Film]
    cinemas: list[Cinema]
    projections: list[Projection]

    def filtre_nom(self) -> list[Film]:
        """Donat un/s mot/s, mostra quines pel·lícules el/s contenen."""

        fts: str = input("Quina pel·lícula vols buscar?\n")
        matches: set[Film] = set()
        for film in self.films:
            if film.title.lower().find(fts.lower()) >= 0:
                matches.add(film)
        return list(matches)

    def filtre_genere(self) -> None:
        """
        Donat un o més gèneres, retorna quines pel·lícules
        tenen almenys un dels gèneres.
        """

        genres: list[str] = input(
            "Quins generes (separats per un espai)  ").split()
        matches: set[Film] = set()
        for film in self.films:
            fgenre: list[str] = [genre.lower() for genre in film.genre]
            if any(gen.lower() in fgenre for gen in genres):
                matches.add(film)
        return list(matches)

    def filtre_actors_director(self) -> None:
        """
        Donat el nom d'un actor o director, retorna en quines
        pel·lícules hi apareixen.
        """
        actdir: str = input(
            "Quin actor o director vols buscar?")
        matches: set[Film] = set()
        for film in self.films:
            factdir: list[str] = (
                " ".join(
                    film.actors) +
                " ".join(
                    film.director)).lower()
            if factdir.find(actdir.lower()) == 0:
                matches.add(film)
        return list(matches)


def get_theater(cinemes, i, cinemas: list[Cinema]) -> Cinema | None:
    """Retorna el cinema actual si és a Barcelona."""

    adreca: str = cinemes[i].find_all(
        "span", class_="lighten")[-1].text.lower()
    if "barcelona" in adreca:
        nom: str = cinemes[i].h2.a.text.replace("\n", "")
        adreca = city.filtra_adreca(adreca).replace("\n", "")
        coord = city.coordenades(adreca)
        cinema_actual: Cinema = Cinema(nom, adreca, coord)

        return cinema_actual
    return None


def get_film(film_data, mov: set[Film], films: list[Film]) -> Film:
    """Retorna la pel·lícula actual."""

    # get each individual film info.
    film_dict: dict[str, str | list[str]
                    ] = json.loads(film_data.div["data-movie"])
    title: str = film_dict["title"]
    genre: list[str] = film_dict["genre"]
    directors: list[str] = film_dict["directors"]
    actors: list[str] = film_dict["actors"]
    movie = Film(title, genre, directors, actors)
    if title not in mov:  # Si la pel·lícula
        # no ha estat visitada, l'afegim.
        mov.add(title)
        films.append(movie)
    return movie


def get_film_hours(film_data) -> list[tuple[str, str]]:
    """Retorna el llistat d'hores en què s'emet una pel·lícula determinada."""

    hours: list[tuple[str, str]] = list()
    ul = film_data.find("ul")
    for li in ul.find_all("li"):
        counter = 0
        time = ''
        for char in str(li):
            if char in "1234567890":
                time += char
                counter += 1
                if counter == 4:
                    break
        hours.append((time[0:2], time[2:4]))
    return hours


def get_projection(film: Film, cinema: Cinema,
                   time: tuple[str, str], film_data) -> Projection:
    """
    Retorna la projecció d'un film; informació sobre la pel·lícula,
    cinema, horaris i llengua.
    """

    language = "Castellà"
    # Predeterminat en castellà; si no, VO.
    spec = str(film_data.find("span", class_="bold"))
    spec = spec.replace(
        "<span class=\"bold\">",
        "").replace(
        "</span>",
        "").replace(
        " ",
        "")
    if spec == "VersiónOriginal":
        language = "Versió Original"

    return Projection(film, cinema, time, language)


def get_Billboard(films, cinemas, projections, soup) -> None:
    """Crea la cartellera del dia d'avui."""

    mov: set[Film] = set()  # conté les pel·lícules ja visitades
    cinemes = soup.find_all("div", class_="margin_10b j_entity_container")
    contingut_cine = soup.find_all("div", class_="tabs_box_panels")
    for i in range(len(cinemes)):
        cinema = get_theater(cinemes, i, cinemas)
        if cinema:
            cinemas.append(cinema)
            panel = contingut_cine[i]
            panel_avui = panel.div  # limitem a les pel·lícules d'avui
            pelicules = panel_avui.find_all("div", class_="item_resa")
            for info_film in pelicules:
                pelicula: Film = get_film(info_film, mov, films)
                horari: list[tuple[str, str]] = get_film_hours(info_film)
                for sessio in horari:
                    projections.append(
                        get_projection(
                            pelicula,
                            cinema,
                            sessio,
                            info_film))


def read() -> Billboard:
    """Retorna la cartellera del dia d'avui."""

    films: list[Film] = list()
    cinemas: list[Cinema] = list()
    projections: list[Projection] = list()

    for url in [
        "https://www.sensacine.com/cines/cines-en-72480/?page=1",
        "https://www.sensacine.com/cines/cines-en-72480/?page=2",
            "https://www.sensacine.com/cines/cines-en-72480/?page=3"]:

        r = requests.get(url).content
        soup = BeautifulSoup(r, "lxml")

        get_Billboard(films, cinemas, projections, soup)

    return Billboard(films, cinemas, projections)
