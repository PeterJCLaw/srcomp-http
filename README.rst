SR Comp HTTP
============

|Build Status| |Docs Status|

A HTTP interface around `SRComp <https://github.com/PeterJCLaw/srcomp/wiki/SRComp>`__,
the fifth round of `Student Robotics <http://srobo.org>`__ competition
software.

This repository provides a JSON API to accessing information about the
state of the competition. It is a lightweight
`Flask <http://flask.pocoo.org/>`__ application wrapping the
`SRComp <https://github.com/PeterJCLaw/srcomp>`__ python
APIs to the competition state.

Usage
-----

**Install**:

.. code:: shell

    pip install sr.comp.http

**Configuration**

In deployment you should configure the app by setting the ``COMPSTATE`` key of
the app's config to the absolute path of the compstate which the server intends
to serve.

.. code:: python

    from sr.comp.http import app
    app.config['COMPSTATE'] = '/path/to/compstate'

Development
-----------

**Install**:

.. code:: shell

    pip install -e .

**Run**:
``./run $COMPSTATE``.

**Test**:
``./run-tests``

Developers may wish to use the `SRComp Dev`_ repo to setup a dev instance.

State Caching
~~~~~~~~~~~~~

Since loading a given state repo takes a non-trivial amount of time,
this is cached within the Flask application. Updates to the state repo
are not tracked directly, and must be signalled by running the
``./update`` script provided.


.. |Build Status| image:: https://circleci.com/gh/PeterJCLaw/srcomp-http.svg?style=svg
   :target: https://circleci.com/gh/PeterJCLaw/srcomp-http

.. |Docs Status| image:: https://readthedocs.org/projects/srcomp-http/badge/?version=latest
   :target: https://srcomp-http.readthedocs.org/

.. _`SRComp Dev`: https://github.com/PeterJCLaw/srcomp-dev
