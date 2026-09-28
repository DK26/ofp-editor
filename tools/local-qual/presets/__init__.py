"""Harness presets for the local-qual runner (D048; doc 55 section 3).

This folder holds data and one checker, not runner code:

* ``schema/harness-preset.schema.json``: the preset format (JSON Schema 2020-12, draft 2 of doc 55 section 3.3).
* ``drafts/*.preset.json``: draft presets, each an untested hypothesis (status ``draft``).
* ``lint.py``: the standard-library checker (schema subset validator, base resolution, the loader rules the schema
  cannot express); ``python tools/local-qual/presets/lint.py [FILE ...]`` checks files, and run_preset.py loads a
  preset through it for ``run.py --preset``.

It is a package only so that run_preset.py and the tests can ``from presets import lint``.
"""
