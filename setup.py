from setuptools import find_namespace_packages, setup

with open('README.rst') as f:
    long_description = f.read()

setup(
    name='sr.comp.http',
    version='1.9.0',
    url='https://github.com/PeterJCLaw/srcomp-http',
    project_urls={
        'Documentation': 'https://srcomp-http.readthedocs.org/',
        'Code': 'https://github.com/PeterJCLaw/srcomp-http',
        'Issue tracker': 'https://github.com/PeterJCLaw/srcomp-http/issues',
    },
    packages=find_namespace_packages(include=['sr.*']),
    namespace_packages=['sr', 'sr.comp'],
    package_data={'sr.comp.http': ['logging-*.ini']},
    description="HTTP API for Student Robotics Competition Software",
    long_description=long_description,
    author="Student Robotics Competition Software SIG",
    author_email="srobo-devel@googlegroups.com",
    install_requires=[
        'sr.comp >=1.5, <2',
        'Flask >=2.2',
        'Werkzeug >= 2, <4',
        'simplejson >=3.6, <4',
        'python-dateutil >=2.2, <3',
        'typing-extensions >=3.7.4.2, <5',
    ],
    python_requires='>=3.9',
    entry_points={
        'console_scripts': [
            'srcomp-update = sr.comp.http.update:main',
        ],
    },
    classifiers=[
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: WSGI :: Application',
    ],
    zip_safe=False,
)
