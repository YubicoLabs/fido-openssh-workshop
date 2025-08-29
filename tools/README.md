This directory contains several Python tools used in the exercises.
To not interfere with how Python is installed on your system, use a Python virtual environment.

# Install a Python virtual environment

- Create a Python virtual environment:

```
python3 -m venv venv
```

- Activate the virtual environment:

```
source venv/bin/activate
```

- Install dependencies:

```
pip install requests fido2 PyYAML
```

You should now be able to run the Python tools in this directory.
