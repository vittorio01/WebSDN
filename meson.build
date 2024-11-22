project('GTKSDNManager')

# Importing modules
python = import('python')

# Module objects
py_installation = python.find_installation('python3')

# Make sure Python is installed and found
if not py_installation.found()
    error('No valid python3 binary found')
endif

# Python 3.7 is needed for postponed evalution of annotations
if not py_installation.language_version().version_compare('>= 3')
  error('Python 3 or newer is required.')
endif

dependency('gtk4')

#install_data('src/controller/controller.py', install_dir: get_option('bindir'))