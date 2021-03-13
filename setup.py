from setuptools import setup, find_namespace_packages


with open("ziopy/VERSION") as version_file:
    version = version_file.read().strip()

kwds = {}
try:
    kwds['long_description'] = open('README.md').read()
    kwds['long_description_content_type'] = 'text/markdown'
except IOError:
    pass

setup(
    name="zio_py",
    version=version,
    author="William Harvey",
    author_email="drwjharvey@gmail.com",
    license='MIT License',
    description="Python port of Scala ZIO for pure functional programming",
    url="https://github.com/miiohio/ziopy",
    packages=["ziopy"] + find_namespace_packages(include=["ziopy.*"]),
    package_data={"ziopy": ["VERSION", "py.typed"]},
    package_dir={"zio_py": "ziopy"},
    install_requires=[
        "dataclasses; python_version<'3.7'",
    ],
    **kwds
)
