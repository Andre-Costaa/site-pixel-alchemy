"""
Pixel Alchemy — Cold Message Generator
========================================

Generates personalized outreach messages for prospects based on business niche.

Usage:
    from message_generator import generate_cold_message

    msg = generate_cold_message(
        nome="Dra. Laura Sanches",
        nicho="Dentista",
        slug="dra-laura-sanches",
        genero="feminino"  # ou "masculino", "neutro"
    )
"""

from config import SITE_DEMO_BASE_URL


def generate_cold_message(
    nome: str,
    nicho: str,
    slug: str,
    genero: str = "neutro"
) -> str:
    """Generate personalized cold message for a prospect.

    Args:
        nome: Business or professional name (e.g., "Dra. Laura Sanches")
        nicho: Business niche (e.g., "Dentista", "Veterinária", "Harmonização")
        slug: URL slug for the demo site
        genero: "masculino", "feminino", or "neutro" for pronoun selection

    Returns:
        Formatted cold message as a string
    """
    demo_url = f"{SITE_DEMO_BASE_URL}/{slug}/"

    # Pronoun selection
    pronouns = _get_pronouns(genero)

    # Niche-specific messaging
    subject_verb = _get_subject_verb(nicho, pronouns)
    service_type = _get_service_type(nicho)
    target_audience = _get_target_audience(nicho)

    # Build the message
    message = f"""Olá! Tudo bem? Sou o André, fundador da Pixel Alchemy.

Estávamos analisando a presença digital {subject_verb} e percebemos que {pronouns['vocês']} ainda não {pronouns['têm']} um website. Tomamos a liberdade de rascunhar um layout demo:

{demo_url}

O objetivo foi criar uma experiência que transmita mais autoridade e sofisticação aos {target_audience}. Adaptamos cada detalhe {pronouns['que queriam']}, com fotos reais, informações, {service_type} e depoimentos para que o site fique 100% fiel à identidade {pronouns['da clínica']}.

Se você gostar da linha visual e quiser um site para {nome}, podemos conversar 10 ou 15 minutinhos? Posso explicar e tirar dúvidas por aqui mesmo, caso prefira.

Abraços!"""

    return message.strip()


def _get_pronouns(genero: str) -> dict:
    """Get pronoun set based on gender."""
    if genero == "feminino":
        return {
            "vocês": "ela",
            "têm": "tem",
            "que queriam": "que queria",
            "da clínica": "do consultório dela"
        }
    elif genero == "masculino":
        return {
            "vocês": "ele",
            "têm": "tem",
            "que queriam": "que queria",
            "da clínica": "do consultório dele"
        }
    else:  # neutro - assume plural/empresa
        return {
            "vocês": "vocês",
            "têm": "têm",
            "que queriam": "que queriam",
            "da clínica": "da clínica"
        }


def _get_subject_verb(nicho: str, pronouns: dict) -> str:
    """Get the subject + verb for opening sentence."""
    niche_map = {
        "Dentista": "do consultório",
        "Veterinária": "da clínica veterinária",
        "Harmonização": "da clínica de estética",
        "Beleza": "do salão",
        "Pizzaria": "da pizzaria",
        "Barbearia": "da barbearia",
        "Padaria": "da padaria",
        "Açougue": "do açougue",
        "Pet Shop": "do pet shop",
    }
    return niche_map.get(nicho, "do negócio")


def _get_service_type(nicho: str) -> str:
    """Get the service type mention for the message."""
    service_map = {
        "Dentista": "serviços",
        "Veterinária": "serviços",
        "Harmonização": "tratamentos",
        "Beleza": "serviços",
        "Pizzaria": "cardápio",
        "Barbearia": "serviços",
        "Padaria": "produtos",
        "Açougue": "produtos",
        "Pet Shop": "serviços e produtos",
    }
    return service_map.get(nicho, "serviços")


def _get_target_audience(nicho: str) -> str:
    """Get the target audience for the message."""
    audience_map = {
        "Dentista": "seus pacientes",
        "Veterinária": "seus clientes",
        "Harmonização": "seus pacientes",
        "Beleza": "seus clientes",
        "Pizzaria": "seus clientes",
        "Barbearia": "seus clientes",
        "Padaria": "seus clientes",
        "Açougue": "seus clientes",
        "Pet Shop": "seus clientes",
    }
    return audience_map.get(nicho, "seus clientes")


def infer_genero_from_nome(nome: str) -> str:
    """Attempt to infer gender from name prefixes.

    Returns "feminino", "masculino", or "neutro" (default).
    """
    nome_lower = nome.lower()

    # Female indicators
    if any(prefix in nome_lower for prefix in ["dra.", "dra ", "dr. ", "doctora"]):
        return "feminino"

    # Male indicators
    if any(prefix in nome_lower for prefix in ["dr.", "dr ", "doctor"]):
        return "masculino"

    # Business names (no gendered prefix)
    return "neutro"


if __name__ == "__main__":
    # Test cases
    print("=== Test 1: Dra. Laura Sanches ===")
    msg1 = generate_cold_message(
        nome="Dra. Laura Sanches",
        nicho="Dentista",
        slug="dra-laura-sanches",
        genero=infer_genero_from_nome("Dra. Laura Sanches")
    )
    print(msg1)
    print()

    print("=== Test 2: Mairake Odontologia ===")
    msg2 = generate_cold_message(
        nome="Mairake Odontologia",
        nicho="Dentista",
        slug="mairake-odontologia",
        genero=infer_genero_from_nome("Mairake Odontologia")
    )
    print(msg2)
    print()

    print("=== Test 3: Dr. João Silva ===")
    msg3 = generate_cold_message(
        nome="Dr. João Silva",
        nicho="Veterinária",
        slug="dr-joao-silva",
        genero=infer_genero_from_nome("Dr. João Silva")
    )
    print(msg3)
