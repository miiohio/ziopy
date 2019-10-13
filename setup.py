from distutils.core import setup
setup(
    name = 'zio_py',
    packages = ['zio_py'],
    version = '0.0.2a',
    license='Apache license 2.0',
    description = 'Python port of Scala ZIO for pure functional programming',
    author = 'William Harvey',
    author_email = 'drwjharvey@gmail.com',
    url = 'https://github.com/harveywi/ziopy',
    download_url = 'https://github.com/harveywi/ziopy/archive/0.0.2a.tar.gz',
    keywords = ['ZIO', 'IO', 'monads', 'pure fp', 'functional programming',
                'monad syntax'],
    install_requires=[
        'macropy3==1.1.0b2'
    ],
    python_requires='==3.7',
    classifiers=[
      'Development Status :: 3 - Alpha',
      'Intended Audience :: Developers',
      'Topic :: Software Development :: Libraries :: Python Modules',
      'License :: OSI Approved :: Apache Software License',
      'Programming Language :: Python :: 3.7'
    ]
)
