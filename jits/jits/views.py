from pyramid.response import Response
from pyramid.view import view_config, view_defaults

from sqlalchemy.exc import DBAPIError

from .models import (
    DBSession,
    Person,
    )


@view_config(route_name='home', renderer='templates/mytemplate.jinja2')
def home(request):
    return {}


@view_defaults(renderer='json')
class PersonView(object):

    def __init__(self, request):
        self.request = request

    @view_config(route_name='person-list', request_method='POST')
    def add(self):
        post = self.request.json_body

        errors = {}
        if DBSession.query(Person).filter_by(name=post['name']).count():
            errors['name'] = 'Person with name "{}" already exists.'.format(post['name'])
        if DBSession.query(Person).filter_by(email=post['email']).count():
            errors['email'] = 'Person with email "{}" already exists.'.format(post['email'])
        if DBSession.query(Person).filter_by(phone=post['phone']).count():
            errors['phone'] = 'Person with phone "{}" already exists.'.format(post['phone'])

        if errors:
            post['errors'] = errors
            self.request.response.status_code = 403
            return post

        person = Person(**post)
        DBSession.add(person)
        self.request.response.status_code = 201
        return self.request.response

    @view_config(route_name='person', request_method='DELETE')
    def delete(self):
        query = DBSession.query(Person).filter_by(id=self.request.matchdict['id'])
        if query.count():
            query.delete()
            status_code = 204
        else:
            status_code = 404
        self.request.response.status_code = status_code
        return self.request.response

    @view_config(route_name='person-list', request_method='GET')
    def list(self):
        people = [dict(id=person.id,
                       email=person.email,
                       name=person.name,
                       phone=person.phone)
                  for person in DBSession.query(Person).all()]
        return people
