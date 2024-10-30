from dataclasses import dataclass
import networkx
import staticmap
import requests
import json
from typing import TypeAlias, Optional
import matplotlib.pyplot as plt


BusesGraph: TypeAlias = networkx.Graph


@dataclass
class Parada:
    codAMB: str
    nom: str
    y: float
    x: float
    adreca: str

    def __hash__(self) -> int:
        return int(self.codAMB)

    def __repr__(self) -> str:
        return self.nom


@dataclass
class Linia:
    nom: str

    def __repr__(self) -> str:
        return f"{self.nom}"

    def __hash__(self) -> int:
        return sum(ord(c) for c in self.nom)

    def __eq__(self, other: object) -> bool:
        return self.nom == other.nom


def get_buses_graph() -> BusesGraph:
    """Crea i retorna un graf de busos de l'Àrea Metrolpolitana de Barcelona"""

    url = "https://www.ambmobilitat.cat/OpenData/ObtenirDadesAMB.json"
    info = requests.get(url)
    AMBdata = info.json()

    G: BusesGraph = networkx.Graph()

    for linia in AMBdata["ObtenirDadesAMBResult"]["Linies"]["Linia"]:
        # per a cada línia unim les seves parades
        nom: str = linia["Nom"]
        anterior: Parada | None = None
        for parada in linia["Parades"]["Parada"]:
            if parada["Municipi"].lower() == "barcelona":
                codAMB: str = parada["CodAMB"]
                par = Parada(
                    codAMB,
                    parada["Nom"],
                    parada["UTM_Y"],
                    parada["UTM_X"],
                    parada["Adreca"])
                G.add_node(par, y=parada["UTM_X"], x=parada["UTM_Y"])
                if anterior:
                    if G.has_edge(anterior, par):
                        G[anterior][par]["linies"].add(Linia(nom))
                        # si ja existeix la aresta afegim la línia de bus per
                        # tal de no sobreescriure informació
                    else:
                        G.add_edge(anterior, par, linies={Linia(nom)})
                        # si no, la creem.
                anterior: Parada = par

    return G


def show(g: BusesGraph) -> None:
    """Mostra el graf interactivament"""

    positions = {node: (node.x, node.y) for node in g.nodes()}
    networkx.draw(g, pos=positions, node_size=1)
    plt.show()


def plot(g: BusesGraph, nom_fitxer: str) -> None:
    """Desa el graf com una imatge amb el mapa de la ciutat de fons"""

    m = staticmap.StaticMap(600, 600)
    for con in g.edges():  # per a cada cada connexio
        m.add_line(staticmap.Line(((con[0].y, con[0].x), (
            con[1].y, con[1].x)), "red", 1))
        m.add_marker(staticmap.CircleMarker((con[0].y, con[0].x), "black", 2))
        m.add_marker(staticmap.CircleMarker((con[1].y, con[1].x), "black", 2))
    image = m.render()
    image.save(nom_fitxer)
