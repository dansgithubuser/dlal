def peruse(path, file_name=None, file_ext='.txt'):
    if not file_name:
        return os.listdir(path)
    if os.path.split(file_name)[1] == file_name:
        file_name = os.path.join(path, file_name)
    if not file_name.endswith(file_ext):
        file_name += file_ext
    return file_name
