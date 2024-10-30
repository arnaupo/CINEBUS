from dataclasses import dataclass
import networkx
from buses import *
from typing import TypeAlias, Optional
import osmnx
import os
import staticmap
import pickle
from haversine import haversine, Unit
import time


CityGraph: TypeAlias = networkx.Graph

OsmnxGraph: TypeAlias = networkx.MultiDiGraph

Coord: TypeAlias = tuple[float, float]   # (latitude, longitude)

NodeID: TypeAlias = int | Parada

Path: TypeAlias = list[NodeID]


def get_osmnx_graph() -> OsmnxGraph:
    """Crea i retorna el graf de la ciutat de Barcelona"""

    graph = osmnx.graph_from_place(
        "Barcelona",
        network_type='walk',
        simplify=True)

    for u, v, key, geom in graph.edges(data="geometry", keys=True):
        if geom is not None:
            del (graph[u][v][key]["geometry"])
    return graph


def save_osmnx_graph(g: OsmnxGraph, filename: str) -> None:
    """Guarda el graf g al fitxer filename"""

    pickle.dump(g, open(filename, "wb"))


def load_osmnx_graph(filename: str) -> OsmnxGraph | None:
    """Retorna el graf guardat al fitxer filename"""

    if os.path.exists(filename):
        g = pickle.load(open(filename, "rb"))
        return g
    return None


def join_parada_cruilla(
        g1: OsmnxGraph,
        g2: BusesGraph,
        G: CityGraph) -> CityGraph:
    """Junta cada parada amb la seva cruïlla més propera """

    xs: list[float] = list()
    ys: list[float] = list()
    for parada in g2.nodes(data=True):
        xs.append(parada[1]["x"])
        ys.append(parada[1]["y"])
    # unim cada parada amb la cruïlla més propera.
    closest_nodes = osmnx.nearest_nodes(g1, xs, ys)
    aux = networkx.Graph()
    for cruilla, parada in zip(closest_nodes, g2.nodes()):
        G.add_edge(cruilla, parada, length=haversine(
            (g1.nodes[cruilla]["x"], g1.nodes[cruilla]["y"]),
            (parada.y, parada.x)))
    # definim la distància entre cada parada (el cami més curt entre les dues
    # cruïlles més properes)
    for p1, p2 in g2.edges():
        c1: NodeID = list(G.edges(p1))[-1][1]
        c2: NodeID = list(G.edges(p2))[-1][1]  # és l'última connexió feta
        time: float = 0
        cami: list[NodeID] = networkx.shortest_path(g1, c1, c2)
        i, long = 1, len(cami)
        for c in cami:
            if i == long:
                break
            time += street_time(G, G[c][cami[i]], "bus")
            i += 1

        G[p1][p2]["time"] = time

    for a, b in G.edges():
        if isinstance(a, Parada) and isinstance(b, Parada):
            continue
        else:
            G[a][b]["time"] = street_time(G, G[a][b], "peu")
    return G


def load_city_graph(filename) -> CityGraph:
    """"""

    G = pickle.load(open(filename, "rb"))
    return G


def build_city_graph(g1: OsmnxGraph, g2: BusesGraph) -> CityGraph:
    """Retorna un graf fusió de g1 i g2"""

    filename = "ciutat.grf"
    G = networkx.Graph()
    G.add_nodes_from(g1.nodes(data=True))
    G.add_nodes_from(g2.nodes(data=True))
    G.add_edges_from(g1.edges(data=True))
    G.add_edges_from(g2.edges(data=True))
    # juntem els dos grafs, de moment són disjunts.
    G = join_parada_cruilla(g1, g2, G)
    with open(filename, "wb") as f:
        pickle.dump(G, f)
    return G


