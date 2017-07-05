""" Collection of methods that don't yet have a home
"""
import os


def diriter(root_dir):
    """ grab files from root/sub dirs having extension
    """
    return ((f, os.path.join(root, f))
            for root, dirs, files in os.walk(root_dir)
            for f in files)


def commafix(root_dir):

    def clean(line):
        """ remove trailing commas from line
        """
        return [line[:-1].rstrip(',')
                for line in lines]

    for fn, fp in diriter(root_dir):
        if fn.lower() == 'results.csv':
            lines = open(fp, 'r').readlines()
            content = '\n'.join(clean(lines))
            open(fp, 'w').write(content)


if __name__ == '__main__':
    commafix('../data/test3')
