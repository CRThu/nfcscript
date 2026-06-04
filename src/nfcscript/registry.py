_REGISTRY = {
    "hardware": {},
    "driver": {},
    "card": {},
    "card_sak": {} # 映射 SAK -> card_name
}

def register(category, name, klass, sak=None):
    if category in _REGISTRY:
        _REGISTRY[category][name] = klass
        if category == "card" and sak is not None:
            _REGISTRY["card_sak"][sak] = name

def get(category, name):
    klass = _REGISTRY[category].get(name)
    if not klass:
        raise ValueError(f"Plugin '{name}' not found in category '{category}'")
    return klass

def get_name_by_sak(sak):
    return _REGISTRY["card_sak"].get(sak)
