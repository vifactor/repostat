import os


def split_email_address(email_address):
    parts = email_address.split('@')
    if len(parts) != 2:
        raise ValueError('Not an email passed: %s' % email_address)
    return parts[0], parts[1]


def get_file_extension(filepath: str):
    assert filepath
    filename = os.path.basename(filepath)
    basename_parts = filename.split('.')
    if len(basename_parts) == 1:
        # 'folder/filename'-case
        return filename
    elif len(basename_parts) == 2 and not basename_parts[0]:
        # 'folder/.filename'-case
        return filename
    else:
        # "normal" case
        return basename_parts[-1]
