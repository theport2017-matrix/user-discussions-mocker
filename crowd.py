#!/usr/bin/env python3

import json, io, requests, time
import urllib, math

class UserLink:
    "Class in charge creating of users"
    def __init__(self, homeserver="matrix.fastcoin.ch"):
        """
        Keyword arguments:
        homeserver -- the homeserver base address (ie. https://matrix.org")
        """

        if (homeserver.find("http") < 0):
            homeserver = "https://" + homeserver
        self.homeserver_url = homeserver

    def createUser(self, username, display_name=None, password=None):
        """
        Depends on
        self.homeserver_url

        Keyword arguments:
        userid -- string containing the name of the user to be created

        Populates:
        self.username
        self.password
        self.display_name
        self.access_token
        self.user_id
        self.device_id
        self.homeserver

        """
        if hasattr(self, "access_token"):
            print("access_token detected, not creating user")
            return self
        if not hasattr(self, "homeserver_url"):
            print("No homeserver set!")
            return self
        if password is None:
            password = username
        if display_name is None:
            display_name = username

        registration_endpoint = self.homeserver_url + "/_matrix/client/r0/register"
        precreate_data = {"auth":{},"username":username,"password":username,"bind_email":True,"bind_msisdn":True,"x_show_msisdn":True}
        precreate_response = requests.post(registration_endpoint, json=precreate_data).json()
        create_data = {"auth":{"session":precreate_response['session'],"type":"m.login.dummy"},"username":username,"password":username,"bind_email":True,"bind_msisdn":True,"x_show_msisdn":True}
        create_response = requests.post(registration_endpoint, json=create_data).json()

        self.username = username
        self.password = password
        self.display_name = display_name
        self.access_token = create_response['access_token']
        self.user_id = create_response['user_id']
        self.device_id = create_response['device_id']
        self.homeserver = create_response['home_server']

        displayname_endpoint = self.homeserver_url + "/_matrix/client/r0/displayname"
        self.lastr = requests.put(displayname_endpoint, params={"access_token":self.access_token}, json={"displayname":display_name})

        return self

    def setPresence(self, presence="online"):
        if not hasattr(self, "access_token"):
            print("Couldn't find access token, authenticate first")
            return self

        presence_url = self.homeserver_url + "/_matrix/client/r0/presence/" + self.user_id + "/status"
        self.lastr = requests.put(presence_url, params={"access_token":self.access_token}, json={"presence":presence})
        return self

    def createRoom(self, room_name):
        if room_name.find("#") != 0:
            print("Invalid room_name: format #group_name:" + self.homeserver)
            return self
        room_id = room_name.split("#")[1].split(":")[0].lower().replace(" ", "_")
        self.last_room = room_id + self.homeserver
        ## Dirty hack to prevent python-requests from splitting my url.
        room_id = urllib.parse.quote(room_id)
        endpoint= self.homeserver_url + "/_matrix/client/r0/createRoom"
        data = {
            "preset": "public_chat",
#            "room_alias_name": room_id,
            "name": room_id,
            "visibility": "public",
#            "topic": room_id,
            "initial_state":[{"content":{"guest_access":"can_join"}, "type":"m.room.guest_access", "state_key":{}}],
#            "creation_content": { "m.federate": True }
            }
        self.lastr = requests.post(endpoint, params={"access_token":self.access_token}, json=data)
        #self.last_room = self.lastr.json()['room_id']
        return self

    def joinRoom(self, room_id):
        if len(room_id) == 0:
            print("Please specify a non-empty id")
            return self
        self.last_room = room_id
        ## Dirty hack to prevent python-requests from splitting my url.
        room_id = urllib.parse.quote(room_id)
        join_endpoint= self.homeserver_url + "/_matrix/client/r0/join/" + room_id
        self.lastr = requests.post(join_endpoint, params={"access_token":self.access_token})
        #self.last_room = self.lastr.json()['room_id']
        return self

    def sendMessage(self, message, room_id=None):
        if len(message) == 0:
            print("Please specify a non-empty message")
            return self

        if room_id is None:
            room_id = self.last_room

        ## Dirty hack to prevent python-requests from splitting my url.
        room_id = urllib.parse.quote(room_id)
        endpoint= self.homeserver_url + "/_matrix/client/r0/rooms/" + room_id + "/send/m.room.message/m" + str(time.time())
        self.lastr = requests.put(endpoint, params={"access_token":self.access_token}, json={"msgtype":"m.test", "body":message})
        return self

class ScriptRoller:
    def __init__(self, admin_user_link, homeserver="matrix.fastcoin.ch"):
        if (homeserver.find("http") < 0):
            homeserver = "https://" + homeserver
        self.homeserver_url = homeserver
        self.admin = admin_user_link

    def roll(self, discussion):
        for l in discussion:
            if l.find("#") == 0:
                admin_user_link.createRoom(l)

    def rollfile(self, filename):
        with open(filename) as sourcefile:
            self.roll(sourcefile.readlines())

class Bordel:
    def find_discussions(self):
        from os import listdir
        from os.path import isfile, join
        return [f for f in listdir(".") if isfile(join(".", f)) and f.find("disc") >= 0]

