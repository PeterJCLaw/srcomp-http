from setuptools import find_namespace_packages, setup

with open('README.rst') as f:
    long_description = f.read()

setup(
    name='sr.comp.http',
    version='1.3.0',
    packages=find_namespace_packages(exclude=('tests',)),
    namespace_packages=['sr', 'sr.comp'],
    package_data={'sr.comp.http': ['logging-*.ini']},
    long_description=long_description,
    author="Student Robotics Competition Software SIG",
    author_email="srobo-devel@googlegroups.com",
    install_requires=[
        'sr.comp >=1.2, <2',
        'Flask >=1.0, <2',
        'simplejson >=3.6, <4',
        'python-dateutil >=2.2, <3',
        'typing-extensions >=3.7.4.2, <4',
    ],
    python_requires='>=3.7',
    setup_requires=[
        'Sphinx >=1.3, <2',
    ],
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
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: WSGI :: Application',
    ],
    zip_safe=False,
)
