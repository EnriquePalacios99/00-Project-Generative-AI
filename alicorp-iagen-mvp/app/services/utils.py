def parse_attrs(text:str)->dict:
    out={}
    for part in text.split(";"):
        if ":" in part:
            k,v=part.split(":",1)
            out[k.strip()] = v.strip()
    return out
