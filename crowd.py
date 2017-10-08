#!/usr/bin/env python3

import json, io, requests, time, random
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
        self.access_token
        self.user_id
        self.device_id
        self.homeserver
        self.joined_groups = {}

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
        self.access_token = create_response['access_token']
        self.user_id = create_response['user_id']
        self.device_id = create_response['device_id']
        self.homeserver = create_response['home_server']
        self.joined_groups = {}

        displayname_endpoint = self.homeserver_url + "/_matrix/client/r0/profile/" + self.user_id + "/displayname"
        self.lastr = requests.put(displayname_endpoint, params={"access_token":self.access_token}, json={"displayname":display_name})

        return self

    def tryLoginElseRegister(self, username, password=None):
        if password is None:
            password = username

        endpoint = self.homeserver_url + "/_matrix/client/r0/login"
        login_data = {
              "type": "m.login.password",
              "password": password,
              "identifier": {
                "type": "m.id.user",
                "user": username
              },
              "initial_device_display_name": "Hello I'm a script :D",
              "user": username
            }
        r = requests.post(endpoint, json=login_data)
        self.lastr = r
        if r.status_code != 200:
            return self.createUser(username, password=password)
        response = r.json()
        self.username = username
        self.password = password
        self.access_token = response['access_token']
        self.user_id = response['user_id']
        self.device_id = response['device_id']
        self.homeserver = response['home_server']
        self.joined_groups = {}
        return self

    def setPresence(self, presence="online"):
        if not hasattr(self, "access_token"):
            print("Couldn't find access token, authenticate first")
            return self

        presence_url = self.homeserver_url + "/_matrix/client/r0/presence/" + self.user_id + "/status"
        self.lastr = requests.put(presence_url, params={"access_token":self.access_token}, json={"presence":presence})
        return self

    def createRoom(self, room_name, room_id, room_topic=None):
        if room_id.find("#") != 0:
            print("Invalid room_id: format #room_id:" + self.homeserver)
            return self
        room_name = room_name
        if room_topic is None:
            room_topic = room_name
        self.last_room = room_id + self.homeserver
        ## Dirty hack to prevent python-requests from splitting my url.
        room_id = urllib.parse.quote(room_id)
        endpoint= self.homeserver_url + "/_matrix/client/r0/createRoom"
        data = {
            "name": room_name,
            "preset": "public_chat",
            "visibility": "public",
            "initial_state":[{"content":{"guest_access":"can_join"}, "type":"m.room.guest_access", "state_key":""}],
            "room_alias_name": room_id,
            "topic": room_topic,
            "creation_content": { "m.federate": True }
            }
        self.lastr = requests.post(endpoint, params={"access_token":self.access_token}, json=data)
        #self.last_room = self.lastr.json()['room_id']
        return self

    def joinRoom(self, room_id):
        if room_id.find("#") != 0:
            print("Invalid room_id: format #room_id:" + self.homeserver)
            return self
        print("Joining " + self.username + " to room " + room_id)
        self.last_room = room_id
        room_id_escaped = urllib.parse.quote(room_id)
        join_endpoint= self.homeserver_url + "/_matrix/client/r0/join/" + room_id_escaped
        self.lastr = requests.post(join_endpoint, params={"access_token":self.access_token})
        if room_id not in self.joined_groups:
            self.joined_groups[room_id] = self.lastr.json()['room_id']
        return self

    def sendMessage(self, message, room_id=None):
        if len(message) == 0:
            print("Please specify a non-empty message")
            return self

        if room_id is None:
            room_id = self.last_room

        if room_id not in self.joined_groups:
            self.joinRoom(room_id)

        print("User " + self.username + " sending message to room " + room_id + ": " + message)
        room_internal_id = self.joined_groups[room_id]
        ## Dirty hack to prevent python-requests from splitting my url.
        room_internal_id = urllib.parse.quote(room_internal_id)
        endpoint= self.homeserver_url + "/_matrix/client/r0/rooms/" + room_internal_id + "/send/m.room.message/m" + str(time.time())
        self.lastr = requests.put(endpoint, params={"access_token":self.access_token}, json={"msgtype":"m.test", "body":message})
        return self

class ScriptRoller:
    def __init__(self, admin_user_link, homeserver="matrix.fastcoin.ch"):
        if (homeserver.find("http") < 0):
            homeserver = "https://" + homeserver
        self.homeserver_url = homeserver
        self.admin = admin_user_link.username
        self.last_username = self.admin
        self.last_room = None

        self.users = {self.admin:admin_user_link}

    def roll(self, discussion):
        for l in discussion:
            l = l.strip()
            if l.find("#") == 0:
                room_name = l
                topic = room_name
                if room_name.find(":")>0:
                    topic = room_name.split(":")[1]
                    room_name = room_name.split(":")[0].strip()
                admin = self.users[self.admin]
                room_id = room_name.lower().replace(" ","_").strip() + ":" + admin.homeserver
                admin.createRoom(room_name, room_id, topic)
                self.last_room = room_id
            elif l.find("@") == 0:
                username = l.split("@")[1].lower()
                if username not in self.users:
                    self.users[username] = UserLink().tryLoginElseRegister(username).setPresence()
#                user = self.users[username]
#                user.joinRoom(self.last_room)
#                self.users[username]
                self.last_username = username
            else:
                time.sleep(1 + 5 * random.random())
                user = self.users[self.last_username]
                user.sendMessage(l, self.last_room)
        return self

    def rollfile(self, filename):
        with open(filename) as sourcefile:
            self.roll(sourcefile.readlines())
        return self

class Bordel:
    def find_discussions(self):
        from os import listdir
        from os.path import isfile, join
        return [f for f in listdir(".") if isfile(join(".", f)) and f.find("disc") > 0]

