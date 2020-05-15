import os


def sort_keys_by_value_of_key(d, key, reverse=False):
    return [el[1] for el in sorted([(d[el][key], el) for el in d.keys()], reverse=reverse)]


def split_email_address(email_address):
    parts = email_address.split('@')
    if len(parts) != 2:
        raise ValueError('Not an email passed: %s' % email_address)
    return parts[0], parts[1]


def get_file_extension(git_file_path, max_ext_length=5):
    filename = os.path.basename(git_file_path)
    basename_parts = filename.split('.')
    ext = basename_parts[1] if len(basename_parts) == 2 and basename_parts[0] else ''
    if len(ext) > max_ext_length:
        ext = ''
    return ext
