#!/bin/bash

python_version=3.7.6

set -e

script_dir=$(dirname $0)
if [ $script_dir = '.' ]
then
script_dir="$(pwd)"
fi
pushd $script_dir > /dev/null

# Prerequisite:  Make sure that we have pyenv installed.  If not, then exit.
echo "Ensuring that pyenv is installed..."
command -v pyenv >/dev/null 2>&1 || {
    echo >&2 "Error:  pyenv does not appear to be installed."
    echo >&2 "        Please follow the installation instructions here before running this script:"
    echo >&2 "        https://github.com/pyenv/pyenv#installation"
    exit 1
}
echo "Done."

# Use pyenv to install the prescribed version of Python.
echo "Using pyenv to install the prescribed version of Python ($python_version)..."
pyenv install $python_version --skip-existing >/dev/null 2>&1 || {
    echo >&2 "Error:  Unable to install Python version $(cat .python-version) using pyenv.";
    echo >&2 "        Try updating pyenv by running:     ";
    echo >&2 "                                           ";
    echo >&2 "        brew update && brew upgrade pyenv"
    exit 1
}
echo "Done."

pyenv local $python_version

# Create a virtual environment for this project.
virtualenv_name=venv-$(basename $script_dir)

echo "Creating a virtual environment for this project called $virtualenv_name..."
mkdir -p .$virtualenv_name/
python -m venv .$virtualenv_name
echo "Done."

# Activate the virtual environment
echo "Activating the virtual environment..."
source .$virtualenv_name/bin/activate
echo "Done."

echo "Upgrading pip..."
pip install --upgrade pip
echo "Done."

echo "Installing requirements.txt..."
pip install -U -r requirements.txt
echo "Done."

echo "Installing requirements-dev.txt..."
pip install -U -r requirements-dev.txt
echo "Done."

echo "
Setup succeeded!

  - Now run 'source .$virtualenv_name/bin/activate' in the shell to activate the
    virtual environment.

  - Run 'deactivate' to exit the virtual environment."

popd > /dev/null
