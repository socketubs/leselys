Leselys
=======

I'm Leselys, your very elegant RSS reader. Try me `right now`_ (password: demo)!

No `bullshit apps`_ for Android, iPhone, etc. Just a responsive design and for every device.

Leselys is Heroku ready.

.. image:: https://dl.dropboxusercontent.com/u/79447684/Github/Leselys/screenshot_01.png
.. image:: https://dl.dropboxusercontent.com/u/79447684/Github/Leselys/screenshot_02.png

Installation
------------

Ubuntu
~~~~~~

Two requirements: **Mongodb** and **Python**.

In order to install leselys you'll need some dependencies: ::

  sudo apt-get install build-essential python-dev python-setuptools
  sudo apt-get install libxslt1-dev libxml2-dev
  sudo easy_install pip
  sudo easy_install virtualenv

And install your `MongoDB`_.

This is the right way, with ``virtualenv``:

::

  mkdir leselys && cd leselys
  virtualenv .
  source bin/activate
  pip install leselys
  leselys init leselys.ini
  leselys serve leselys.ini
  # In another terminal (in leselys directory)
  source bin/activate
  leselys worker leselys.ini

Open your browser at ``http://localhost:5000``.


Heroku
~~~~~~

Advanced setup with MongoDB for storage and Redis for session on Heroku.
You will also need the Heroku Scheduler add-on to refresh your feeds.

All Heroku dependencies like ``Pymongo``, ``gunicorn`` and ``redis`` are in ``requirements.txt`` file, so everything will be installed automagically.

::

  git clone git@github.com:socketubs/leselys.git
  cd leselys
  heroku create
  heroku addons:add mongohq:sandbox
  heroku addons:add redistogo:nano
  heroku addons:add scheduler:standard
  heroku addons:open scheduler
  # Add "sh heroku.sh && leselys refresh heroku.ini" job every 10 minutes
  # And "sh heroku.sh && leselys retention heroku.ini" job every day
  git push heroku master

Import your Google Reader OPML file right now!

Update
------

This is how to update your Leselys (on Heroku): ::

  git pull
  git push heroku master
  heroku restart

And for the ``pip`` way, you just have to go to your ``virtualenv`` and run ``pip install leselys -U`` and restart Leselys processes.

Misc
----

Storage and session backends are Python modules, you can easily write your own. Take a look at the `MongoDB storage backend`_.

Leselys automagically fetch new stories with it's refresher worker, and automagically (again), purge our stories database with it's retention task.

Python 3 support is available, there is just ``worker`` with celery which doesn't work correctly. You can schedule the task with refresh and retention commands.
Python 3 is automatically used on Heroku.

License
-------

License is `AGPL3`_. See `LICENSE`_.

.. _MongoDB: http://docs.mongodb.org/manual/installation/
.. _bullshit apps: http://tommorris.org/posts/8070
.. _right now: https://leselys.herokuapp.com
.. _MongoDB storage backend: https://github.com/socketubs/leselys/blob/master/leselys/backends/storage/_mongodb.py
.. _Ubuntu: https://github.com/socketubs/leselys/wiki/Ubuntu
.. _Heroku: https://github.com/socketubs/leselys/wiki/Heroku
.. _AGPL3: http://www.gnu.org/licenses/agpl.html
.. _LICENSE: https://raw.github.com/socketubs/leselys/master/LICENSE
