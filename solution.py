
import os
import requests
import folium

TOKEN = os.getenv("SPTRANS_TOKEN")

if not TOKEN:
    raise RuntimeError("Defina a variável de ambiente SPTRANS_TOKEN.")
BASE_URL = "https://api.olhovivo.sptrans.com.br/v2.1"
BUSCA_LINHA = "875A" 
BUSCA_PARADA = "TERMINAL" 

sessao = requests.Session()

def consultar_api(endpoint, params=None):
    """Consulta a API da SPTrans."""
    url = f"{BASE_URL}/{endpoint}"
    resposta = sessao.get(url, params=params, timeout=30)
    resposta.raise_for_status()
    return resposta.json()

resposta = sessao.post(
    f"{BASE_URL}/Login/Autenticar",
    params={"token": TOKEN},
    timeout=30
)
resposta.raise_for_status()

if resposta.json() is not True:
    raise RuntimeError("Falha na autenticação. Confira seu token.")

print("Autenticação realizada com sucesso!")

linhas = consultar_api(
    "Linha/Buscar",
    {"termosBusca": BUSCA_LINHA}
)

if not linhas:
    raise RuntimeError("Nenhuma linha encontrada. Altere BUSCA_LINHA.")

linha = linhas[0]
codigo_linha = linha["cl"]

print("Linha selecionada:", linha.get("lt", BUSCA_LINHA))

paradas = consultar_api(
    "Parada/BuscarParadasPorLinha",
    {"codigoLinha": codigo_linha}
)
posicoes = consultar_api(
    "Posicao/Linha",
    {"codigoLinha": codigo_linha}
)

veiculos = posicoes.get("vs", [])
print("Resposta de posições:", posicoes)

coordenadas = []

for parada in paradas:
    latitude = parada.get("py")
    longitude = parada.get("px")

    if latitude is not None and longitude is not None:
        coordenadas.append((latitude, longitude))

for veiculo in veiculos:
    latitude = veiculo.get("py")
    longitude = veiculo.get("px")

    if latitude is not None and longitude is not None:
        coordenadas.append((latitude, longitude))

if not coordenadas:
    raise RuntimeError(
        "Não foram encontradas coordenadas para criar o mapa."
    )

centro_lat = sum(p[0] for p in coordenadas) / len(coordenadas)
centro_lon = sum(p[1] for p in coordenadas) / len(coordenadas)

mapa = folium.Map(
    location=[centro_lat, centro_lon],
    zoom_start=13,
    tiles=None
)

for parada in paradas:
    latitude = parada.get("py")
    longitude = parada.get("px")

    if latitude is not None and longitude is not None:
        folium.Marker(
            location=[latitude, longitude],
            popup=parada.get("np", "Parada de ônibus"),
            tooltip=parada.get("np", "Parada"),
            icon=folium.Icon(color="blue", icon="info-sign")
        ).add_to(mapa)

for veiculo in veiculos:
    latitude = veiculo.get("py")
    longitude = veiculo.get("px")

    if latitude is not None and longitude is not None:
        folium.Marker(
            location=[latitude, longitude],
            popup=f"Ônibus prefixo: {veiculo.get('p', 'N/I')}",
            tooltip=f"Ônibus {veiculo.get('p', '')}",
            icon=folium.Icon(color="red", icon="bus")
        ).add_to(mapa)

mapa.save("mapa_onibus.html")

print("Mapa criado: mapa_onibus.html")
print("Quantidade de paradas:", len(paradas))
print("Quantidade de ônibus encontrados:", len(veiculos))
