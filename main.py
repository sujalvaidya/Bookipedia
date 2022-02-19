# Create exe using pyinstaller --onefile --windowed  --add-data="assets;assets" --icon="assets/images/app.ico" main.py

import sys
from PyQt5.uic import loadUi
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import QDialog, QApplication
from PyQt5.QtGui import QCursor
import requests
import socket
import requests.packages.urllib3.util.connection as urllib3_cn
from functools import partial
import backend_functions as bgfns
from itertools import groupby
import os.path
import logging
import pycountry
from threading import Thread

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s — Line:%(lineno)d — %(message)s",
                    datefmt='%d-%b-%y %H:%M:%S')
urllib3_cn.allowed_gai_family = lambda: socket.AF_INET


class SQLScreen(QDialog):
    def __init__(self):
        super(SQLScreen, self).__init__()
        loadUi(resource_path('assets/ui/sql-screen.ui'), self)
        self.password_line_edit.setEchoMode(QtWidgets.QLineEdit.Password)
        self.continue_button.clicked.connect(self.initialise_sql)
        self.host_line_edit.returnPressed.connect(self.initialise_sql)
        self.user_line_edit.returnPressed.connect(self.initialise_sql)
        self.password_line_edit.returnPressed.connect(self.initialise_sql)

    def initialise_sql(self):
        host = self.host_line_edit.text()
        user = self.user_line_edit.text()
        password = self.password_line_edit.text()
        if not bgfns.initialise_sql(host, user, password):
            self.error_label.setText("Connection error! Invalid credentials.")
        else:
            logging.info(f'{user} successfully connected to MYSQL server located in {host}.')
            WelcomeScreen().gotologin()


class WelcomeScreen(QDialog):
    def __init__(self):
        global cursor
        super(WelcomeScreen, self).__init__()
        loadUi(resource_path('assets/ui/welcome-screen.ui'), self)
        cursor = bgfns.cursor_obj()
        self.login_button.clicked.connect(self.gotologin)
        self.new_acc_button.clicked.connect(self.gotocreate)

    @staticmethod
    def gotologin():
        login = LoginScreen()
        widget.addWidget(login)
        widget.setCurrentIndex(widget.currentIndex() + 1)

    @staticmethod
    def gotocreate():
        create = CreateAccScreen()
        widget.addWidget(create)
        widget.setCurrentIndex(widget.currentIndex() + 1)


class LoginScreen(QDialog):
    def __init__(self):
        super(LoginScreen, self).__init__()
        loadUi(resource_path('assets/ui/login.ui'), self)
        self.password_line_edit.setEchoMode(QtWidgets.QLineEdit.Password)
        self.username_line_edit.returnPressed.connect(self.login_function)
        self.password_line_edit.returnPressed.connect(self.login_function)
        self.login_button.clicked.connect(self.login_function)
        self.sign_up_button.clicked.connect(WelcomeScreen.gotocreate)

    def login_function(self):
        global username
        username = self.username_line_edit.text()
        password = self.password_line_edit.text()
        self.error_label.setText('')
        self.error_label_2.setText('')
        if len(username) == 0 or len(password) == 0:
            self.error_label.setText('Please input all fields')
        else:
            try:
                userdata = bgfns.login(username)
                matched_password = userdata[1]
                if matched_password == password and not userdata[2]:
                    logging.info(f'{username} has successfully logged in.')
                    main_screen = MainScreen()
                    widget.addWidget(main_screen)
                    widget.setCurrentIndex(widget.currentIndex() + 1)
                elif userdata[2]:
                    logging.info(f'Banned user {username} attempted log in.')
                    self.error_label_2.setText("This account has been banned. Contact support@bookipedia.com to appeal your ban.")
                else:
                    self.error_label.setText('Invalid username or password')
            except:
                self.error_label.setText('Invalid username or password')


