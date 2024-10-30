from billboard import *
from city import *
from buses import show as show2
from buses import plot as plot2
from datetime import datetime
import os
import osmnx
import pickle
from matplotlib import pyplot as plt
from matplotlib import image as mpimg
import platform

if platform.system() == "Windows":
    clear = "cls"
# Per netejar la shell, la comanda depen del SO
else:
    clear = "clear"


def ruta(film: Film, cartellera: Billboard) -> None:
    """Indica com arribar a un determinat cinema."""

    adreca = input("Si us plau, indica la teva adreça de sortida\n")
    adreca = filtra_adreca(adreca)
    src: Coord | None = None
    while not src:
        src = coordenades(adreca)
        if not src:
            adreca = input("Adreça no vàlida, torna a provar.\n")
            adreca = filtra_adreca(adreca)

    filename = "barcelona.grf"
    filename2 = "buses.grf"
    filename3 = "ciutat.grf"

    if os.path.exists(filename):
        ox_g = load_osmnx_graph(filename)
    else:
        ox_g = get_osmnx_graph()
        save_osmnx_graph(get_osmnx_graph(), filename)

    if os.path.exists(filename2):
        bg = load_osmnx_graph(filename2)

    else:
        bg = get_buses_graph()
        with open(filename2, "wb") as f:
            pickle.dump(bg, f)

    if os.path.exists(filename3):
        g = load_city_graph(filename3)
    else:
        g = build_city_graph(ox_g, bg)
        with open(filename3, "wb") as f:
            pickle.dump(g, f)

    time_now = datetime.now()  # busquem l'hora per ensenyar les que interessen
    hora = time_now.strftime("%H%M")
    hora = int(hora[0:2]) * 60 + int(hora[2:4])
    sessions: list[Projection] = list()
    for projection in cartellera.projections:
        if projection.film == film and int(projection.time[0]) * \
                60 + int(projection.time[1]) >= hora:
            sessions.append(projection)
    if sessions:
        sessions.sort(key=lambda x: int(x.time[0]) * 60 + int(x.time[1]))
        for session in sessions:
            session_time = int(session.time[0]) * 60 + int(session.time[1])
            cinema: str = session.cinema.name
            dst: Coord = session.cinema.coord
            path = find_path(ox_g, g, src, dst)
            tpath = path_time(g, ox_g, path)
            if hora + tpath <= session_time:
                break
        pathfilename: str = input(
            "Introdueix un nom pel fitxer del camí.\n") + ".png"
        os.system(clear)
        bus_combination(path, g)
        print(f"Camina fins a {session.cinema.address}. Ja ets a"
              f" {session.cinema}! La pel·lícula comença a les"
              f" {session.time[0]}:{session.time[1]}.")
        plot_path(g, ox_g, path, pathfilename)
        plt.title(
            f"Ruta des de {adreca.upper()} fins a {cinema.upper()}.\n"
            f"La pel·lícula comença a les {session.time[0]}:{session.time[1]}")
        image = mpimg.imread(pathfilename)
        plt.axis("off")
        plt.imshow(image)
        plt.show()
        quit()
    else:
        print("No s'han trobat sessions a partir de l'hora actual.", end="")
        entrada = input(
            "Si vols tornar a fer una búsqueda introdueix l'1, \
                si vols sortir introdueix qualsevol altra tecla\n")
        if entrada == "1":
            os.system(clear)
            find_film()


def show_film(film: Film, cartellera: Billboard) -> None:
    """Donada una pel·lícula, mostra la informació i com arribar-hi."""

    entrada: str = input("Què vols?\n1. Més informació sobre la película."
                         "\n2. Com arribar-hi.\n3. Torna al menú.\n")
    if entrada == "1":
        os.system(clear)
        print("Els genères de la pel·lícula són els següents:")
        print(*film.genre, sep=", ", end="\n\n")
        print("Els actors que hi apareixen són:")
        print(*film.actors, sep=", ", end="\n\n")
        print("El seu director és:")
        print(*film.director, sep=", ", end="\n\n")
        entrada2 = ""
        while entrada2 not in ["1", "2"]:
            entrada2 = input("1. Com arribar-hi.\n2. Torna al menú.\n")
        if entrada2 == "1":
            os.system(clear)
            ruta(film, cartellera)
        else:
            os.system(clear)
            main()
    elif entrada == "2":
        os.system(clear)
        ruta(film, cartellera)
    elif entrada == "3":
        os.system(clear)
        main()
    else:
        print("Entrada no vàlida. Torna a intentar.ho")
        show_film(film, cartellera)


