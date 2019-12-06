# kinda of configuration file
# should be a little database?

versions = {
    'oilsnszeus': ['00000000000000000000000000000001'],
    'gassnszeus': ['01000000000001010000000000000000'],
    'spdsnszeus': ['00001010101000000000000000000000'],
    'brksnszeus': ['00100000000000000000000000000000',
                   '10100000000000000000000000000000']
}

patches = {
    ('brksnszeus', '10100000000000000000000000000000'):
        'brake_patch_1-2.patch'
}

def get_latest_version(id_name):
    return versions[id_name][-1]

def get_patch_file(id_name, version):
    return patches[(id_name, version)]
