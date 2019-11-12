def sort_keys_by_value_of_key(d, key, reverse=False):
    return [el[1] for el in sorted([(d[el][key], el) for el in d.keys()], reverse=reverse)]


def split_email_address(email_address):
    parts = email_address.split('@')
    if len(parts) != 2:
        raise ValueError('Not an email passed: %s' % email_address)
    return parts[0], parts[1]
