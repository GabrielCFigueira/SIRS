# kinda of configuration file
# should be a little database?

versions = {'0123456789': ["ola01234567890123456789012345678"]}

patches = {('0123456789', 'ola01234567890123456789012345678'): 'test.patch'}

def get_latest_version(id_name):
    return versions[id_name][-1]

def get_patch_file(id_name, version):
    return patches[(id_name, version)]
