#! /usr/bin/python3

import httplib2, urllib, re, json, os, urllib.request, sys

http = httplib2.Http(ca_certs='/etc/ssl/certs/ca-certificates.crt')
#httplib2.debuglevel=4
encoding = "windows-1252"

# Auxiliar function
def save(line):
    f = open('test.html', 'w')
    f.write(line)
    f.close()

def download_images(images, path):
    for im in images:
        #print(im)
        filename = im.split("/")[-1]
        filename = os.path.join(path,filename)
        try:
            urllib.request.urlretrieve(im, filename)
        except:
            print("Failed to download "+im)

def parse_hugeview(hit):
        hugeview = hit['hugeview']
        img_urls = re.findall('(?<=-img=")[^ ]*://fc[^ ]*(?=")', hugeview)
        if len(img_urls) > 0:
            img_url = img_urls[0]
        else:
            thumb = re.findall('(?<=src=")[^ ]*://fc[^ ]*(?=")', hugeview)
            if len(thumb) < 1:
                href = re.findall('(?<=href=")[^ ]*(?=")', hugeview)[0]
                print("This is not an image: " + href)
                return  re.findall('(?<=src=")[^ ]*(?=")', hugeview)[0]
            image_name = thumb[0].split("/")[-1]
            # When the thumbnail doesn't correspond to the actual image
            resp, content = http.request(hit['url'], 'GET')
            image_page = content.decode(encoding)
            img_urls = re.findall('(?<=src=")[^ ]*://fc[^ ]*(?=")', image_page)
            for img in img_urls:
                if thumb != img:
                    img_url = img
                    break
            img_url = ''
        return img_url

if len(sys.argv) < 3:
    print("Usage: " + sys.argv[0] + " username password")
    sys.exit()

username = sys.argv[1]
password = sys.argv[2]

url = "https://www.deviantart.com/users/login"
# This url will give us a pretty json with all the information of new deviations
deviations_url = "http://www.deviantart.com/global/difi/?c%5B%5D=%22MessageCenter%22%2C%22get_views%22%2C%5B%224529392%22%2C%22oq%3Adevwatch%3A0%3A100%3Af%3Atg%3Ddeviations%2Cgroup%3Dsender%22%5D&t=json"
#deviations_user_url_begin = "http://www.deviantart.com/global/difi/?c%5B%5D=%22MessageCenter%22%2C%22get_views%22%2C%5B%224529392%22%2C%22oq%3Adevwatch%3A0%3A48%3Af%3Atg%3Ddeviations%2Csender%3D"
#deviations_user_url_end = "%22%5D&t=json"
deviations_user_url_begin = 'http://www.deviantart.com/global/difi/?c[]="MessageCenter","get_views",["4529392","oq:devwatch:0:48:f:tg=deviations,sender='
deviations_user_url_end = '"]&t=json'
#encoding = "utf-8"
folder = "deviations"

login_data = 'username=' + username + '&password=' + password + '&remember_me=1'
headers = {'Content-type': 'application/x-www-form-urlencoded'}

print("Logging in...")
resp, content = http.request(url, "POST", headers=headers, body=login_data)

headers = {'Cookie': resp['set-cookie']}

# httplib will merge all the "Cookie" fields separating them with ", " ... That's not good!
headers['Cookie'] = headers['Cookie'].replace(", ", "; ")

print("Retrieving deviatons pages...")
resp, content = http.request(deviations_url, 'GET', headers=headers)
deviations = content.decode(encoding)

dev_dec = json.loads(deviations)
hits = dev_dec['DiFi']['response']['calls'][0]['response']['content'][0]['result']['hits']

n_deviations = 0
for hit in hits:
    n_deviations = n_deviations + int(hit['stack_count'])

print("You have " + str(n_deviations) + " new deviations from " + str(len(hits)) + " users")

#exit()

print("Downloading deviations...")
# Iterate on users with new deviations
images = []
for hit in hits:
    # Check if there is one or more deviation for that user
    if hit['stack_count'] == '1':
        images.append(parse_hugeview(hit))
    else:
        user_stack_url = deviations_user_url_begin + hit['whoid'] + deviations_user_url_end
        resp, content = http.request(user_stack_url, 'GET', headers=headers)
        user_stack = content.decode(encoding)
        #print()
        #print(user_stack)
        #print()
        stack_dec = json.loads(user_stack)
        hits2 = stack_dec['DiFi']['response']['calls'][0]['response']['content'][0]['result']['hits']
        for hit2 in hits2:
            try:
                images.append(parse_hugeview(hit2))
            except:
                print('Error with: ', hit2)


download_images(images, 'deviations')

#save(deviations)
