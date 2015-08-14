import argparse
import functools
import os
from bottle import Bottle, run, abort, jinja2_view, static_file


SCRIPT_ROOT = os.path.dirname(os.path.realpath(__file__))
ROOT = os.getcwd()

app = Bottle()
view = functools.partial(jinja2_view, template_lookup=[
    os.path.join(SCRIPT_ROOT, 'templates')
])


class FileSystemManager(object):

    def __init__(self, root, relative_path):
        self.root = root
        self.relative_path = relative_path
        self.absolute_path = self._path_join(root, relative_path)

    def _get_item(self, filename):
        path = self._path_join(self.absolute_path, filename)
        normpath = self._normpath(path)
        is_file = self.isfile(normpath)
        return dict(
            name=filename,
            is_file=is_file,
            new_tab=is_file and filename[-4:].lower() == '.xml',
            link=self._normpath(self._path_join('/', self.relative_path, filename))
        )

    def _get_items(self):
        items = map(self._get_item, self._listdir())
        items.sort(key=lambda item: item['name'])
        items.sort(key=lambda item: item['is_file'])
        parent = self._get_item('..')
        items.insert(0, parent)
        return items

    def _listdir(self, path=None):
        return os.listdir(path or self.absolute_path)

    def _normpath(self, path):
        return os.path.normpath(path)

    def _path_exists(self, *args, **kwargs):
        return os.path.exists(*args, **kwargs)

    def _path_join(self, *args, **kwargs):
        return os.path.join(*args, **kwargs)

    def _path_split(self, *args, **kwargs):
        return os.path.split(*args, **kwargs)

    def exists(self):
        return self._path_exists(self.absolute_path)

    def isdir(self):
        return os.path.isdir(self.absolute_path)

    def isfile(self, absolute_path=None):
        return os.path.isfile(absolute_path or self.absolute_path)

    def islink(self):
        return os.path.islink(self.absolute_path)

    def show_dir(self):
        return dict(path=self.relative_path,
                    items=self._get_items())

    def show_file(self):
        head, tail = self._path_split(self.absolute_path)
        if tail[-4:].lower() == '.xml':
            return static_file(tail, root=head, mimetype='text/xml')
        else:
            return static_file(tail, root=head, download=tail)


@app.route('/')
@app.route('/<path:path>')
@view('ls.html')
def view(path='./'):
    manager = FileSystemManager(ROOT, path)
    if manager.exists():
        if manager.islink():
            abort(401, "Sorry, didn't allow symbolic links.")
        elif manager.isdir():
            return manager.show_dir()
        elif manager.isfile():
            return manager.show_file()
    else:
        abort(401, "Sorry, access denied.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Serve files in current directory.')
    parser.add_argument('-H', '--host', type=str, help='specify host for listening')
    parser.add_argument('-P', '--port', type=int, help='specify port for listening')
    args = parser.parse_args()
    run(app, host=args.host or 'localhost', port=args.port or 8080)

