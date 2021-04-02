import datetime
import json
import sys
import urllib
import os
import codecs

import requests

from prettytable import PrettyTable

from geopy.geocoders import Nominatim

from function import printcolors as pc

from instagram_private_api import Client as AppClient
from instagram_private_api import ClientCookieExpiredError, ClientLoginRequiredError, ClientError, ClientThrottledError


class dat_insta:
    api = None
    api2 = None
    geolocator = Nominatim(user_agent="http")
    user_id = None
    target_id = None
    is_private = True
    following = False
    target = ""
    writeFile = False
    jsonDump = False

    def __init__(self, target, is_file, is_json):
        u = self.__getUsername__()
        p = self.__getPassword__()
        print("\nĐang dô chờ tí...")
        self.login(u, p)
        self.setTarget(target)
        self.writeFile = is_file
        self.jsonDump = is_json

    def setTarget(self, target):
        self.target = target
        user = self.get_user(target)
        self.target_id = user['id']
        self.is_private = user['is_private']
        self.following = self.check_following()
        self.__printTargetBanner__()

    def __getUsername__(self):
        try:
            u = open("../tk.conf", "r").read()
            u = u.replace("\n", "")
            return u
        except FileNotFoundError:
            pc.printout(": file \"tk.conf\" không có!", pc.RED)
            pc.printout("\n")
            sys.exit(0)

    def __getPassword__(self):
        try:
            p = open("../mk.conf", "r").read()
            p = p.replace("\n", "")
            return p
        except FileNotFoundError:
            pc.printout("Error: file \"mk.conf\" not found!", pc.RED)
            pc.printout("\n")
            sys.exit(0)

    def __get_feed__(self):
        data = []

        result = self.api.user_feed(str(self.target_id))
        data.extend(result.get('items', []))

        next_max_id = result.get('next_max_id')
        while next_max_id:
            results = self.api.user_feed(str(self.target_id), max_id=next_max_id)
            data.extend(results.get('items', []))
            next_max_id = results.get('next_max_id')

        return data

    def __printTargetBanner__(self):
        pc.printout("\nLogged as ", pc.GREEN)
        pc.printout(self.api.username, pc.CYAN)
        pc.printout(". Target: ", pc.GREEN)
        pc.printout(str(self.target), pc.CYAN)
        pc.printout(" [" + str(self.target_id) + "]")
        if self.is_private:
            pc.printout(" [PRIVATE PROFILE]", pc.BLUE)
        if self.following:
            pc.printout(" [FOLLOWING]", pc.GREEN)
        else:
            pc.printout(" [NOT FOLLOWING]", pc.RED)

        print('\n')

    def change_target(self):
        pc.printout("Đưa đứa khác coi thử: ", pc.YELLOW)
        line = input()
        self.setTarget(line)
        return

    def check_following(self):
        if str(self.target_id) == self.api.authenticated_user_id:
            return True
        endpoint = 'users/{user_id!s}/full_detail_info/'.format(**{'user_id': self.target_id})
        return self.api._call_api(endpoint)['user_detail']['user']['friendship_status']['following']

    def get_media_type(self):
        if self.check_private_profile():
            return

        pc.printout("đang tìm...\n")

        counter = 0
        photo_counter = 0
        video_counter = 0

        data = self.__get_feed__()

        for post in data:
            if "media_type" in post:
                if post["media_type"] == 1:
                    photo_counter = photo_counter + 1
                elif post["media_type"] == 2:
                    video_counter = video_counter + 1
                counter = counter + 1
                sys.stdout.write("\rChecked %i" % counter)
                sys.stdout.flush()

        sys.stdout.write(" posts")
        sys.stdout.flush()

        if counter > 0:

            if self.writeFile:
                file_name = "output/" + self.target + "_mediatype.txt"
                file = open(file_name, "w")
                file.write(str(photo_counter) + " photos and " + str(video_counter) + " video posted by target\n")
                file.close()

            pc.printout("\ntôi tìm thấy rồi " + str(photo_counter) + " photos and " + str(video_counter) +
                        " video posted by target\n", pc.GREEN)

            if self.jsonDump:
                json_data = {
                    "photos": photo_counter,
                    "videos": video_counter
                }
                json_file_name = "output/" + self.target + "_mediatype.json"
                with open(json_file_name, 'w') as f:
                    json.dump(json_data, f)

        else:
            pc.printout("không tìm thấy :-(\n", pc.RED)

    def get_location(self):
        if self.check_private_profile():
            return

        pc.printout("Đang tìm địa chỉ nó hay đi lại :>\n")

        data = self.__get_feed__()

        locations = {}

        for post in data:
            if 'location' in post and post['location'] is not None:
                if 'lat' in post['location'] and 'lng' in post['location']:
                    lat = post['location']['lat']
                    lng = post['location']['lng']
                    locations[str(lat) + ', ' + str(lng)] = post.get('taken_at')

        address = {}
        for k, v in locations.items():
            details = self.geolocator.reverse(k)
            unix_timestamp = datetime.datetime.fromtimestamp(v)
            address[details.address] = unix_timestamp.strftime('%Y-%m-%d %H:%M:%S')

        sort_addresses = sorted(address.items(), key=lambda p: p[1], reverse=True)

        if len(sort_addresses) > 0:
            t = PrettyTable()

            t.field_names = ['Post', 'Address', 'time']
            t.align["Post"] = "l"
            t.align["Address"] = "l"
            t.align["Time"] = "l"
            pc.printout("\nOhh shit tôi tìm được rồi" + str(len(sort_addresses)) + " addresses\n", pc.GREEN)

            i = 1

            json_data = {}
            addrs_list = []

            for address, time in sort_addresses:
                t.add_row([str(i), address, time])

                if self.jsonDump:
                    addr = {
                        'address': address,
                        'time': time
                    }
                    addrs_list.append(addr)

                i = i + 1

            if self.writeFile:
                file_name = "output/" + self.target + "_addrs.txt"
                file = open(file_name, "w")
                file.write(str(t))
                file.close()

            if self.jsonDump:
                json_data['address'] = addrs_list
                json_file_name = "output/" + self.target + "_addrs.json"
                with open(json_file_name, 'w') as f:
                    json.dump(json_data, f)

            print(t)
        else:
            pc.printout("ui ghê nó ít vị trí đi lại quá\n", pc.RED)

    def get_user_info(self):
        try:
            endpoint = 'users/{user_id!s}/full_detail_info/'.format(**{'user_id': self.target_id})
            content = self.api._call_api(endpoint)

            data = content['user_detail']['user']

            pc.printout("[ID] ", pc.GREEN)
            pc.printout(str(data['pk']) + '\n')
            pc.printout("[Tên đầy ] ", pc.RED)
            pc.printout(str(data['full_name']) + '\n')
            pc.printout("[BIOGRAPHY] ", pc.CYAN)
            pc.printout(str(data['biography']) + '\n')
            pc.printout("[FOLLOWED] ", pc.BLUE)
            pc.printout(str(data['follower_count']) + '\n')
            pc.printout("[FOLLOW] ", pc.GREEN)
            pc.printout(str(data['following_count']) + '\n')
            pc.printout("[BUSINESS ACCOUNT] ", pc.RED)
            pc.printout(str(data['is_business']) + '\n')
            if data['is_business']:
                if not data['can_hide_category']:
                    pc.printout("[BUSINESS CATEGORY] ")
                    pc.printout(str(data['category']) + '\n')
            pc.printout("[VERIFIED ACCOUNT] ", pc.CYAN)
            pc.printout(str(data['is_verified']) + '\n')
            if 'public_email' in data and data['public_email']:
                pc.printout("[EMAIL] ", pc.BLUE)
                pc.printout(str(data['public_email']) + '\n')
            pc.printout("[HD PROFILE PIC] ", pc.GREEN)
            pc.printout(str(data['hd_profile_pic_url_info']['url']) + '\n')
            if 'fb_page_call_to_action_id' in data and data['fb_page_call_to_action_id']:
                pc.printout("[FB PAGE] ", pc.RED)
                pc.printout(str(data['connected_fb_page']) + '\n')
            if 'city_name' in data and data['city_name']:
                pc.printout("[CITY] ", pc.YELLOW)
                pc.printout(str(data['city_name']) + '\n')
            if 'address_street' in data and data['address_street']:
                pc.printout("[ADDRESS STREET] ", pc.RED)
                pc.printout(str(data['address_street']) + '\n')
            if 'contact_phone_number' in data and data['contact_phone_number']:
                pc.printout("[CONTACT PHONE NUMBER] ", pc.CYAN)
                pc.printout(str(data['contact_phone_number']) + '\n')

            if self.jsonDump:
                user = {
                    'id': data['pk'],
                    'full_name': data['full_name'],
                    'biography': data['biography'],
                    'edge_followed_by': data['follower_count'],
                    'edge_follow': data['following_count'],
                    'is_business_account': data['is_business_account'],
                    'is_verified': data['is_business'],
                    'profile_pic_url_hd': data['hd_profile_pic_url_info']['url']
                }
                if 'public_email' in data and data['public_email']:
                    user['email'] = data['public_email']
                if 'fb_page_call_to_action_id' in data and data['fb_page_call_to_action_id']:
                    user['connected_fb_page'] = data['fb_page_call_to_action_id']
                if 'city_name' in data and data['city_name']:
                    user['city_name'] = data['city_name']
                if 'address_street' in data and data['address_street']:
                    user['address_street'] = data['address_street']
                if 'contact_phone_number' in data and data['contact_phone_number']:
                    user['contact_phone_number'] = data['contact_phone_number']

                json_file_name = "output/" + self.target + "_info.json"
                with open(json_file_name, 'w') as f:
                    json.dump(user, f)

        except ClientError as e:
            print(e)
            pc.printout("Oops... " + str(self.target) + " non exist, please enter a valid username.", pc.RED)
            pc.printout("\n")
            exit(2)

    def get_photo_description(self):
        if self.check_private_profile():
            return

        content = requests.get("https://www.instagram.com/" + str(self.target) + "/?__a=1")
        data = content.json()

        dd = data['graphql']['user']['edge_owner_to_timeline_media']['edges']

        if len(dd) > 0:
            pc.printout("\nOhh shit tôi tìm được rồi " + str(len(dd)) + " descriptions\n", pc.GREEN)

            count = 1

            t = PrettyTable(['Photo', 'Description'])
            t.align["Photo"] = "l"
            t.align["Description"] = "l"

            json_data = {}
            descriptions_list = []

            for i in dd:
                node = i.get('node')
                descr = node.get('accessibility_caption')
                t.add_row([str(count), descr])

                if self.jsonDump:
                    description = {
                        'description': descr
                    }
                    descriptions_list.append(description)

                count += 1

            if self.writeFile:
                file_name = "output/" + self.target + "_photodes.txt"
                file = open(file_name, "w")
                file.write(str(t))
                file.close()

            if self.jsonDump:
                json_data['descriptions'] = descriptions_list
                json_file_name = "output/" + self.target + "_descriptions.json"
                with open(json_file_name, 'w') as f:
                    json.dump(json_data, f)

            print(t)
        else:
            pc.printout("tìm không ra nè :-(\n", pc.RED)

    def get_user_photo(self):
        if self.check_private_profile():
            return

        limit = -1
        pc.printout("Bao nhiêu ảnh bạn muốn tải về: ", pc.YELLOW)
        user_input = input()
        try:
            if user_input == "":
                pc.printout("đang tải ảnh chờ ...\n")
            else:
                limit = int(user_input)
                pc.printout("Tải ảnh của" + user_input + " xuống máy bạn ...\n")

        except ValueError:
            pc.printout("giá trị nhập vào ko đúng\n", pc.RED)
            return

        data = []
        counter = 0

        result = self.api.user_feed(str(self.target_id))
        data.extend(result.get('items', []))

        next_max_id = result.get('next_max_id')
        while next_max_id:
            results = self.api.user_feed(str(self.target_id), max_id=next_max_id)
            data.extend(results.get('items', []))
            next_max_id = results.get('next_max_id')

        try:
            for item in data:
                if counter == limit:
                    break
                if "image_versions2" in item:
                    counter = counter + 1
                    url = item["image_versions2"]["candidates"][0]["url"]
                    photo_id = item["id"]
                    end = "output/" + self.target + "_" + photo_id + ".jpg"
                    urllib.request.urlretrieve(url, end)
                    sys.stdout.write("\rDownloaded %i" % counter)
                    sys.stdout.flush()
                else:
                    carousel = item["carousel_media"]
                    for i in carousel:
                        if counter == limit:
                            break
                        counter = counter + 1
                        url = i["image_versions2"]["candidates"][0]["url"]
                        photo_id = i["id"]
                        end = "output/" + self.target + "_" + photo_id + ".jpg"
                        urllib.request.urlretrieve(url, end)
                        sys.stdout.write("\rDownloaded %i" % counter)
                        sys.stdout.flush()

        except AttributeError:
            pass

        except KeyError:
            pass

        sys.stdout.write(" photos")
        sys.stdout.flush()

        pc.printout("\nyeah tôi đã tải xuống thành công " + str(counter) + " ảnh đã lưu ở file photo_insta \n", pc.GREEN)

    def get_user_profile_picture(self):

        try:
            endpoint = 'users/{user_id!s}/full_detail_info/'.format(**{'user_id': self.target_id})
            content = self.api._call_api(endpoint)

            data = content['user_detail']['user']

            if "hd_profile_pic_url_info" in data:
                URL = data["hd_profile_pic_url_info"]['url']
            else:
                # get better quality photo
                items = len(data['hd_profile_pic_versions'])
                URL = data["hd_profile_pic_versions"][items - 1]['url']

            if URL != "":
                end = "output/" + self.target + "_propic.jpg"
                urllib.request.urlretrieve(URL, end)
                pc.printout("ảnh của nó đã được lưu", pc.GREEN)

            else:
                pc.printout("Nó không có để avata\n", pc.RED)

        except ClientError as e:
            error = json.loads(e.error_response)
            print(error['message'])
            print(error['error_title'])
            exit(2)

    def get_user_stories(self):
        if self.check_private_profile():
            return

        pc.printout("đang tìm stori...\n")

        data = self.api.user_reel_media(str(self.target_id))

        counter = 0

        if data['items'] is not None:  # no stories avaibile
            counter = data['media_count']
            for i in data['items']:
                story_id = i["id"]
                if i["media_type"] == 1:  # it's a photo
                    url = i['image_versions2']['candidates'][0]['url']
                    end = "output/" + self.target + "_" + story_id + ".jpg"
                    urllib.request.urlretrieve(url, end)

                elif i["media_type"] == 2:  # it's a gif or video
                    url = i['video_versions'][0]['url']
                    end = "output/" + self.target + "_" + story_id + ".mp4"
                    urllib.request.urlretrieve(url, end)

        if counter > 0:
            pc.printout(str(counter) + " đã lưu \n", pc.GREEN)
        else:
            pc.printout("Nó không đăng stories\n", pc.RED)

    def login(self, u, p):
        try:
            settings_file = "../settings.json"
            if not os.path.isfile(settings_file):
                # settings file does not exist
                print('Unable to find file: {0!s}'.format(settings_file))

                # login new
                self.api = AppClient(auto_patch=True, authenticate=True, username=u, password=p,
                                     on_login=lambda x: self.onlogin_callback(x, settings_file))

            else:
                with open(settings_file) as file_data:
                    cached_settings = json.load(file_data, object_hook=self.from_json)
                # print('Reusing settings: {0!s}'.format(settings_file))

                # reuse auth settings
                self.api = AppClient(
                    username=u, password=p,
                    settings=cached_settings,
                    on_login=lambda x: self.onlogin_callback(x, settings_file))

        except (ClientCookieExpiredError, ClientLoginRequiredError) as e:
            print('ClientCookieExpiredError/ClientLoginRequiredError: {0!s}'.format(e))

            self.api = AppClient(auto_patch=True, authenticate=True, username=u, password=p,
                                 on_login=lambda x: self.onlogin_callback(x, settings_file))

        except ClientError as e:
            error = json.loads(e.error_response)
            pc.printout(error['message'], pc.RED)
            pc.printout(": ", pc.RED)
            pc.printout(e.msg, pc.RED)
            pc.printout("\n")
            exit(9)

    def to_json(self, python_object):
        if isinstance(python_object, bytes):
            return {'__class__': 'bytes',
                    '__value__': codecs.encode(python_object, 'base64').decode()}
        raise TypeError(repr(python_object) + ' is not JSON serializable')

    def from_json(self, json_object):
        if '__class__' in json_object and json_object['__class__'] == 'bytes':
            return codecs.decode(json_object['__value__'].encode(), 'base64')
        return json_object

    def onlogin_callback(self, api, new_settings_file):
        cache_settings = api.settings
        with open(new_settings_file, 'w') as outfile:
            json.dump(cache_settings, outfile, default=self.to_json)
            # print('SAVED: {0!s}'.format(new_settings_file))

    def check_following(self):
        if str(self.target_id) == self.api.authenticated_user_id:
            return True
        endpoint = 'users/{user_id!s}/full_detail_info/'.format(**{'user_id': self.target_id})
        return self.api._call_api(endpoint)['user_detail']['user']['friendship_status']['following']

    def check_private_profile(self):
        if self.is_private and not self.following:
            pc.printout("thật khó để thực hiện command khi đó là tài khoản private\n", pc.RED)
            send = input("bạn có muốn gửi lời mời Follow không[Y/N]: ")
            if send.lower() == "y":
                self.api.friendships_create(self.target_id)
                print("mình gửi rồi đó p/s bạn chỉ sử dụng command khi người ta chấp nhận follow")

            return True
        return False

    def get_user(self, username):
        try:
            content = self.api.username_info(username)
            if self.writeFile:
                file_name = "output/" + self.target + "_user_id.txt"
                file = open(file_name, "w")
                file.write(str(content['user']['pk']))
                file.close()

            user = dict()
            user['id'] = content['user']['pk']
            user['is_private'] = content['user']['is_private']

            return user
        except ClientError as e:
            error = json.loads(e.error_response)
            if 'message' in error:
                print(error['message'])
            if 'error_title' in error:
                print(error['error_title'])
            if 'challenge' in error:
                print("Please follow this link to complete the challenge: " + error['challenge']['url'])
            sys.exit(2)

    def set_write_file(self, flag):
        if flag:
            pc.printout("Write to file: ")
            pc.printout("enabled", pc.GREEN)
            pc.printout("\n")
        else:
            pc.printout("Write to file: ")
            pc.printout("disabled", pc.RED)
            pc.printout("\n")

        self.writeFile = flag

    def get_fluseremail(self):
        if self.check_private_profile():
            return

        followers = []

        try:

            pc.printout("đang tìm gmail của mấy đứa nó follow\n")

            rank_token = AppClient.generate_uuid()
            data = self.api.user_followers(str(self.target_id), rank_token=rank_token)

            for user in data.get('users', []):
                u = {
                    'id': user['pk'],
                    'username': user['username'],
                    'full_name': user['full_name']
                }
                followers.append(u)

            next_max_id = data.get('next_max_id')
            while next_max_id:
                sys.stdout.write("\rtìm được %i người " % len(followers))
                sys.stdout.flush()
                results = self.api.user_followers(str(self.target_id), rank_token=rank_token, max_id=next_max_id)

                for user in results.get('users', []):
                    u = {
                        'id': user['pk'],
                        'username': user['username'],
                        'full_name': user['full_name']
                    }
                    followers.append(u)

                next_max_id = results.get('next_max_id')

            print("\n")

            results = []

            for follow in followers:
                user = self.api.user_info(str(follow['id']))
                if 'public_email' in user['user'] and user['user']['public_email']:
                    follow['email'] = user['user']['public_email']
                    results.append(follow)

        except ClientThrottledError  as e:
            pc.printout("\nError: INS nó chặn cmnr làm lại thử :((",
                        pc.RED)
            pc.printout("\n")
            return

        if len(results) > 0:

            t = PrettyTable(['ID', 'Username', 'Full Name', 'Email'])
            t.align["ID"] = "l"
            t.align["Username"] = "l"
            t.align["Full Name"] = "l"
            t.align["Email"] = "l"

            json_data = {}

            for node in results:
                t.add_row([str(node['id']), node['username'], node['full_name'], node['email']])

            if self.writeFile:
                file_name = "output/" + self.target + "_fwersemail.txt"
                file = open(file_name, "w")
                file.write(str(t))
                file.close()

            if self.jsonDump:
                json_data['followers_email'] = results
                json_file_name = "output/" + self.target + "_fwersemail.json"
                with open(json_file_name, 'w') as f:
                    json.dump(json_data, f)

            print(t)
        else:
            pc.printout("tìm không ra nè :-(\n", pc.RED)

    def get_flemail(self):
        if self.check_private_profile():
            return

        followings = []

        try:

            pc.printout("tìm gmail của người dùng fl bởi nick này chờ hơi lâu\n")

            rank_token = AppClient.generate_uuid()
            data = self.api.user_following(str(self.target_id), rank_token=rank_token)

            for user in data.get('users', []):
                u = {
                    'id': user['pk'],
                    'username': user['username'],
                    'full_name': user['full_name']
                }
                followings.append(u)

            next_max_id = data.get('next_max_id')

            while next_max_id:
                results = self.api.user_following(str(self.target_id), rank_token=rank_token, max_id=next_max_id)

                for user in results.get('users', []):
                    u = {
                        'id': user['pk'],
                        'username': user['username'],
                        'full_name': user['full_name']
                    }
                    followings.append(u)

                next_max_id = results.get('next_max_id')

            results = []

            for follow in followings:
                sys.stdout.write("\rtìm được gmail của %i người " % len(results))
                sys.stdout.flush()
                user = self.api.user_info(str(follow['id']))
                if 'public_email' in user['user'] and user['user']['public_email']:
                    follow['email'] = user['user']['public_email']
                    results.append(follow)

        except ClientThrottledError as e:
            pc.printout("\nError: INS nó chặn cmnr làm lại thử :((",
                        pc.RED)
            pc.printout("\n")
            return

        print("\n")

        if len(results) > 0:
            t = PrettyTable(['ID', 'Username', 'Full Name', 'Email'])
            t.align["ID"] = "l"
            t.align["Username"] = "l"
            t.align["Full Name"] = "l"
            t.align["Email"] = "l"

            json_data = {}

            for node in results:
                t.add_row([str(node['id']), node['username'], node['full_name'], node['email']])

            if self.writeFile:
                file_name = "output/" + self.target + "_fwingsemail.txt"
                file = open(file_name, "w")
                file.write(str(t))
                file.close()

            if self.jsonDump:
                json_data['followings_email'] = results
                json_file_name = "output/" + self.target + "_fwingsemail.json"
                with open(json_file_name, 'w') as f:
                    json.dump(json_data, f)

            print(t)
        else:
            pc.printout("Tìm không ra :-(\n", pc.RED)

    def get_flphone(self):
        if self.check_private_profile():
            return

        results = []

        try:

            pc.printout("tìm số đth của người dùng được nick này follow\n")

            followings = []

            rank_token = AppClient.generate_uuid()
            data = self.api.user_following(str(self.target_id), rank_token=rank_token)

            for user in data.get('users', []):
                u = {
                    'id': user['pk'],
                    'username': user['username'],
                    'full_name': user['full_name']
                }
                followings.append(u)

            next_max_id = data.get('next_max_id')

            while next_max_id:
                results = self.api.user_following(str(self.target_id), rank_token=rank_token, max_id=next_max_id)

                for user in results.get('users', []):
                    u = {
                        'id': user['pk'],
                        'username': user['username'],
                        'full_name': user['full_name']
                    }
                    followings.append(u)

                next_max_id = results.get('next_max_id')

            for follow in followings:
                sys.stdout.write("\rtìm được %i số đth" % len(results))
                sys.stdout.flush()
                user = self.api.user_info(str(follow['id']))
                if 'contact_phone_number' in user['user'] and user['user']['contact_phone_number']:
                    follow['contact_phone_number'] = user['user']['contact_phone_number']
                    results.append(follow)

        except ClientThrottledError as e:
            pc.printout("\nError: INS nó chặn cmnr làm lại thử :((",
                        pc.RED)
            pc.printout("\n")
            return

        print("\n")

        if len(results) > 0:
            t = PrettyTable(['ID', 'Username', 'Full Name', 'Phone'])
            t.align["ID"] = "l"
            t.align["Username"] = "l"
            t.align["Full Name"] = "l"
            t.align["Phone number"] = "l"

            json_data = {}

            for node in results:
                t.add_row([str(node['id']), node['username'], node['full_name'], node['contact_phone_number']])

            if self.writeFile:
                file_name = "output/" + self.target + "_fwingsnumber.txt"
                file = open(file_name, "w")
                file.write(str(t))
                file.close()

            if self.jsonDump:
                json_data['followings_phone_numbers'] = results
                json_file_name = "output/" + self.target + "_fwingsnumber.json"
                with open(json_file_name, 'w') as f:
                    json.dump(json_data, f)

            print(t)
        else:
            pc.printout("Tìm không ra nè :-(\n", pc.RED)

    def get_fluserphone(self):
        if self.check_private_profile():
            return

        followings = []

        try:

            pc.printout("tìm số đth của mấy đưá follow nick này\n")

            rank_token = AppClient.generate_uuid()
            data = self.api.user_following(str(self.target_id), rank_token=rank_token)

            for user in data.get('users', []):
                u = {
                    'id': user['pk'],
                    'username': user['username'],
                    'full_name': user['full_name']
                }
                followings.append(u)

            next_max_id = data.get('next_max_id')

            while next_max_id:
                results = self.api.user_following(str(self.target_id), rank_token=rank_token, max_id=next_max_id)

                for user in results.get('users', []):
                    u = {
                        'id': user['pk'],
                        'username': user['username'],
                        'full_name': user['full_name']
                    }
                    followings.append(u)

                next_max_id = results.get('next_max_id')

            results = []

            for follow in followings:
                sys.stdout.write("\rtìm được %i số " % len(results))
                sys.stdout.flush()
                user = self.api.user_info(str(follow['id']))
                if 'contact_phone_number' in user['user'] and user['user']['contact_phone_number']:
                    follow['contact_phone_number'] = user['user']['contact_phone_number']
                    results.append(follow)

        except ClientThrottledError as e:
            pc.printout("\nError: INS nó chặn cmnr làm lại thử :((",
                        pc.RED)
            pc.printout("\n")
            return

        print("\n")

        if len(results) > 0:
            t = PrettyTable(['ID', 'Username', 'Full Name', 'Phone'])
            t.align["ID"] = "l"
            t.align["Username"] = "l"
            t.align["Full Name"] = "l"
            t.align["Phone number"] = "l"

            json_data = {}

            for node in results:
                t.add_row([str(node['id']), node['username'], node['full_name'], node['contact_phone_number']])

            if self.writeFile:
                file_name = "output/" + self.target + "_fwersnumber.txt"
                file = open(file_name, "w")
                file.write(str(t))
                file.close()

            if self.jsonDump:
                json_data['followings_phone_numbers'] = results
                json_file_name = "output/" + self.target + "_fwerssnumber.json"
                with open(json_file_name, 'w') as f:
                    json.dump(json_data, f)
            print(t)
        else:
            pc.printout("tìm không ra nè :-(\n", pc.RED)
