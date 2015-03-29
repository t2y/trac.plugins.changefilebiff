#!/usr/bin/env python
# -*- coding: utf-8 -*-
from setuptools import setup

VERSION = '0.4.0'

try:
    import pypandoc  
    LONG_DESCRIPTION = '\n'.join([
        pypandoc.convert('README.md', 'rst'),
        pypandoc.convert('CHANGELOG.md', 'rst'),
    ])
except (IOError, ImportError):
    LONG_DESCRIPTION = ''

REQUIRES = [
    'Trac >= 1.0',
]

EXTRAS_REQUIRE = {
    'gitignore': [
        'pathspec >= 0.3',
    ],
}

CLASSIFIERS = [
    'Framework :: Trac',
    'Development Status :: 4 - Beta',
    'Environment :: Web Environment',
    'License :: OSI Approved :: Apache Software License',
    'Intended Audience :: Developers',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    'Topic :: Software Development',
]

EXTRA_PARAMETER = {}
try:
    # Adding i18n/l10n to Trac plugins (Trac >= 0.12)
    # see also: http://trac.edgewall.org/wiki/CookBook/PluginL10N
    from trac.util.dist import get_l10n_cmdclass
    cmdclass = get_l10n_cmdclass()
    if cmdclass:  # Yay, Babel is there, we've got something to do!
        EXTRA_PARAMETER['cmdclass'] = cmdclass
        EXTRA_PARAMETER['message_extractors'] = {
            'changefilebiff': [
                ('**.py', 'python', None),
                ('**/templates/**.html', 'genshi', None),
                ('**/templates/**.txt',  'genshi', {
                    'template_class': 'genshi.template:TextTemplate',
                }),
            ]
        }
except ImportError:
    pass

setup(
    name='TracChangeFileBiffPlugin',
    version=VERSION,
    description='Provides a feature like Biff for file in repository',
    long_description=LONG_DESCRIPTION,
    classifiers=CLASSIFIERS,
    keywords=['trac', 'plugin', 'ticket', 'changeset', 'biff'],
    author='Tetsuya Morimoto',
    author_email='tetsuya dot morimoto at gmail dot com',
    url='http://trac-hacks.org/wiki/TracChangeFileBiffPlugin',
    license='Apache License 2.0',
    packages=['changefilebiff'],
    package_data={
        'changefilebiff': [
            'htdocs/*.js',
            'htdocs/*.css',
            'locale/*/LC_MESSAGES/*.po',
            'locale/*/LC_MESSAGES/*.mo',
        ],
    },
    include_package_data=True,
    install_requires=REQUIRES,
    extras_require=EXTRAS_REQUIRE,
    entry_points={
        'trac.plugins': [
            'changefilebiff.admin = changefilebiff.admin',
            'changefilebiff.api = changefilebiff.api',
            'changefilebiff.model = changefilebiff.model',
        ]
    },
    **EXTRA_PARAMETER
)