def find_film() -> None:
    """Filtra la cartellera segons el paràmete corresponent"""

    # obtenim o guardem la cartellera
    cartellera: Billboard = read()
    while len(cartellera.cinemas) < 15:
        # de vegades no carreguen tots els cinemes
        cartellera: Billboard = read()
    print("Què vols fer:\n1. Buscar segons el títol.\n2.", end="")
    print(" Buscar segons el gènere.\n3. ", end="")
    print("Buscar segons els actors o director.\n", end="")

    command: int = -1
    while command not in range(1, 4):
        entrada = input()
        try:
            command = int(entrada)
            if command not in range(1, 4):
                print("Entrada no vàlida")
        except ValueError:
            print("Entrada no vàlida")

    if command == 1:
        matches: list[Film] = cartellera.filtre_nom()
    elif command == 2:
        matches: list[Film] = cartellera.filtre_genere()
    elif command == 3:
        matches: list[Film] = cartellera.filtre_actors_director()
    if matches:
        os.system(clear)
        print("Hem trobat les següents coincidències:")
        for i, pelicula in enumerate(matches):
            print(f"{i+1}:", pelicula)
        print("Si vols anar a veure una d'aquestes pel·lícules", end="")
        print(" o saber-ne més introdueix el seu número. ", end="")
        print("Si en vols buscar més, introdueix \"buscar\".", end="")
        print(" Si vols tornar al menú, introdueix \"sortir\"")
        while True:
            entrada = input()
            if entrada == "buscar":
                os.system(clear)
                find_film()
                break
            if entrada == "sortir":
                os.system(clear)
                main()
            try:
                entrada = int(entrada)
                if 0 < entrada <= len(matches):
                    show_film(matches[entrada - 1], cartellera)
                    break
                else:
                    print("Entrada no vàlida. Torna a intentar-ho.")
            except ValueError:
                print("Entrada no vàlida. Torna a intentar-ho.")
    else:
        print("No hi ha hagut cap coincidència")
        entrada = input(
            "Si vols tornar a fer una búsqueda introdueix l'1,"
            "si vols sortir introdueix qualsevol altra tecla\n")
        if entrada == "1":
            os.system(clear)
            find_film()


def mostra_cartellera() -> None:
    """Mostra la cartellera del dis d'avui"""

    cartellera: Billboard = read()
    while len(cartellera.cinemas) < 12:
        cartellera: Billboard = read()
    # de vegades no es carreguen tots els cinemes.
    # la cartellera només triga a carregar-se el primer cop,
    # després es queda al cache i és més ràpid.
    cinema: Cinema | None = None
    first = True
    for projection in cartellera.projections:
        if not cinema or projection.cinema != cinema:
            if not first:
                print("\n")
                entrada: str = input("Per passar al següent cinema, prem"
                                     " l'intro. Si tornar al menú,"
                                     " introdueix \"sortir\".\n")
                os.system(clear)
                if entrada == "sortir":
                    main()
                    break
            first = False
            nom: str = projection.cinema.name.upper()
            adreca: str = projection.cinema.address
            missatge: str = f"{nom} // {adreca}"
            print(missatge + "\n" + len(missatge) * "—")
            cinema = projection.cinema
            films: set[Film] = set()
        if projection.film not in films:
            if films:
                print("\n")
            films.add(projection.film)
            print(f"{projection.film.title.upper()} | ", end="")
            print(*projection.film.director, sep=", ")
            print("Gènere(s): ", end="")
            print(*projection.film.genre, sep=", ")
            print("Actors: ", end="")
            print(f"Idioma: {projection.language}")
            print(*projection.film.actors, sep=", ")
            print("Horaris: ", end="")
        print(f"{projection.time[0]}:{projection.time[1]}", end=" ")
    os.system(clear)
    main()


