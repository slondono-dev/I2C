"""Versioned prompt registry. Keep all prompts here, never scattered in code."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Prompt:
    key: str
    version: str
    system: str
    template: str

    def render(self, **kwargs: object) -> str:
        return self.template.format(**kwargs)


_PROMPTS: dict[str, Prompt] = {}


def register(prompt: Prompt) -> Prompt:
    _PROMPTS[prompt.key] = prompt
    return prompt


def get_prompt(key: str) -> Prompt:
    return _PROMPTS[key]


register(
    Prompt(
        key="product_recognition",
        version="v1",
        system=(
            "Eres un asistente experto en catalogación de productos de moda y retail. "
            "Analizas fotos tomadas con celular y extraes atributos visuales. "
            "No intentes identificar marcas, modelos ni SKU reales."
        ),
        template=(
            "Analiza la imagen del producto y devuelve SOLO un objeto JSON con estas claves: "
            "category (ej: camiseta, pantalón, vestido, zapatos, bolso, accesorio), "
            "subcategory, color (nombre comercial corto en español, ej: ivory, negro, "
            "azul marino), "
            "gender (mujer|hombre|unisex|niño|niña|null), "
            "sleeve (corta|larga|sin mangas|3/4|null), "
            "neck (redondo|v|polo|alto|null), fit (slim|regular|oversize|null), "
            "pattern (liso|rayas|estampado|cuadros|floral|null), material (si es evidente o null), "
            "confidence (0 a 1). Usa null cuando no aplique o no sea visible."
        ),
    )
)

register(
    Prompt(
        key="product_name",
        version="v1",
        system="Eres copywriter de una marca de moda. Respondes solo con el texto pedido.",
        template=(
            "Genera un nombre comercial corto (2 a 4 palabras, en español, sin comillas) "
            "para un producto con estos atributos: {attributes}. "
            "Ejemplo de estilo: 'Camiseta Essential Ivory'. Responde solo con el nombre."
        ),
    )
)

register(
    Prompt(
        key="product_description",
        version="v1",
        system="Eres copywriter de una marca de moda. Escribes textos breves y vendedores.",
        template=(
            "Escribe una descripción comercial en español de entre 25 y 40 palabras para "
            "'{name}' con atributos: {attributes}. Sin hashtags, sin emojis, sin listas. "
            "Responde solo con la descripción."
        ),
    )
)