def find_path(ox_g: OsmnxGraph, g: CityGraph, src: Coord, dst: Coord) -> Path:
    """Retorna el camí més curt fins al cinema"""

    sortida: NodeID = osmnx.nearest_nodes(ox_g, src[1], src[0])
    arribada: NodeID = osmnx.nearest_nodes(ox_g, dst[1], dst[0])

    return networkx.shortest_path(g, sortida, arribada, "time")


def bus_combination(
        p: Path, g: CityGraph) -> list[tuple[Parada, Linia]] | None:
    """Donat un camí, retorna una combinació de busos per arribar-hi."""

    i = 0
    steps: list[tuple[NodeID, NodeID, Linia | None]] = list()
    for n1, n2 in zip(p[:-1:], p[1::]):
        if isinstance(n1, Parada) and isinstance(n2, Parada):
            steps.append((n1, n2, g[n1][n2]["linies"]))
        else:
            steps.append((n1, n2, None))

    primer = True
    linies: set[Linia] = set()
    pujada: Parada | None = None
    nom_carrer = ""
    ultima_parada: Parada | None = None
    for step in steps:
        if step[2]:  # de parada a parada
            if primer:
                linies = step[2]
                primer = False
                pujada = step[0]
            if linies & step[2]:
                linies = linies & step[2]
                # coincidències de línies
            else:
                linia = linies.pop()
                print(f"Agafa l'autobús {linia} a {pujada}"
                      f" i baixa a {step[0]}", end=". ")
                linies = step[2]
                pujada = step[0]
            ultima_parada = step[1]
        else:
            if linies:
                linia = linies.pop()
                print(f"Agafa l'autobús {linia} a {pujada}"
                      f" i baixa a {ultima_parada}", end=". ")
                primer = True
                # O bé pot fer tot el recorregut amb un sol bus
                # o bé hi baixa i va caminant fins a una altra parada.
            if isinstance(step[0], Parada) and isinstance(step[0], int):
                continue  # necessitem dues cruilles per obtenir
                # el nom del carrer
            elif isinstance(step[0], int) and isinstance(step[0], Parada):
                print(f"Camina fins la parada {step[1]}", end=". ")
            else:
                try:
                    if nom_carrer != g[step[0]][step[1]]["name"]:
                        nom_carrer = g[step[0]][step[1]]["name"]
                        print(f"Camina fins {nom_carrer}", end=". ")
                except KeyError:
                    pass


def street_time(g: OsmnxGraph, info_carrer: tuple(), metode: str):
    """
    Donat un carrer dona una aproximació del temps que es triga a recórrer,
    a peu o amb bus.
    """

    temps: float
    if metode == "bus":
        if "maxspeed" in info_carrer:
            try:
                # passem a metres/minut i suposem que la velocitat no és màxima
                # tota la estona
                temps = info_carrer["length"] / \
                    (int(info_carrer["maxspeed"]) * (1000 / 60) * 0.55)
            except TypeError:
                velocitat_mitja = sum(int(
                    s) for s in info_carrer["maxspeed"]) / \
                    len(info_carrer["maxspeed"]) * (1000 / 60) * 0.55
                temps = info_carrer["length"] / velocitat_mitja
        else:
            temps = info_carrer["length"] / \
                (20 * (1000 / 60) * 0.55)

    else:
        # si no hi ha informació de la velocitat suposem 20kmh
        # caminant
        # suposem 5kmh mitjana velocitat caminant
        temps = info_carrer["length"] / (5 * (1000 / 60))
    return temps


def path_time(G: CityGraph, ox_g: OsmnxGraph, p: Path) -> int:
    """Retorna, en minuts, una aproximació de quant temps de trajecte hi ha."""

    temps: float = 0
    i, ll = 1, len(p)
    for node in p:
        if i == ll:
            break
        node2 = p[i]
        temps += G[node][node2]["time"]
        i += 1
    return temps


def show(g: CityGraph) -> None:
    """Mostra g de forma interactiva en una finestra."""

    positions = {node[0]: (node[1]["y"], node[1]["x"])
                 for node in g.nodes(data=True)}
    networkx.draw(g, pos=positions, node_size=1)
    plt.show()


