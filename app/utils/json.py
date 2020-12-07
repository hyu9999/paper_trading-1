from typing import Optional

import ujson


def json_encoder(
    obj: dict,
    include: Optional[set] = None,
    exclude: Optional[set] = None,
):
    if include and exclude:
        raise ValueError("")
    if include:
        dict_obj = {k: v for k, v in obj.items() if k in include}
    elif exclude:
        dict_obj = {k: v for k, v in obj.items() if k not in exclude}
    else:
        dict_obj = obj
    return ujson.dumps(dict_obj)
