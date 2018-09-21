version_info = (0, 1, 0, 'final', 0)

_specifier_ = {
    'alpha': 'a',
    'beta': 'b',
    'candidate': 'rc',
    'final': '',
}

subversion_specifier = ''
if version_info[3] != 'final':
    subversion_specifier = _specifier_[version_info[3]] + str(version_info[4])

__version__ = '%s.%s.%s%s' % (version_info[0],
                              version_info[1],
                              version_info[2],
                              subversion_specifier)
