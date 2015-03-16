Notes
=====

[TracChangeFileBiffPlugin](https://trac-hacks.org/wiki/TracChangeFileBiffPlugin "TracChangeFileBiffPlugin")
is useful to query or monitor certain file in the repository when someone will update it.

Note: TracChangeFileBiffPlugin requires Trac 1.0 or higher since it uses
the **list** format of text type. ([TracTicketsCustomFields](http://trac.edgewall.org/wiki/TracTicketsCustomFields "TracTicketsCustomFields"))


Features
--------

* Provides a feature like [Biff](http://en.wikipedia.org/wiki/Biff "Biff") for file in repository


Configuration
=============

* Enable TracChangeFileBiffPlugin in Plugins page.

* **Access to File Biff admin panel**

  The option of `ticket-custom` section would be added when you access to File Biff admin page like this.

    [ticket-custom]
    filebiff = text
    filebiff.format = list
    filebiff.label = Biff       ; change filed label as you like
    filebiff.multiple = true    ; this option is used by TracMultiSelectBoxPlugin
    filebiff.options =          ; will be set when you configure File Biff settings
    filebiff.size = 3           ; this option is used by TracMultiSelectBoxPlugin
    filebiff.matching_pattern = fnmatch ; glob matching pattern (fnmatch or gitignore)

* **Configure a File Biff settings**

  Specification:

    * White-space is not allowed to include into Name
    * Cc and Filename are configured multiple values separated by comma.
    * The glob pattern for Filename is allowed
    * The glob pattern is configurable in `filebiff.matching_pattern` of `[ticket-custom]`. The possible values are (default: `fnmatch`):
        * `fnmatch`: standard glob pattern by [fnmatch module](https://docs.python.org/2/library/fnmatch.html "fnmatch module").
        * `gitignore`: gitignore sytle pattern by [pathspec library](https://pypi.python.org/pypi/pathspec/ "pathspec library").

  Added `[changefilebiff]` section after you configured File Biff settings like this.

    [changefilebiff]
    biff.2e320ca20d1aed6a.cc = user1
    biff.2e320ca20d1aed6a.filename = *.txt, *.text
    biff.2e320ca20d1aed6a.name = text-files
    biff.319ddde3cb437ffc.cc = user2, guest1
    biff.319ddde3cb437ffc.filename = *.properties
    biff.319ddde3cb437ffc.name = property-files
    biff.dd487b83e5e76d08.cc = user1, user2
    biff.dd487b83e5e76d08.filename = *.gif, *.png, *.jpg
    biff.dd487b83e5e76d08.name = Image-files
    biff_keys = dd487b83e5e76d08, 319ddde3cb437ffc, 2e320ca20d1aed6a


Operation Tips
==============

integrate TracMultiSelectBoxPlugin
----------------------------------

To integrate [TracMultiSelectBoxPlugin](https://trac-hacks.org/wiki/TracMultiSelectBoxPlugin "TracMultiSelectBoxPlugin") is good practice for ticket maintenance like this.

