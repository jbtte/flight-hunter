from duffel_api import Duffel
import os


def buscar_passagem_dinamica(origem, destino, data_ida, data_volta):
    """
    Busca na Duffel usando os parâmetros passados pelo orquestrador.
    Client instanciado por chamada para garantir thread-safety no executor.
    """
    client = Duffel(access_token=os.getenv("DUFFEL_TOKEN"), api_version="v2")
    try:
        offer_request = (
            client.offer_requests.create()
            .slices([
                {
                    "origin": origem,
                    "destination": destino,
                    "departure_date": data_ida,
                },
                {
                    "origin": destino,
                    "destination": origem,
                    "departure_date": data_volta,
                },
            ])
            .passengers([{"type": "adult"}])
            .cabin_class("economy")
            .return_offers()
            .execute()
        )

        offers = offer_request.offers
        if not offers:
            return None

        melhor = min(offers, key=lambda o: float(o.total_amount))

        return {
            "preco": float(melhor.total_amount),
            "moeda": melhor.total_currency,
            "companhia": melhor.owner.name,
        }
    except Exception as e:
        print(f"Erro Duffel ({origem}-{destino}): {e}")
        return None
