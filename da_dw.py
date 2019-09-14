#!/usr/bin/env python3

import sys
import os
import re
import requests
import urllib

URL_DA = 'https://www.deviantart.com'
URL_LOGIN = f'{URL_DA}/users/login'
URL_SIGNIN = f'{URL_DA}/_sisu/do/signin'
URL_DEVIATIONS = f'{URL_DA}/notifications/watch/deviations'
URL_WATCH = f'{URL_DA}/_napi/da-messagecentre/api/watch'

USER_AGENT = 'Mozilla/5.0 (X11; Linux x86_64; rv:68.0) Gecko/20100101 Firefox/68.0'

def filename_safe(filename):
    return re.sub(r'[^\w\d-]', '_', filename)

username = sys.argv[1]
password = sys.argv[2]
_px = None
if len(sys.argv) == 4:
    _px = sys.argv[3]
    #_px = urllib.parse.quote_plus(_px)

### Create deviations folder
FOLDER_DA = 'deviations'
os.makedirs(FOLDER_DA, exist_ok=True)

### Get initial cookie and csrf_token
headers = {'User-Agent': USER_AGENT}
if _px:
    headers['Cookie'] = f'_px={_px}'
r = requests.get(URL_LOGIN, headers=headers)
set_cookie = r.headers['set-cookie']
print('set-cookie', set_cookie)
match = re.search('(userinfo=)([^ ;]*)', set_cookie)
if not match:
    print('Something went wrong :(')
    print('html:', r.text)
    print('headers:', r.headers)
    sys.exit(1)
userinfo = match.group(2)
html = r.text
# print('html', html)
match = re.search('(<input type=\"hidden\" name=\"csrf_token\" value=\")([^ ]*)(\"\/)', html)
csrf_token = match.group(2)
print('csrf_token', csrf_token)

### Sign In
headers = {'User-Agent': USER_AGENT, 'Cookie': f'userinfo={userinfo}; _px={_px}', 'Referer': URL_LOGIN}
data = {'referer': URL_DA, 'csrf_token': csrf_token, 'challenge': '0', 'username': username, 'password': password}
r = requests.post(URL_SIGNIN, headers=headers, data=data, allow_redirects=False)
html = r.text
# print('html', html)
# print('headers', r.headers)
set_cookie = r.headers['Set-Cookie']
print('set-cookie', set_cookie)
match = re.search('(userinfo=)([^ ;]*)', set_cookie)
userinfo = match.group(2)
match = re.search('(auth=)([^ ;]*)', set_cookie)
auth = match.group(2)
match = re.search('(auth_secure=)([^ ;]*)', set_cookie)
auth_secure = match.group(2)

### Watch
headers['Referer'] = URL_DEVIATIONS
headers['Cookie'] = f'userinfo={userinfo}; _px={_px}; auth={auth}; auth_secure={auth_secure}'
 # watch?limit=24&messagetype=deviations&stacked=true&cursor=YTM1ZjQxOGQ9MjQ'
cursor = None
total = None
while True:
    params = {'limit': '24', 'messagetype': 'deviations', 'stacked': 'false'}
    if cursor:
        params['cursor'] = cursor
    r = requests.get(URL_WATCH, headers=headers, params=params)
    try:
        j = r.json()
    except:
        print('Something went wrong :(')
        print('html:', r.text)
        sys.exit(1)
    if not cursor:
        total = j['counts']['total']
        print(f'Total deviations: {total}')
    for result in j['results']:
        deviation = result['deviation']
        url = deviation['url']
        title = deviation['title']
        author = deviation['author']['username']
        deviation_id = deviation['deviationId']
        print(f'- {title} ({deviation_id}) by {author}: {url}')
        try:
            file_url = deviation['files'][8]['src']
        except:
            print('No fullview file found for deviation')
            continue
        try:
            r = requests.get(file_url, headers={'User-Agent': USER_AGENT})
        except KeyboardInterrupt:
            sys.exit(1)
        except:
            print('Error downloading deviation fullview file')
            continue
        content_type = r.headers['content-type']
        ext = None
        if content_type == 'image/jpeg':
            ext = 'jpg'
        elif content_type == 'image/png':
            ext = 'png'
        elif content_type == 'image/gif':
            ext = 'png'
        elif content_type == 'video/mp4':
            ext = 'mp4'
        else:
            print(f'Unexpected content-type: {content_type}')
            sys.exit(1)
        filename = f'{title}_{deviation_id}_by_{author}'.lower()
        filename = filename_safe(filename)
        filename = f'{filename}.{ext}'
        file_path = f'{FOLDER_DA}/{filename}'
        if os.path.isfile(file_path):
            print(f'File {file_path} already exists!')
            sys.exit(1)
        with open(file_path, 'w+b') as f:
            f.write(r.content)

    if j['hasMore']:
        cursor = j['cursor']
    else:
        break

