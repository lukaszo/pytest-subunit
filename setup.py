from setuptools import setup

setup(
    name='pytest-subunit',
    description=(
        'pytest-subunit is a plugin for py.test which outputs tests'
        'result in subunit format.'
    ),
    long_description="",
    version='0.0.1',
    license='Apache 2',
    author='Łukasz Oleś',
    author_email='loles@mirantis.com',
    py_modules=['pytest_subunit'],
    entry_points={'pytest11': ['subunit = pytest_subunit']},
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    install_requires=['pytest>=2.3'],
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache-2 License',
        'Operating System :: POSIX',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: MacOS :: MacOS X',
        'Topic :: Software Development :: Testing',
        'Topic :: Software Development :: Libraries',
        'Topic :: Utilities',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
    ]
)
