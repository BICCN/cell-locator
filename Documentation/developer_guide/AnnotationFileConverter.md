# Annotation File Converter

Since some changes to the file format are backwards-incompatible, we provide a conversion
utility to update files to newer versions with sensible defaults for new values. The 
converter can also _downgrade_ file versions, although this is not as thoroughly-tested.

## Commands

### convert

See {py:func}`converters.match()` about target version strings.

```{eval-rst}
.. argparse::
    :module: cl_convert.convert
    :func: make_parser
    :prog: cl-file
    :path: convert
    :nodefault:
```

### versions

Show all versions and exit.

```{eval-rst}
.. argparse::
    :module: cl_convert.convert
    :func: make_parser
    :prog: cl-file
    :path: versions
    :nodefault:
```

### infer

Show inferred version of file and exit.

```{eval-rst}
.. argparse::
    :module: cl_convert.convert
    :func: make_parser
    :prog: cl-file
    :path: infer
    :nodefault:
```

## Converter API

### converters

```{eval-rst}
.. autoclass:: cl_convert.model.Converter
    :members:

.. autodecorator:: cl_convert.model.versioned

.. autoclass:: cl_convert.model.Document
    :members:
    :undoc-members:

.. autoclass:: cl_convert.model.Annotation
    :members:
    :undoc-members:

.. automodule:: cl_convert.converters
    :members:
```