class CreateAccScreen(QDialog):
    def __init__(self):
        super(CreateAccScreen, self).__init__()
        loadUi(resource_path('assets/ui/create-acc.ui'), self)
        self.password_line_edit.setEchoMode(QtWidgets.QLineEdit.Password)
        self.confirm_password_line_edit.setEchoMode(QtWidgets.QLineEdit.Password)
        self.sign_up_button.clicked.connect(self.sign_up_function)
        self.username_line_edit.returnPressed.connect(self.sign_up_function)
        self.password_line_edit.returnPressed.connect(self.sign_up_function)
        self.confirm_password_line_edit.returnPressed.connect(self.sign_up_function)
        self.login_button.clicked.connect(WelcomeScreen.gotologin)

    def sign_up_function(self):
        global username
        username = self.username_line_edit.text()
        password = self.password_line_edit.text()
        confirm_password = self.confirm_password_line_edit.text()
        self.error_label.setText('')
        if len(username) == 0 or len(password) == 0 or len(
                confirm_password) == 0:
            self.error_label.setText("Please fill in all fields")
        elif password != confirm_password:
            self.error_label.setText("Passwords do not match")
        elif (bgfns.getuser(username)) and (
                username in bgfns.getuser(username)):
            self.error_label.setText("Username is already taken")
        elif not 4 < len(username) < 21:
            self.error_label.setText('Username should be 5 to 20 characters long.')
        elif not 4 < len(password) < 21:
            self.error_label.setText('Password should be 5 to 20 characters long.')
        else:
            bgfns.create_profile(username, password)
            logging.info(f'New user {username} signed up.')
            WelcomeScreen().gotologin()


class MainScreen(QDialog):
    def __init__(self):
        super(MainScreen, self).__init__()
        loadUi(resource_path('assets/ui/main-screen.ui'), self)
        if username not in admin_list:
            self.user_management.deleteLater()
            self.admin_shield.deleteLater()
        self.search_button.clicked.connect(self.search_function)
        self.search_line_edit.returnPressed.connect(self.search_function)
        self.menu_home.clicked.connect(MainScreen.gotomenu)
        self.menu_fav.clicked.connect(lambda: MainScreen.gotouserlists(0))
        self.menu_my_read.clicked.connect(lambda: MainScreen.gotouserlists(1))
        self.menu_read_list.clicked.connect(lambda: MainScreen.gotouserlists(2))
        self.menu_sign_out.clicked.connect(WelcomeScreen.gotologin)
        self.user_management.clicked.connect(MainScreen.gotousermanagement)

    def search_function(self):
        global searchterm
        searchterm = self.search_line_edit.text()
        if len(searchterm):
            logging.info(f"Searching for '{searchterm}'")
            QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
            response = requests.get(f"https://www.googleapis.com/books/v1/volumes?q={searchterm}&maxResults=40").json()
            search_screen = SearchScreen(response, True)
            widget.addWidget(search_screen)
            widget.setCurrentIndex(widget.currentIndex() + 1)

    @staticmethod
    def gotouserlists(num):
        items = []
        QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        user_lists = [bgfns.list_toggle(username, False, '', 'LIKEBOOK'),
                      bgfns.list_toggle(username, False, '', 'READBOOK'),
                      bgfns.list_toggle(username, False, '', 'WANTBOOK')]
        for book_id in user_lists[num]:
            resp = requests.get(f"https://www.googleapis.com/books/v1/volumes/{book_id}").json()
            items = items + [resp]
        response = {'items': items}
        search_screen = SearchScreen(response, False, num)
        widget.addWidget(search_screen)
        widget.setCurrentIndex(widget.currentIndex() + 1)

    @staticmethod
    def gotousermanagement():
        user_management = UserManagement()
        widget.addWidget(user_management)
        widget.setCurrentIndex(widget.currentIndex() + 1)

    @staticmethod
    def gotomenu():
        main_screen = MainScreen()
        widget.addWidget(main_screen)
        widget.setCurrentIndex(widget.currentIndex() + 1)

    @staticmethod
    def goback():
        widget_name = widget.currentWidget().objectName()
        if widget_name in ['expanded_book', 'user_management']:
            while widget.currentWidget().objectName() == widget_name:
                widget.removeWidget(widget.currentWidget())
        elif widget_name == 'search_screen' and widget.widget(widget.currentIndex() - 1).objectName() == 'search_screen':
            global searchterm
            search_list.pop()
            searchterm = search_list[-1]
            if len(searchterm):
                logging.info(f"Searching for '{searchterm}'")
                QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
                response = requests.get(
                    f"https://www.googleapis.com/books/v1/volumes?q={searchterm}&maxResults=40").json()
                search_screen = SearchScreen(response, True)
                widget.removeWidget(widget.currentWidget())
                widget.removeWidget(widget.currentWidget())
                widget.addWidget(search_screen)
                widget.setCurrentIndex(widget.currentIndex() + 1)
        else:
            widget.removeWidget(widget.currentWidget())