def bus_graph() -> None:
    """
    Dona l'opció de mostrar per pantalla el graf de busos i
    de guardar el graf sobre el fons de Barcelona.
    """

    # obtenim o guardem el buses_graph
    filename: str = "buses.grf"
    if os.path.exists(filename):
        bg = pickle.load(open(filename, "rb"))
    else:
        bg = get_buses_graph()
        with open(filename, "wb") as f:
            pickle.dump(bg, f)

    entrada: str = input(
        "1. Mostra el graf interactiu per pantalla.\n2. "
        "Guarda una imatge del graf sobre Barcelona en un fitxer."
        "\n3. Torna al menú\n")
    if entrada == "1":
        show2(bg)
        os.system(clear)
        main()
    elif entrada == "2":
        filename: str = input(
            "Si us plau, introdueixi el nom que desitja pel fitxer\n") + ".png"
        plot2(bg, filename)
        plt.title(f"Mapa de les línies de busos de Barcelona")
        image = mpimg.imread(filename)
        plt.axis("off")
        plt.imshow(image)
        plt.show()
        os.system(clear)
        main()
    elif entrada == "3":
        os.system(clear)
        main()
    else:
        print("Entrada incorrecta.")
        bus_graph()


def city_graph() -> None:
    """
    Dona l'opció de mostrar per pantalla el graf de la ciutat i
    de guardar el graf sobre el fons de Barcelona.
    """

    # obtenim o guardem el city_graph, només es carregarà quan s'invoqui per
    # primer cop.
    filename = "barcelona.grf"
    filename2 = "buses.grf"
    filename3 = "ciutat.grf"
    if os.path.exists(filename3):
        g = load_city_graph(filename3)
    else:
        if os.path.exists(filename):
            ox_g = load_osmnx_graph(filename)
        else:
            save_osmnx_graph(get_osmnx_graph(), filename)

        if os.path.exists(filename2):
            bg = pickle.load(open(filename2, "rb"))
        else:
            bg = get_buses_graph()
            with open(filename2, "wb") as f:
                pickle.dump(bg, f)
        g = build_city_graph(ox_g, bg)

    entrada: str = input(
        "1. Mostra el graf interactiu per pantalla."
        "\n2. Guarda una imatge del graf sobre Barcelona "
        "en un fitxer.\n3. Torna al menú\n")
    if entrada == "1":
        show(g)
        os.system(clear)
        main()
    elif entrada == "2":
        filename: str = input(
            "Si us plau, introdueixi el nom que desitja pel fitxer\n") + ".png"
        plot(g, filename)
        plt.title(f"Mapa dels carrers i línies de busos de Barcelona")
        image = mpimg.imread(filename)
        plt.axis("off")
        plt.imshow(image)
        plt.show()
        os.system(clear)
        main()
    elif entrada == "3":
        os.system(clear)
        main()
    else:
        print("Entrada incorrecta.")
        city_graph()


def main() -> None:
    """Pregunta a l'usuari què vol fer."""

    os.system(clear)
    print("Què vols fer?\n1. Buscar una pel·lícula.\n2."
          " Mostra la cartellera.\n3."
          " Graf d'autobusos.\n4. Graf de la ciutat."
          "\n5. Mostra el creador del projecte\n6. Sortir.")
    command: int = -1
    while command not in range(1, 7):
        entrada = input()
        try:
            command = int(entrada)
            if command not in range(1, 7):
                print("Entrada no vàlida. Si us plau, torna a provar-ho.\n")
        except ValueError:
            print("Entrada no vàlida. Si us plau, torna a provar-ho.\n")
    if command == 1:
        os.system(clear)
        find_film()
    elif command == 2:
        os.system(clear)
        mostra_cartellera()
    elif command == 3:
        os.system(clear)
        bus_graph()
    elif command == 4:
        os.system(clear)
        city_graph()
    elif command == 5:
        entrada = input(
            "L'autor del projecte és l'Arnau Pons Oliván."
            " Per tornar al menú introdueixi qualsevol tecla."
            " Per sortir introdueix \"sortir\".\n")
        if entrada == "sortir":
            os.system(clear)
        else:
            os.system(clear)
            main()


if __name__ == "__main__":
    main()
