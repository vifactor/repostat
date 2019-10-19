
def sort_keys_by_value_of_key(d, key):
    return [el[1] for el in sorted([(d[el][key], el) for el in d.keys()])]
