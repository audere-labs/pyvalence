import os


def diriter(root_dir):
    ''' grab files from root/sub dirs having extension
    '''
    return ((f, os.path.join(root, f))
            for root, dirs, files in os.walk(root_dir)
            for f in files)
