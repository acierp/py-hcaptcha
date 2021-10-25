from . import hsl
from . import hsw

def get_proof(type, data):
    if type == "hsl":
        return hsl.get_proof(data)
    elif type == "hsw":
        return hsw.get_proof(data)
    else:
        raise Exception(f"Unrecognized proof type '{type}'")