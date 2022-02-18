import mysql.connector as sqltor
import pickle as binwriter
from main import resource_path


def initialise_sql(host, user, password):
    try:
        mycon = sqltor.connect(host=host, user=user, password=password)
    except:
        return False
    with open(resource_path(r'assets\creds.bin'), 'wb') as f:
        binwriter.dump({'host': host, 'user': user, 'password': password}, f)
    cur = mycon.cursor()
    cur.execute("DROP DATABASE IF EXISTS BOOKIPEDIA")
    cur.execute('CREATE DATABASE BOOKIPEDIA')
    cur.execute('USE BOOKIPEDIA')
    cur.execute("CREATE TABLE REGISTRY("
                "name VARCHAR(20) NOT NULL, "
                "password VARCHAR(20) NOT NULL, "
                "bancheck BIT(1) DEFAULT b'0');")
    cur.execute('create table regdata('
                'name varchar(20) not null, '
                'book varchar(60), '
                "readbook bit(1) default b'0', "
                "likebook bit(1) default b'0', "
                "wantbook bit(1) default b'0', "
                'comments varchar(200));')
    cur.execute('INSERT INTO REGISTRY VALUES("root","pass", 0);')
    mycon.commit()
    return True


def connection():
    with open(resource_path(r'assets\creds.bin'), 'rb') as f:
        creds = binwriter.load(f)
    mycon = sqltor.connect(host=creds['host'],
                           user=creds['user'],
                           password=creds['password'],
                           database='bookipedia')
    if mycon.is_connected():
        return mycon


def cursor_obj():
    global con_obj, cursor
    con_obj = connection()
    con_obj.autocommit = True
    cursor = con_obj.cursor()
    return cursor


def create_profile(uname, pwd):
    cursor.execute(f'INSERT INTO REGISTRY VALUES("{uname}", "{pwd}",0);')


def getuser(name):
    cursor.execute(f"SELECT name FROM REGISTRY where name='{name}';")
    return cursor.fetchone()


def delete_profile(name):
    cursor.execute(f'DELETE FROM REGDATE WHERE name="{name}";')
    cursor.execute(f'DELETE FROM REGISTRY WHERE name="{name}";')


def login(uname):
    cursor.execute("USE BOOKIPEDIA")
    cursor.execute(f'SELECT * FROM REGISTRY WHERE name="{uname}";')
    u_query = cursor.fetchone()
    if not u_query:
        return ['', '']
    return u_query


def tempbook(uname, bookid=''):
    cursor.execute(f'INSERT INTO REGDATA (name,book) VALUES("{uname}", "{bookid}");')


def list_toggle(uname, condn=True, bookid='', toggle_type=''):
    if condn:
        cursor.execute(f'SELECT {toggle_type} FROM REGDATA WHERE name="{uname}" AND book="{bookid}";')
        boolean = int(not cursor.fetchone()[0])
        cursor.execute(f'UPDATE REGDATA SET {toggle_type}={boolean} WHERE name="{uname}" AND book="{bookid}";')
    else:
        cursor.execute(f'SELECT BOOK FROM REGDATA WHERE {toggle_type}=1 AND name="{uname}";')
        returnlist = cursor.fetchall()
        if bool(returnlist):
            return list(i[0] for i in returnlist)
        else:
            return []


def insertcomment(bookid, condn=True, uname='', comment=''):
    if condn:
        cursor.execute(f'UPDATE REGDATA SET comments="{comment}" WHERE name="{uname}" AND book="{bookid}";')
    else:
        cursor.execute(f'SELECT name,comments FROM REGDATA WHERE book="{bookid}"')
        comments_tuple = []
        for tup in cursor.fetchall():
            if bool(tup[1]):
                comments_tuple += [tup]
        return comments_tuple


def book_onclick(name, book):
    cursor.execute(f"SELECT name,book FROM REGDATA WHERE name='{name}' AND book='{book}';")
    if not cursor.fetchone():
        cursor.execute(f"INSERT INTO REGDATA VALUES('{name}','{book}',0,0,0,'');")


def banlist():
    cursor.execute("SELECT name,bancheck FROM REGISTRY WHERE NOT name='root';")
    ban_list = cursor.fetchall()
    for i in range(len(ban_list)):
        if ban_list[i][1] == 0:
            ban_list[i] = (ban_list[i][0], False)
        else:
            ban_list[i] = (ban_list[i][0], True)
    return ban_list


def ban(uname, banbool=1):
    cursor.execute(f"update registry set bancheck={banbool} where name = '{uname}';")


def eradicate():
    try:
        cursor.execute("DELETE FROM REGDATA WHERE readbook + likebook + wantbook = 0 AND comments='';")
    except AttributeError:
        pass
