import functools
import os
from bottle import Bottle, run, abort, jinja2_view, static_file


app = Bottle()
view = functools.partial(jinja2_view, template_lookup=['templates'])
ROOT = os.getcwd()


def get_items(path, abs_path):
    items = []
    for i, item in enumerate(os.listdir(abs_path)):
        is_file = os.path.isfile(os.path.join(abs_path, item))
        items.append(dict(
            name=item,
            is_file=is_file,
            new_tab=is_file and item[-4:].lower() == '.xml',
            link=os.path.join(path, item)
        ))
    items.sort(key=lambda item: item['name'])
    items.sort(key=lambda item: item['is_file'])
    print(os.path.split(path))
    parent = dict(
        name='../',
        is_file=False,
        new_tab=False,
        link='/' + os.path.split(path)[0])
    items.insert(0, parent)
    return items


@app.route('/')
@app.route('/<path:path>')
@view('ls.html')
def view(path='./'):
    abs_path = os.path.join(ROOT, path)
    if os.path.exists(abs_path):
        if os.path.isdir(abs_path):
            return dict(
                path=path, 
                items=list(get_items(path, abs_path))
            )
        elif os.path.isfile(abs_path):
            head, tail = os.path.split(abs_path)
            if abs_path[-4:].lower() == '.xml':
                return static_file(tail, root=head, mimetype='text/xml')
            else:
                return static_file(tail, root=head, download=tail)
    else:
        abort(401, "Sorry, access denied.")


run(app, host='localhost', port=8080)

