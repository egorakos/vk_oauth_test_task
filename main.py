#!/usr/bin/python3

import cherrypy
import requests
from jinja2 import Template

redirect_uri = 'http://egorakos.spb.ru:8080/'
client_secret = ''  # secret is so secret
client_id = '6385461'


class TestTask(object):
    def gettoken(self, code):
        authparams = {
            'client_id': client_id,
            'client_secret': client_secret,
            'redirect_uri': redirect_uri,
            'code': code,
        }
        response = requests.get(
            'https://oauth.vk.com/access_token',
            params=authparams,
            )
        # print(response.json())
        try:
            token = response.json()['access_token']
        except KeyError:
            raise Exception(str(response.json()['error']))
        self.token = token
        return token

    def getusers(self, token):
        """ actually only one """
        userparams = {
            'access_token': token,
            'v': '5.80',
        }
        response = requests.get(
            'https://api.vk.com/method/users.get',
            params=userparams,
            )
        try:
            userJSON = response.json()['response'][0]
            return userJSON
        except KeyError:
            raise Exception(str(response.json()['error']))

    def getfriends(self, token):
        """ returns full VK API response """
        params = {
            'access_token': token,
            'fields': 'name',
            # 'count': count,
            'v': '5.80',
        }
        response = requests.get(
            'https://api.vk.com/method/friends.get',
            params=params,
            )
        return response.json()

    @cherrypy.expose
    def getcode(self, **kwargs):
        uri = 'https://oauth.vk.com/authorize?client_id='
        uri += client_id + '&display=page&redirect_uri='
        uri += redirect_uri + '&scope=friends&response_type=code&v=5.80'
        raise cherrypy.HTTPRedirect(uri)

    @cherrypy.expose
    def index(self, **kwargs):
        if 'code' in kwargs:
            token = self.gettoken(kwargs['code'])
            cherrypy.session['token'] = token
            raise cherrypy.HTTPRedirect('/?n=5')
        else:
            try:
                token = cherrypy.session['token']
            except KeyError:
                return Template(open('templates/index.html').read()).render()
        try:
            userJSON = self.getusers(token)
            friends_response = self.getfriends(token)['response']
            friendscount = friends_response['count']
            friends_list = friends_response['items']
            if 'n' in kwargs:
                friends_list = friends_list[:int(kwargs['n'])]
            template = Template(open('templates/index.html').read())
            return template.render(
                user=userJSON,
                friends_list=friends_list,
                count=friendscount
                )
        except:
            cherrypy.session.pop('token')
            raise cherrypy.HTTPRedirect('/')


if __name__ == '__main__':
    cherrypy.quickstart(TestTask(), '/', 'conf')