class UserManagement(QDialog):
    def __init__(self):
        super(UserManagement, self).__init__()
        loadUi(resource_path('assets/ui/user-management.ui'), self)
        users_list = bgfns.banlist()
        users_list.sort(key=lambda x: x[1])
        i = 0
        for user in users_list:
            self.user = QtWidgets.QLabel(self.bgwidget)
            self.user.setGeometry(QtCore.QRect(270, 530 + (i * 70), 431, 51))
            self.user.setStyleSheet("border-radius: 18px;\n"
                                    "background-color: rgba(238, 2, 73, 0);\n"
                                    "font: 18pt \"MS Shell Dlg 2\";\n"
                                    "color: rgb(255, 255, 255);")
            self.user.setScaledContents(True)
            self.user.setAlignment(QtCore.Qt.AlignLeading | QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
            self.user.setObjectName(f"user_{user[0]}")
            self.ban_user = QtWidgets.QPushButton(self.bgwidget)
            self.ban_user.setGeometry(QtCore.QRect(730, 535 + (i * 70), 151, 41))
            self.ban_user.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
            self.ban_user.setStyleSheet("border-radius: 5px;\n"
                                        "font: 14pt \"MS Shell Dlg 2\";\n"
                                        "color: rgb(255, 255, 255);\n"
                                        "border: 1px solid rgb(238, 2, 73);\n"
                                        "padding-bottom: 4px;\n"
                                        "")
            _translate = QtCore.QCoreApplication.translate
            self.user.setText(_translate("Dialog", user[0]))
            if user[1]:
                self.ban_user.setObjectName(f"unban_{user[0]}")
                self.ban_user.setText(_translate("Dialog", "Unban user"))
            else:
                self.ban_user.setObjectName(f"ban_{user[0]}")
                self.ban_user.setText(_translate("Dialog", "Ban user"))
            i += 1

        if len(users_list) > 3:
            self.scrollAreaWidgetContents.resize(1198, 900 + ((len(users_list) - 4) * 70))
            self.bgwidget.resize(1200, 900 + ((len(users_list) - 4) * 70))

        menu_button_redirector(self)
        for button in self.bgwidget.findChildren(QtWidgets.QPushButton):
            button.clicked.connect(partial(self.update_ban_list))

    def update_ban_list(self):
        if 'ban' in self.sender().objectName():
            user = self.sender().objectName().split('_', 1)
            if 'unban' in user[0]:
                bgfns.ban(user[1], 0)
                logging.info(f'Unbanned user {user[1]}')
            else:
                bgfns.ban(user[1], 1)
                logging.info(f'Banned user {user[1]}')
            MainScreen.gotousermanagement()


class SearchScreen(QDialog):
    def __init__(self, response, search, list_num=0):
        global thumbnail_list, title_list, authors_list, publisher_list, desc_list, lang_list, book_id_list, search_list
        super(SearchScreen, self).__init__()
        user_lists = [bgfns.list_toggle(username, False, '', 'LIKEBOOK'),
                      bgfns.list_toggle(username, False, '', 'READBOOK'),
                      bgfns.list_toggle(username, False, '', 'WANTBOOK')]
        if search:
            loadUi(resource_path('assets/ui/search-screen.ui'), self)
            self.search_line_edit.setText(searchterm)
            search_list = search_list + [searchterm]
            iter_no = 40
        else:
            loadUi(resource_path('assets/ui/user-list-screen.ui'), self)
            iter_no = len(user_lists[list_num])
            if list_num == 1:
                self.title_label.setText('Read books')
                self.setWindowTitle('Read books')
            elif list_num == 2:
                self.title_label.setText('Read Later')
                self.setWindowTitle('Read Later')
        thumbnail_list = title_list = authors_list = publisher_list = desc_list = lang_list = book_id_list = []
        for i in range(iter_no):
            try:
                book_info = response['items'][i]
            except:
                break
            try:
                book_id = book_info['id']
                title = book_info['volumeInfo']['title']
                thumbnail = book_info['volumeInfo']['imageLinks']['thumbnail']
                authors = ', '.join(book_info['volumeInfo']['authors'])
                desc = book_info['volumeInfo']['description']
                lang = pycountry.languages.get(alpha_2=book_info['volumeInfo']['language']).name
            except:
                continue
            try:
                publisher = book_info['volumeInfo']['publisher']
            except:
                publisher = 'Centry Publication House'
            thumbnail_list = thumbnail_list + [thumbnail]
            title_list = title_list + [title]
            authors_list = authors_list + [authors]
            publisher_list = publisher_list + [publisher]
            desc_list = desc_list + [desc]
            lang_list = lang_list + [lang]
            book_id_list = book_id_list + [book_id]
        threads = []
        for j in range(len(thumbnail_list)):
            self.label = QtWidgets.QLabel(self.bgwidget)
            self.label.setObjectName("label_book_" + str(j + 1))
            self.button = QtWidgets.QPushButton(self.bgwidget)
            self.button.setObjectName("button_book_" + str(j + 1))
            self.plainTextEdit = QtWidgets.QPlainTextEdit(self.bgwidget)
            self.plainTextEdit.setObjectName("plain_text_book_" + str(j + 1))
            t = Thread(target=self.download_thumbnails, args=(j, ))
            threads.append(t)
        for x in threads:
            x.start()
        for x in threads:
            x.join()
        if not title_list:
            self.error_label = QtWidgets.QLabel(self.bgwidget)
            self.error_label.setGeometry(QtCore.QRect(0, 360, 1171, 131))
            self.error_label.setAlignment(QtCore.Qt.AlignCenter)
            self.error_label.setStyleSheet("font: 16pt \"Roboto\";\n"
                                           "color: rgb(255, 0, 0);")
            self.error_label.setObjectName("error_label")
            if search:
                self.error_label.setText(
                    QtCore.QCoreApplication.translate("Dialog", "No results containing your search term were found"))
            else:
                self.error_label.setText(
                    QtCore.QCoreApplication.translate("Dialog", "No books added"))
        elif len(title_list) > 10:
            self.scrollAreaWidgetContents.resize(1200, 1150 + (len(title_list) - 11) // 5 * 300)
            self.bgwidget.resize(1200, 1150 + (len(title_list) - 11) // 5 * 300)
        QApplication.restoreOverrideCursor()
        if search:
            self.search_button.clicked.connect(self.search_function)
            self.search_line_edit.returnPressed.connect(self.search_function)
        for button in self.bgwidget.findChildren(QtWidgets.QPushButton):
            button.clicked.connect(partial(self.check_clicked))
        menu_button_redirector(self)

    def download_thumbnails(self, j):
        label = self.findChild(QtWidgets.QLabel, "label_book_" + str(j + 1))
        label.setGeometry(QtCore.QRect(100 + ((j % 5) * 200), 210 + ((j // 5) * 300), 128, 190))
        label.setText('')
        image = QtGui.QImage()
        image.loadFromData(requests.get(thumbnail_list[j]).content)
        label.setPixmap(QtGui.QPixmap(image))
        label.setScaledContents(True)
        button = self.findChild(QtWidgets.QPushButton, "button_book_" + str(j + 1))
        button.setGeometry(QtCore.QRect(100 + ((j % 5) * 200), 210 + ((j // 5) * 300), 128, 190))
        button.setStyleSheet("background-color: rgba(0, 0, 0, 0);")
        button.setText("")
        button.setCursor(QCursor(QtCore.Qt.PointingHandCursor))
        plain_text_edit = self.findChild(QtWidgets.QPlainTextEdit, "plain_text_book_" + str(j + 1))
        plain_text_edit.setGeometry(QtCore.QRect(100 + ((j % 5) * 200), 400 + ((j // 5) * 300), 128, 87))
        plain_text_edit.setStyleSheet("background-color: rgba(0, 0, 0, 0);"
                                         "color: white;"
                                         "border: None;"
                                         "font: 9pt \"MS Shell Dlg 2\";")
        plain_text_edit.setPlainText(QtCore.QCoreApplication.translate("Dialog", title_list[j]))
        plain_text_edit.setReadOnly(True)

    def search_function(self):
        global searchterm
        searchterm = self.search_line_edit.text()
        if len(searchterm):
            logging.info(f"Searching for '{searchterm}'")
            QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
            response = requests.get(f"https://www.googleapis.com/books/v1/volumes?q={searchterm}&maxResults=40").json()
            search_screen = SearchScreen(response, True)
            widget.addWidget(search_screen)
            widget.setCurrentIndex(widget.currentIndex() + 1)

    def check_clicked(self):
        try:
            button_redirect = ButtonRedirect(int((self.sender().objectName())[12:]) - 1)
            widget.addWidget(button_redirect)
            widget.setCurrentIndex(widget.currentIndex() + 1)
            bgfns.book_onclick(username, book_id_list[int((self.sender().objectName())[12:]) - 1])
        except:
            pass

    @staticmethod
    def gotouserlists(num):
        items = []
        QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        user_lists = [bgfns.list_toggle(username, False, '', 'LIKEBOOK'),
                      bgfns.list_toggle(username, False, '', 'READBOOK'),
                      bgfns.list_toggle(username, False, '', 'WANTBOOK')]
        for book_id in user_lists[num]:
            resp = requests.get(f"https://www.googleapis.com/books/v1/volumes/{book_id}").json()
            items = items + [resp]
        response = {'items': items}
        search_screen = SearchScreen(response, False, num)
        widget.addWidget(search_screen)
        widget.setCurrentIndex(widget.currentIndex() + 1)


class ButtonRedirect(QDialog):
    def __init__(self, button_num):
        super(ButtonRedirect, self).__init__()
        loadUi(resource_path('assets/ui/expanded-book.ui'), self)
        _translate = QtCore.QCoreApplication.translate
        self.book_thumbnail = QtWidgets.QLabel(self.bgwidget)
        self.book_thumbnail.setGeometry(QtCore.QRect(70, 70, 320, 475))
        self.book_thumbnail.setText("")
        image = QtGui.QImage()
        image.loadFromData(requests.get(thumbnail_list[button_num]).content)
        self.book_thumbnail.setPixmap(QtGui.QPixmap(image))
        self.book_thumbnail.setScaledContents(True)
        self.book_thumbnail.setObjectName("book_thumbnail")
        self.book_title = QtWidgets.QPlainTextEdit(self.bgwidget)
        self.book_title.setGeometry(QtCore.QRect(450, 90, 631, 87))
        self.book_title.setStyleSheet("color: #f0f0f0;\n"
                                      "font: 15pt \"MS Shell Dlg 2\";\n"
                                      "background-color: rgba(0, 0, 0, 0);\n"
                                      "border: None;")
        self.book_title.setObjectName("book_title")
        self.book_description = QtWidgets.QPlainTextEdit(self.bgwidget)
        self.book_description.setGeometry(QtCore.QRect(440, 380, 731, 401))
        self.book_description.setStyleSheet("color: #ebebeb;\n"
                                            "font: 15pt \"MS Shell Dlg 2\";\n"
                                            "background-color: rgba(0, 0, 0, 0);\n"
                                            "border: None;")
        self.book_description.setObjectName("book_description")
        self.Comment_as_label.setText(f'Comment as {username}')
        try:
            self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 1198, 1100 + (
                    170 * len(bgfns.insertcomment(book_id_list[button_num], False)))))
            self.bgwidget.setGeometry(QtCore.QRect(0, 0, 1198, 1100 + (
                    170 * len(bgfns.insertcomment(book_id_list[button_num], False)))))
            for i in range(len(bgfns.insertcomment(book_id_list[button_num], False))):
                self.comment = QtWidgets.QPlainTextEdit(self.bgwidget)
                self.comment.setGeometry(QtCore.QRect(170, 1140 + (150 * i), 931, 91))
                self.comment.setStyleSheet("background-color: #00000000;\n"
                                           "border: None;\n"
                                           "color: white;\n"
                                           "font: 10pt \"MS Shell Dlg 2\";")
                self.comment.setObjectName(f"comment_{i + 1}")
                self.default_avatar = QtWidgets.QLabel(self.bgwidget)
                self.default_avatar.setGeometry(QtCore.QRect(70, 1100 + (150 * i), 71, 71))
                self.default_avatar.setText("")
                self.default_avatar.setPixmap(QtGui.QPixmap(resource_path("assets/images/default avatar.png")))
                self.default_avatar.setScaledContents(True)
                self.default_avatar.setObjectName(f"default_avatar_{i + 1}")
                self.username = QtWidgets.QLabel(self.bgwidget)
                self.username.setGeometry(QtCore.QRect(175, 1110 + (150 * i), 1061, 21))
                self.username.setStyleSheet("color: rgb(238, 2, 73);\n"
                                            "font: 10pt \"MS Shell Dlg 2\";")
                self.username.setObjectName(f"username_{i + 1}")
                self.comment.setPlainText(
                    _translate("Dialog", bgfns.insertcomment(book_id_list[button_num], False)[i][1]))
                self.comment.setReadOnly(True)
                self.username.setText(
                    _translate("Dialog", bgfns.insertcomment(book_id_list[button_num], False)[i][0]))
                if username in admin_list or username == bgfns.insertcomment(book_id_list[button_num], False)[i][0]:
                    self.remove_icon = QtWidgets.QLabel(self.bgwidget)
                    self.remove_icon.setGeometry(QtCore.QRect(740, 1110 + (150 * i), 20, 20))
                    self.remove_icon.setText("")
                    self.remove_icon.setPixmap(QtGui.QPixmap(resource_path("assets/images/remove_icon.png")))
                    self.remove_icon.setScaledContents(True)
                    self.remove_icon.setObjectName(f"remove_icon_{i + 1}")
                    self.remove_text = QtWidgets.QLabel(self.bgwidget)
                    self.remove_text.setGeometry(QtCore.QRect(770, 1110 + (150 * i), 61, 20))
                    self.remove_text.setStyleSheet("color: white; font: 10pt \"MS Shell Dlg 2\";")
                    self.remove_text.setObjectName(f"remove_text_{i + 1}")
                    self.remove_text.setText(_translate("Dialog", "Remove"))
                    self.remove_button = QtWidgets.QPushButton(self.bgwidget)
                    self.remove_button.setGeometry(QtCore.QRect(740, 1110 + (150 * i), 91, 21))
                    self.remove_button.setStyleSheet("#remove_button_" + str(i + 1) + " {background-color: #00000000;}")
                    self.remove_button.setText("")
                    self.remove_button.setObjectName(f"remove_button_{i + 1}")
                    self.remove_button.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
                    if username in admin_list:
                        self.ban_icon = QtWidgets.QLabel(self.bgwidget)
                        self.ban_icon.setGeometry(QtCore.QRect(860, 1110 + (150 * i), 23, 23))
                        self.ban_icon.setText("")
                        self.ban_icon.setPixmap(QtGui.QPixmap(resource_path("assets/images/ban_icon.png")))
                        self.ban_icon.setScaledContents(True)
                        self.ban_icon.setObjectName(f"ban_icon_{i + 1}")
                        self.ban_text = QtWidgets.QLabel(self.bgwidget)
                        self.ban_text.setGeometry(QtCore.QRect(890, 1110 + (150 * i), 130, 20))
                        self.ban_text.setStyleSheet("color: white; font: 10pt \"MS Shell Dlg 2\";")
                        self.ban_text.setObjectName(f"ban_text_{i + 1}")
                        self.ban_button = QtWidgets.QPushButton(self.bgwidget)
                        self.ban_button.setGeometry(QtCore.QRect(860, 1110 + (150 * i), 101, 21))
                        self.ban_button.setObjectName(f"ban_button_{i + 1}")
                        self.ban_button.setStyleSheet("background-color: #00000000;")
                        self.ban_button.setText("")
                        if not bgfns.login(bgfns.insertcomment(book_id_list[button_num], False)[i][0])[2]:
                            self.ban_text.setText(_translate("Dialog", "Ban User"))
                        else:
                            self.ban_text.setText(_translate("Dialog", "Unban User"))
                        self.ban_button.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        except:
            pass
        self.book_title.setPlainText(_translate("Dialog", title_list[button_num]))
        self.book_title.setReadOnly(True)
        self.book_description.setPlainText(_translate("Dialog", desc_list[button_num]))
        self.book_description.setReadOnly(True)
        self.book_publisher.setText(_translate("Dialog", "Publisher: " + publisher_list[button_num]))
        self.book_author.setText(_translate("Dialog", "Author: " + authors_list[button_num]))
        self.book_language.setText(_translate("Dialog", "Language: " + lang_list[button_num]))
        self.fav_button.setText(_translate("Dialog", "Add to Favourites"))
        self.my_read_button.setText(_translate("Dialog", "Add to Read books"))
        self.read_list_button.setText(_translate("Dialog", "Add to Read later"))
        button_clicked_style = 'border-radius: 5px;' \
                               'font: 14pt "MS Shell Dlg 2";' \
                               'color: rgb(255, 255, 255);' \
                               'border: 1px solid rgb(238, 2, 73);' \
                               'background-color: rgb(238, 2, 73);'
        if book_id_list[button_num] in bgfns.list_toggle(username, False, '', 'LIKEBOOK'):
            self.fav_button.setStyleSheet(button_clicked_style)
        if book_id_list[button_num] in bgfns.list_toggle(username, False, '', 'READBOOK'):
            self.my_read_button.setStyleSheet(button_clicked_style)
        if book_id_list[button_num] in bgfns.list_toggle(username, False, '', 'WANTBOOK'):
            self.read_list_button.setStyleSheet(button_clicked_style)
        menu_button_redirector(self)
        self.fav_button.clicked.connect(lambda: self.change_toggle(button_num, 'LIKEBOOK'))
        self.my_read_button.clicked.connect(lambda: self.change_toggle(button_num, 'READBOOK'))
        self.read_list_button.clicked.connect(lambda: self.change_toggle(button_num, 'WANTBOOK'))
        self.comment_submit_button.clicked.connect(lambda: self.add_comment(button_num))
        for button in self.bgwidget.findChildren(QtWidgets.QPushButton):
            button.clicked.connect(partial(lambda: self.check_clicked(button_num)))

    def change_toggle(self, num, toggle_type):
        if book_id_list[num] in bgfns.list_toggle(username, False, '', toggle_type):
            bgfns.list_toggle(username, True, book_id_list[num], toggle_type)
            self.sender().setStyleSheet('border-radius: 5px;'
                                        'font: 14pt "MS Shell Dlg 2";'
                                        'color: rgb(255, 255, 255);'
                                        'border: 1px solid rgb(238, 2, 73);')
        else:
            bgfns.list_toggle(username, True, book_id_list[num], toggle_type)
            self.sender().setStyleSheet('border-radius: 5px;'
                                        'font: 14pt "MS Shell Dlg 2";'
                                        'color: rgb(255, 255, 255);'
                                        'border: 1px solid rgb(238, 2, 73);'
                                        'background-color: rgb(238, 2, 73);')

    @staticmethod
    def gotouserlists(num):
        items = []
        QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        user_lists = [bgfns.list_toggle(username, False, '', 'LIKEBOOK'),
                      bgfns.list_toggle(username, False, '', 'READBOOK'),
                      bgfns.list_toggle(username, False, '', 'WANTBOOK')]
        for book_id in user_lists[num]:
            resp = requests.get(f"https://www.googleapis.com/books/v1/volumes/{book_id}").json()
            items = items + [resp]
        response = {'items': items}
        search_screen = SearchScreen(response, False, num)
        widget.addWidget(search_screen)
        widget.setCurrentIndex(widget.currentIndex() + 1)

    def add_comment(self, num):
        comment = self.comment_input_text_edit.toPlainText()
        bgfns.insertcomment(book_id_list[num], True, username, comment)
        logging.info(f'New comment posted by {username}')
        widget.addWidget(ButtonRedirect(num))
        widget.setCurrentIndex(widget.currentIndex() + 1)

    def check_clicked(self, button_num):
        button = ["".join(x) for _, x in groupby(self.sender().objectName(), key=str.isdigit)]
        if 'remove_button_' in button:
            comments_list = bgfns.insertcomment(book_id_list[button_num], False)
            bgfns.insertcomment(book_id_list[button_num], True, comments_list[int(button[1]) - 1][0], '')
            logging.info(f"{comments_list[int(button[1]) - 1][0]}'s comment was removed by {username}")
            widget.addWidget(ButtonRedirect(button_num))
            widget.setCurrentIndex(widget.currentIndex() + 1)
        elif 'ban_button_' in button:
            comments_list = bgfns.insertcomment(book_id_list[button_num], False)
            _translate = QtCore.QCoreApplication.translate
            if bgfns.login(bgfns.insertcomment(book_id_list[button_num], False)[int(button[1]) - 1][0])[2]:
                bgfns.ban(comments_list[int(button[1]) - 1][0], 0)
                logging.info(
                    f'Unbanned user {bgfns.insertcomment(book_id_list[button_num], False)[int(button[1]) - 1][0]}')
            else:
                bgfns.ban(comments_list[int(button[1]) - 1][0], 1)
                logging.info(
                    f'Banned user {bgfns.insertcomment(book_id_list[button_num], False)[int(button[1]) - 1][0]}')
            widget.addWidget(ButtonRedirect(button_num))
            widget.setCurrentIndex(widget.currentIndex() + 1)


def menu_button_redirector(self):
    self.menu_home.clicked.connect(MainScreen.gotomenu)
    self.menu_fav.clicked.connect(lambda: MainScreen.gotouserlists(0))
    self.menu_my_read.clicked.connect(lambda: MainScreen.gotouserlists(1))
    self.menu_read_list.clicked.connect(lambda: MainScreen.gotouserlists(2))
    self.menu_sign_out.clicked.connect(WelcomeScreen.gotologin)
    self.back_icon_button.clicked.connect(MainScreen.goback)


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


thumbnail_list = title_list = authors_list = publisher_list = desc_list = lang_list = book_id_list = search_list = []
admin_list = ['root']
username = searchterm = ''
if __name__ == '__main__':
    app = QApplication(sys.argv)
    try:
        logging.info('Found file creds.bin.')
        welcome = WelcomeScreen()
    except:
        logging.info('File creds.bin not created.')
        welcome = SQLScreen()
    widget = QtWidgets.QStackedWidget()
    widget.addWidget(welcome)
    widget.setFixedHeight(800)
    widget.setFixedWidth(1200)
    widget.setWindowIcon(QtGui.QIcon(resource_path('assets/images/app.ico')))
    widget.setWindowTitle('Bookipedia')
    widget.show()
    try:
        sys.exit(app.exec_())
    except:
        logging.info('Application closing...')
        try:
            bgfns.eradicate()
            logging.info('Cleared cache')
        except:
            pass
