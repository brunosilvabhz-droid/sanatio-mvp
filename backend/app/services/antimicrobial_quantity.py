from decimal import Decimal, InvalidOperation


def calculate_product_quantity(dose_value, product) -> tuple[Decimal | None, str | None, Decimal | None, str | None]:
    if not product:
        return None, None, None, None
    try:
        dose = Decimal(str(dose_value or "").strip().replace(",", "."))
        components = [Decimal(part.strip().replace(",", ".")) for part in product.quantidade.split("/")]
    except (InvalidOperation, ValueError):
        return None, None, None, product.unidade_medida
    totals = [component * dose for component in components]
    display = "/".join(format(value.normalize(), "f") for value in totals)
    grams = None
    if len(totals) == 1:
        unit = product.unidade_medida.lower()
        if unit == "g":
            grams = totals[0]
        elif unit == "mg":
            grams = totals[0] / Decimal(1000)
        elif unit == "mcg":
            grams = totals[0] / Decimal(1000000)
    return dose, display, grams, product.unidade_medida