def plot(g: CityGraph, filename: str) -> None:
    """
    Desa g com una imatge amb el mapa de la cuitat
    de fons en l'arxiu filename.
    """

    m = staticmap.StaticMap(600, 600)
    for con in g.edges():
        m.add_line(staticmap.Line(((
            g.nodes[con[0]]["x"], g.nodes[con[0]]["y"]), (
            g.nodes[con[1]]["x"], g.nodes[con[1]]["y"])), "red", 1))
        m.add_marker(staticmap.CircleMarker(
            (g.nodes[con[0]]["x"], g.nodes[con[0]]["y"]), "black", 1))
        m.add_marker(staticmap.CircleMarker(
            (g.nodes[con[1]]["x"], g.nodes[con[1]]["y"]), "black", 1))
    image = m.render()
    image.save(filename)


def plot_path(g: CityGraph, ox_g: OsmnxGraph, p: Path, filename: str) -> None:
    """
    Mostra el camí p en l'arxiu filename.
    Les parades i les rutes d'autbús apareixeran en color blau,
    mentre que el trajecte a peu sortirà en negre.
    """

    m = staticmap.StaticMap(800, 800)
    i, lr = 1, len(p)
    for node in p:
        if i == lr:
            break
        node2 = p[i]
        # si estem en un trajecte de bus, tracem a través de carrers i no
        # diagonal
        if isinstance(node, Parada) and isinstance(node2, Parada):
            c1: NodeID = list(g.edges(node))[-1][1]
            c2: NodeID = list(g.edges(node2))[-1][1]
            cami_bus: list[NodeID] = networkx.shortest_path(ox_g, c1, c2)
            j, l2 = 1, len(cami_bus)
            for cruilla in cami_bus:
                if j == l2:
                    break
                cruilla2 = cami_bus[j]
                m.add_line(
                    staticmap.Line(
                        ((g.nodes[cruilla]["x"],
                          g.nodes[cruilla]["y"]),
                            (g.nodes[cruilla2]["x"],
                             g.nodes[cruilla2]["y"])),
                        "blue",
                        2))
                j += 1
        # de cruïlla a cruïlla no hi ha cap problema
        else:
            m.add_line(
                staticmap.Line(
                    ((g.nodes[node]["x"],
                      g.nodes[node]["y"]),
                        (g.nodes[node2]["x"],
                         g.nodes[node2]["y"])),
                    "black",
                    2))
        if isinstance(node, Parada):
            m.add_marker(
                staticmap.CircleMarker(
                    (g.nodes[node]["x"], g.nodes[node]["y"]), "blue", 5))

        i += 1
    m.add_marker(staticmap.CircleMarker(
        (g.nodes[p[0]]["x"], g.nodes[p[0]]["y"]), "red", 6))
    m.add_marker(staticmap.CircleMarker(
        (g.nodes[p[-1]]["x"], g.nodes[p[-1]]["y"]), "green", 7))
    image = m.render()
    image.save(filename)


def filtra_adreca(adreca: str) -> str:
    """
    Donada una adreça,
    la modifica per a poguer ser usada per osmnx.geocode()
    """

    adreca = adreca.lower().replace(
        "calle",
        "carrer").replace(
        "sta.",
        "santa").replace(
            "st.",
            "sant").replace(
                "sta fé",
                "carrer de santa fe").replace(
                    " - centro comercial la maquinista",
                    "").replace("paseo",
                                "passeig").replace(
                                    "avenida",
                                    "avinguda").replace(
        "paseig",
        "passeig").replace(
        "s/n",
        "").replace(
        "  - pintor alzamora",
        "")

    return adreca


def coordenades(adreca: str) -> tuple[float, float] | None:
    """Donada una adreça, retorna les seves coordenades"""

    try:
        return osmnx.geocode(adreca)
    except ValueError:
        return None
