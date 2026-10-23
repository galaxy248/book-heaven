import sys, os, json
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, \
                            QMainWindow, QLabel, QLineEdit, QMessageBox, \
                            QErrorMessage, QTreeWidget, QTreeWidgetItem, \
                            QMdiArea, QToolBox, QComboBox, QCheckBox, \
                            QSpinBox, QTableWidget, QTableWidgetItem, \
                            QPlainTextEdit, QRadioButton, QGroupBox
from PyQt6.QtGui import QIcon, QPixmap, QStandardItem, QAction
from PyQt6 import uic
import requests
from pathlib import Path
import re
from dotenv import load_dotenv

from theme import apply_theme, get_saved_theme, save_theme, get_icon_path


root_dir = Path(__file__).parent
load_dotenv(root_dir / '.env')
load_dotenv(root_dir.parent / '.env')

REQUEST_HOST = os.getenv('REQUEST_HOST', 'http://127.0.0.1:8080').rstrip('/')

class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.root_path = Path(__file__).parent
        self._sign_in_page = None
        self._profile_page = None
        self._warehouse_page = None
        self._book_list_page = None
        self._cart_page = None
        self._settings_page = None
        self.orders = None
        self.sign_in_again = False

        apply_theme(get_saved_theme(self.root_path))

        self._check_jwt(self.root_path)

        if self._sign_in_page is None:
            self.show_main_page(self.rule)
    
    def _load_styles(self):
        pass

    def _find_all_components(self):
        self.profile_logo: QLabel = self.findChild(QLabel, 'profile_logo')
        self.cart_logo: QLabel = self.findChild(QLabel, 'cart_logo')
        self.warehouse_logo: QLabel = self.findChild(QLabel, 'warehouse_logo')
        self.book_list_logo: QLabel = self.findChild(QLabel, 'book_list_logo')
        self.settings_logo: QLabel = self.findChild(QLabel, 'settings_logo')
        self.orders_logo: QLabel = self.findChild(QLabel, 'orders_logo')

        self.profile_label: QLabel = self.findChild(QLabel, 'profile_label')
        self.cart_label: QLabel = self.findChild(QLabel, 'cart_label')
        self.warehouse_label: QLabel = self.findChild(QLabel, 'warehouse_label')
        self.book_list_label: QLabel = self.findChild(QLabel, 'book_list_label')
        self.settings_label: QLabel = self.findChild(QLabel, 'settings_label')
        self.orders_label: QLabel = self.findChild(QLabel, 'orders_label')

        self.actionExit: QAction = self.findChild(QAction, 'actionExit')
    
    def _load_pics_to_labels(self):
        if self.profile_logo:
            self.profile_logo.setPixmap(QPixmap(get_icon_path(self.root_path, 'user-profile-96.png')))
        if self.cart_logo:
            self.cart_logo.setPixmap(QPixmap(get_icon_path(self.root_path, 'cart-80.png')))
        if self.warehouse_logo:
            self.warehouse_logo.setPixmap(QPixmap(get_icon_path(self.root_path, 'warehouse-96.png')))
        if self.book_list_logo:
            self.book_list_logo.setPixmap(QPixmap(get_icon_path(self.root_path, 'book-100.png')))
        if self.settings_logo:
            self.settings_logo.setPixmap(QPixmap(get_icon_path(self.root_path, 'settings-80.png')))
        if self.orders_logo:
            self.orders_logo.setPixmap(QPixmap(get_icon_path(self.root_path, 'order-list-80.png')))

    def refresh_theme_icons(self):
        self._load_pics_to_labels()
        for attr in ('_profile_page', '_settings_page', '_book_list_page'):
            win = getattr(self, attr, None)
            if win is not None and hasattr(win, '_load_icons'):
                try:
                    win._load_icons()
                except Exception:
                    pass

    def _set_functions(self):
        if self.profile_logo:
            self.profile_logo.mousePressEvent = self.open_profile
        if self.cart_logo:
            self.cart_logo.mousePressEvent = self.open_cart
        if self.warehouse_logo:
            self.warehouse_logo.mousePressEvent = self.open_warehouse
        if self.book_list_logo:
            self.book_list_logo.mousePressEvent = self.open_book_list
        if self.settings_logo:
            self.settings_logo.mousePressEvent = self.open_settings
        if self.orders_logo:
            self.orders_logo.mousePressEvent = self.open_orders
        if self.actionExit:
            self.actionExit.triggered.connect(self.close)

    def closeEvent(self, event):
        for attr in ('_profile_page', '_warehouse_page', '_settings_page', '_book_list_page', '_cart_page', 'orders', '_sign_in_page'):
            win = getattr(self, attr, None)
            if win is not None:
                try:
                    win.close()
                except Exception:
                    pass
        event.accept()

    def sign_out(self):
        try:
            os.remove(self.root_path / 'tmp/cart.json')
        except OSError:
            pass
        self.close()
        self._open_sign_in(self.root_path, sign_in_again=True)
    
    def open_profile(self, *args, **kwargs):
        try:
            res = requests.get(f'{REQUEST_HOST}/profile', data={"token": self._jwt_file})
        except requests.exceptions.ConnectionError:
            self.warning('Internet connection not found or server is down!')
            return

        if res.status_code == 400:
            app.exit(1)
        elif res.status_code == 401:
            if res.json().get('status') == 'invalied token':
                self.error('invalied token. please sign in again')
                self.sign_out()
        elif re.match(r'5\d\d', str(res.status_code)):
            self.warning(f'Server Error! <br> {res.json()}')
            return
        elif res.status_code == 302:
            self.error('expierd token. please sign in again')
            self.sign_out()
        elif res.status_code == 200:
            if self._profile_page is not None:
                try:
                    self._profile_page.close()
                except Exception:
                    pass
            self._profile_page = Profile(res.json()['profile'], self.root_path, self)

    def open_warehouse(self, *args, **kwargs):
        try:
            if self._warehouse_page is not None:
                try:
                    self._warehouse_page.close()
                except Exception:
                    pass
            self._warehouse_page = AdminWarehouse(self._jwt_file, self.root_path, self)
        except ConnectionError as ce:
            self.warning(str(ce))
        except Exception as e:
            self.warning(str(e))

    def open_cart(self, *args, **kwargs):
        try:
            if self._cart_page is None:
                self._cart_page = Cart(self._jwt_file)
            else:
                try:
                    self._cart_page.close()
                    del self._cart_page
                    self._cart_page = None
                except:
                    pass
                self._cart_page = Cart(self._jwt_file)
        except ConnectionError as ce:
            self.warning(str(ce))
        except Exception as e:
            self.info(str(e))

    def open_book_list(self, *args, **kwargs):
        try:
            if self._book_list_page is not None:
                try:
                    self._book_list_page.close()
                    del self._book_list_page
                    self._book_list_page = None
                except:
                    pass
            if getattr(self, 'rule', 'c') == 'a':
                self._book_list_page = AdminBooks(self._jwt_file, self.root_path, self)
            else:
                self._book_list_page = BookList(self._jwt_file)
        except ConnectionError as ce:
            self.warning(str(ce))

    def open_settings(self, *args, **kwargs):
        try:
            if self._settings_page is None:
                self._settings_page = Settings(self.root_path, self)
            else:
                try:
                    self._settings_page.close()
                except Exception:
                    pass
                self._settings_page = Settings(self.root_path, self)
        except Exception as e:
            self.warning(str(e))

    def open_orders(self, *args, **kwargs):
        try:
            res = requests.get(f'{REQUEST_HOST}/orders', data={"token": self._jwt_file})
        except requests.exceptions.ConnectionError as ce:
            self.warning('Internet connection not found or server is down!')
            return
        if res.status_code == 400:
            app.exit(1)
        elif res.status_code == 401:
            if res.json()['status'] == 'invalied token':
                self.error('invalied token. please sign in again')
                try:
                    if self.orders is not None:
                        self.orders.close()
                    del self.orders
                    self.orders = None
                except:
                    pass
                self.close()
                self._open_sign_in(self.root_path, sign_in_again=True)
        # elif res.status_code == 403:
        #     self.error('your account will be block because you change your access level')
        #     return
        elif re.match(r'5\d\d', str(res.status_code)):
            self.warning(f'Server Error! <br> {res.json()}')
            return
        elif res.status_code == 302:
            self.error('expierd token. please sign in again')
            try:
                if self.orders is not None:
                    self.orders.close()
                del self.orders
            except:
                pass
            self.close()
            self._open_sign_in(self.root_path, sign_in_again=True)
        elif res.status_code == 200:
            if self.orders is not None:
                try:
                    self.orders.close()
                except Exception:
                    pass
            self.orders = Orders(res.json()['orders'], self.root_path, self)
    
    def show_main_page(self, rule: str):
        self.rule = rule
        for child in list(self.findChildren((QWidget, QAction))):
            child.setParent(None)
        uic.loadUi(str(self.root_path / f'UI/main-{"u" if rule == "c" else rule}.ui'), self)
        self.setWindowTitle('Book Heaven')
        
        self._find_all_components()
        self._load_pics_to_labels()
        self._load_styles()
        self._set_functions()

        self.show()
    
    def link_handler(self, *arg, **kwargs):
        pass

    def _check_jwt(self, root_path: Path):
        try:
            with open(root_path / 'settings/jwt.txt', 'r', encoding='utf-8') as f:
                self._jwt_file: str = f.read().strip()
            with open(root_path / 'settings/rule.txt', 'r', encoding='utf-8') as f:
                self.rule: str = f.read().strip()
        except:
            self._open_sign_in(self.root_path)

    def _open_sign_in(self, root_path: Path, sign_in_again=False):
        if sign_in_again:
            self.sign_in_again = True
        
        try:
            os.remove(root_path / 'settings/jwt.txt')
        except OSError:
            pass
        try:
            os.remove(root_path / 'settings/rule.txt')
        except OSError:
            pass

        self._sign_in_page = SigIn(self.root_path, self)
        return


    def sign_in(self, user_pass: dict, root_path: Path):
        try:
            res = requests.get(f'{REQUEST_HOST}/signin', data=user_pass)
        except requests.exceptions.ConnectionError as ce:
            self.warning('Internet connection not found or server is down!')
            return 1
        if res.status_code == 400:
            app.exit(1)
        elif res.status_code == 401:
            if res.json()['status'] == 'invalied username or password':
                self.error('invalied username or password')
                return 1
        elif re.match(r'5\d\d', str(res.status_code)):
            self.warning(f'Server Error! <br> {res.json()}')
            return 1
        elif res.status_code == 200:
            (root_path / 'settings').mkdir(parents=True, exist_ok=True)
            with open(root_path / 'settings/jwt.txt', 'w', encoding='utf-8') as f:
                f.write(res.json()['token'][2:-1])
                self._jwt_file = str(res.json()['token'][2:-1])
            with open(root_path / 'settings/rule.txt', 'w', encoding='utf-8') as f:
                f.write(res.json()['rule'])
                self.rule = res.json()['rule'].strip()
            return 0
        
    def _sign_in_successed(self):
        if self._sign_in_page is not None:
            if hasattr(self._sign_in_page, '_sign_up_page') and self._sign_in_page._sign_up_page is not None:
                try:
                    self._sign_in_page._sign_up_page.sign_in_page = None
                    self._sign_in_page._sign_up_page.close()
                except Exception:
                    pass
                self._sign_in_page._sign_up_page = None
            try:
                self._sign_in_page.close()
            except Exception:
                pass
            self._sign_in_page = None
        with open(self.root_path / 'settings/rule.txt', 'r', encoding='utf-8') as f:
            rule = f.read().strip()
        self.show_main_page(rule)
        return

    def error(self, err_message: str='An error has occurred!'):
        msg_box = QMessageBox(self)
        msg_box.setWindowIcon(QIcon(str(self.root_path / "UI/images/error.png")))

        temp = [255, 255, 255] if get_saved_theme(self.root_path) == 'dark' else [int(i) for i in 'rgb(9, 38, 53)'.strip(
            'rgb').strip('()').split(',')]
        QMessageBox.critical(msg_box, 'Error',
                          f"""
            <font color='{'#%02x%02x%02x' % (temp[0], temp[1], temp[2])}'>
            <p>{err_message}</p>
            </font>
            <br>
            <font color='{'#%02x%02x%02x' % (temp[0], temp[1], temp[2])}'>
            <p>Please tap to OK button to continue...</p>
            </font>
        """)

        msg_box.setFixedSize(370, (err_message.count('<br>') + 2) * 100)
        msg_box.move(30, 800)

    def info(self, inf_message: str):
        msg_box = QErrorMessage(self)
        msg_box.setWindowIcon(QIcon(str(self.root_path / "UI/images/info.png")))
        msg_box.setWindowTitle('Info')

        temp = [255, 255, 255] if get_saved_theme(self.root_path) == 'dark' else [int(i) for i in 'rgb(9, 38, 53)'.strip(
            'rgb').strip('()').split(',')]
        msg_box.showMessage(f"""
            <font color='{'#%02x%02x%02x' % (temp[0], temp[1], temp[2])}'>
            <p>{inf_message}</p>
            </font>
            <font color='{'#%02x%02x%02x' % (temp[0], temp[1], temp[2])}'>
            <p>Please tap to OK button to close.</p>
            </font>
        """)
        msg_box.setFixedSize(370, (inf_message.count('<br>') + 2) * 100)
    
    def warning(self, war_message: str):
        msg_box = QErrorMessage(self)
        msg_box.setWindowIcon(QIcon(str(self.root_path / "UI/images/warning.png")))
        msg_box.setWindowTitle('Warning')

        temp = [255, 255, 255] if get_saved_theme(self.root_path) == 'dark' else [int(i) for i in 'rgb(9, 38, 53)'.strip(
            'rgb').strip('()').split(',')]
        msg_box.showMessage(f"""
            <font color='{'#%02x%02x%02x' % (temp[0], temp[1], temp[2])}'>
            <p>{war_message}</p>
            </font>
            <font color='{'#%02x%02x%02x' % (temp[0], temp[1], temp[2])}'>
            <p>Please tap to OK button to close.</p>
            </font>
        """)
        msg_box.setFixedSize(370, (war_message.count('<br>') + 2) * 100)


class SigIn(QWidget):
    def __init__(self, root_path: str = None, main_window: MainWindow = None) -> None:
        super().__init__()

        if main_window is None:
            raise ChildProcessError(f'You should pass main window argument.')
        else:
            self._main_window = main_window
        
        if root_path is None:
            self.root_path = Path(__file__).parent
        else:
            self.root_path = root_path
        
        uic.loadUi(self.root_path / 'UI/sign-in.ui', self)
        self.setWindowTitle('Sign In')
        
        self._load_styles()
        self._find_all_components()
        self._set_functions()
        
        self.show()

    def _load_styles(self):
        pass

    def _find_all_components(self):
        self.sign_in_btn: QPushButton = self.findChild(QPushButton, 'sign_in')
        self.sign_up_btn: QPushButton = self.findChild(QPushButton, 'sign_up')
        
        self.username_label: QLabel = self.findChild(QLabel, 'username_label')
        self.password_label: QLabel = self.findChild(QLabel, 'password_label')
        
        self.username_input: QLineEdit = self.findChild(QLineEdit, 'username_input')
        self.password_input: QLineEdit = self.findChild(QLineEdit, 'password_input')\
        
        self.logo: QLabel = self.findChild(QLabel, 'logo')
        self.logo.setPixmap(QPixmap(str(self.root_path / 'UI/images/logo-00.png')))

    def _set_functions(self):
        self.sign_in_btn.clicked.connect(self._sign_in)
        self.sign_up_btn.clicked.connect(self._sign_up)
    
    def _sign_up(self):
        self.hide()
        if not hasattr(self, '_sign_up_page') or self._sign_up_page is None:
            self._sign_up_page = SignUpUser(self.root_path, self)
        else:
            self._sign_up_page.show()

    def _sign_in(self):
        try:
            user_pass = self.get_sign_in_parameters()
        except ValueError as ve:
            self.error(str(ve))
            return

        check = self._main_window.sign_in(user_pass, self.root_path)
        if not check:
            self._main_window._sign_in_successed()
    
    def get_sign_in_parameters(self):
        username = self.username_input.text()
        password = self.password_input.text()
        if username == '' or password == '':
            raise ValueError('You should write a username or password.')
        else:
            return {
                'username': username,
                'password': password
            }

    def closeEvent(self, event):
        if hasattr(self, '_sign_up_page') and self._sign_up_page is not None:
            try:
                self._sign_up_page.sign_in_page = None
                self._sign_up_page.close()
            except Exception:
                pass
        event.accept()

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass

    def error(self, err_message: str='An error has occurred!'):
        msg_box = QMessageBox()
        msg_box.setWindowIcon(QIcon(str(self.root_path / "UI/images/error.png")))
        temp = [255, 255, 255] if get_saved_theme(self.root_path) == 'dark' else [int(i) for i in 'rgb(9, 38, 53)'.strip(
            'rgb').strip('()').split(',')]
        QMessageBox.critical(msg_box, 'Error',
                          f"""
            <font color='{'#%02x%02x%02x' % (temp[0], temp[1], temp[2])}'>
            <p>{err_message}</p>
            </font>
            <br>
            <font color='{'#%02x%02x%02x' % (temp[0], temp[1], temp[2])}'>
            <p>Please tap to OK button to continue...</p>
            </font>
        """)

        msg_box.setFixedSize(370, (err_message.count('<br>') + 2) * 100)
        msg_box.move(30, 800)


class SignUpUser(QWidget):
    def __init__(self, root_path: Path = None, sign_in_page: QWidget = None) -> None:
        super().__init__()

        self.sign_in_page = sign_in_page
        if root_path is None:
            self.root_path = Path(__file__).parent
        else:
            self.root_path = Path(root_path)

        uic.loadUi(self.root_path / 'UI/sign-up.ui', self)
        self.setWindowTitle('Sign Up')

        self._find_all_components()
        self._set_functions()

        self.show()

    def _find_all_components(self):
        self.logo: QLabel = self.findChild(QLabel, 'logo')
        if self.logo:
            self.logo.setPixmap(QPixmap(str(self.root_path / 'UI/images/logo-00.png')))

        self.name_input: QLineEdit = self.findChild(QLineEdit, 'name_input')
        self.last_name_input: QLineEdit = self.findChild(QLineEdit, 'last_name_input')
        self.email_input: QLineEdit = self.findChild(QLineEdit, 'email_input')
        self.using_email_for_uname_chbox: QCheckBox = self.findChild(QCheckBox, 'using_email_for_uname_chbox')
        self.username_input: QLineEdit = self.findChild(QLineEdit, 'username_input')
        self.password_input: QLineEdit = self.findChild(QLineEdit, 'password_input')
        self.phone_input: QLineEdit = self.findChild(QLineEdit, 'phone_input')
        self.address_plain_text: QPlainTextEdit = self.findChild(QPlainTextEdit, 'address_plain_text')

        self.signup_btn: QPushButton = self.findChild(QPushButton, 'signup')
        self.signin_btn: QPushButton = self.findChild(QPushButton, 'signin')

    def _set_functions(self):
        if self.signup_btn:
            self.signup_btn.clicked.connect(self._handle_signup)
        if self.signin_btn:
            self.signin_btn.clicked.connect(self._back_to_signin)
        if self.using_email_for_uname_chbox:
            self.using_email_for_uname_chbox.stateChanged.connect(self._toggle_email_as_username)
        if self.email_input:
            self.email_input.textChanged.connect(self._on_email_changed)

    def _toggle_email_as_username(self):
        if self.using_email_for_uname_chbox and self.using_email_for_uname_chbox.isChecked():
            if self.email_input:
                self.username_input.setText(self.email_input.text().strip())
            self.username_input.setEnabled(False)
        else:
            self.username_input.setEnabled(True)

    def _on_email_changed(self, text: str):
        if self.using_email_for_uname_chbox and self.using_email_for_uname_chbox.isChecked():
            self.username_input.setText(text.strip())

    def _back_to_signin(self):
        self.hide()
        if self.sign_in_page:
            self.sign_in_page.show()

    def closeEvent(self, event):
        if self.sign_in_page and not self.sign_in_page.isVisible():
            try:
                self.sign_in_page.close()
            except Exception:
                pass
        event.accept()

    def _handle_signup(self):
        name = self.name_input.text().strip() if self.name_input else ''
        last_name = self.last_name_input.text().strip() if self.last_name_input else ''
        email = self.email_input.text().strip() if self.email_input else ''
        username = self.username_input.text().strip() if self.username_input else ''
        password = self.password_input.text() if self.password_input else ''
        phone = self.phone_input.text().strip() if self.phone_input else ''
        address = self.address_plain_text.toPlainText().strip() if self.address_plain_text else ''

        if not all([name, last_name, email, username, password, phone]):
            self.error('Please fill in all required fields.')
            return

        if len(password) < 4:
            self.error('Password must be at least 4 characters.')
            return

        email_pattern = r'^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,4}$'
        if not re.match(email_pattern, email):
            self.error('Invalid email format (e.g. user@example.com).')
            return

        phone_pattern = r'(^(0?9)|(\+?989))\d{9}$'
        if not re.match(phone_pattern, phone):
            self.error('Invalid phone number format.<br>Must start with 09 or +989 followed by 9 digits.')
            return

        try:
            res = requests.post(f'{REQUEST_HOST}/signup', data={
                'username': username,
                'password': password,
                'name': name,
                'last_name': last_name,
                'email': email,
                'phone': phone,
                'address': address
            })
        except requests.exceptions.ConnectionError:
            self.error('Could not reach backend server.<br>Please ensure the Flask API is running.')
            return

        if res.status_code == 201:
            QMessageBox.information(self, 'Success', 'Account created successfully!<br>You can now sign in.')
            if self.sign_in_page:
                if hasattr(self.sign_in_page, 'username_input') and self.sign_in_page.username_input:
                    self.sign_in_page.username_input.setText(username)
                if hasattr(self.sign_in_page, 'password_input') and self.sign_in_page.password_input:
                    self.sign_in_page.password_input.clear()
            self._back_to_signin()
        else:
            try:
                err_data = res.json()
                msg = err_data.get('message', 'Failed to create account.')
            except Exception:
                msg = f'Server error: {res.text}'
            self.error(msg)

    def error(self, err_message: str = 'An error has occurred!'):
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Icon.Warning)
        msg_box.setWindowTitle('Error')
        msg_box.setText(err_message)
        msg_box.exec()


class Settings(QWidget):
    def __init__(self, root_path: Path = None, main_window: MainWindow = None) -> None:
        super().__init__()
        self._main_window = main_window
        if root_path is None:
            self.root_path = Path(__file__).parent
        else:
            self.root_path = Path(root_path)

        uic.loadUi(self.root_path / 'UI/settings.ui', self)
        self.setWindowTitle('Settings')

        self._find_all_components()
        self._load_current_settings()
        self._set_functions()

        self.show()

    def _find_all_components(self):
        self.settings_icon: QLabel = self.findChild(QLabel, 'settings_icon')
        self._load_icons()

        self.light_theme_radio: QRadioButton = self.findChild(QRadioButton, 'light_theme_radio')
        self.dark_theme_radio: QRadioButton = self.findChild(QRadioButton, 'dark_theme_radio')
        self.close_btn: QPushButton = self.findChild(QPushButton, 'close_btn')

    def _load_icons(self):
        if self.settings_icon:
            self.settings_icon.setPixmap(QPixmap(get_icon_path(self.root_path, 'settings-80.png')))

    def _load_current_settings(self):
        current_theme = get_saved_theme(self.root_path)
        if current_theme == 'dark':
            if self.dark_theme_radio:
                self.dark_theme_radio.setChecked(True)
        else:
            if self.light_theme_radio:
                self.light_theme_radio.setChecked(True)

    def _set_functions(self):
        if self.light_theme_radio:
            self.light_theme_radio.toggled.connect(self._on_theme_changed)
        if self.dark_theme_radio:
            self.dark_theme_radio.toggled.connect(self._on_theme_changed)
        if self.close_btn:
            self.close_btn.clicked.connect(self.close)

    def _on_theme_changed(self):
        if self.dark_theme_radio and self.dark_theme_radio.isChecked():
            theme = 'dark'
        else:
            theme = 'light'
        save_theme(self.root_path, theme)
        apply_theme(theme)
        self._load_icons()
        if self._main_window is not None:
            self._main_window.refresh_theme_icons()


class Profile(QWidget):
    def __init__(self, profile_data: dict, root_path: Path = None, main_window: MainWindow = None) -> None:
        super().__init__()
        if main_window is None:
            raise ChildProcessError('You should pass main window argument.')
        self._main_window = main_window

        if root_path is None:
            self.root_path = Path(__file__).parent
        else:
            self.root_path = Path(root_path)

        ui_file = 'profile-a.ui' if profile_data.get('rule') == 'a' else 'profile.ui'
        uic.loadUi(self.root_path / f'UI/{ui_file}', self)
        self.setWindowTitle('Profile')

        self._find_all_components()
        self._set_functions()
        self.load(profile_data)

        self.show()

    def _find_all_components(self):
        self.profile_logo: QLabel = self.findChild(QLabel, 'profile_logo')
        self._load_icons()

        self.name_input: QLineEdit = self.findChild(QLineEdit, 'name_input')
        self.last_name_input: QLineEdit = self.findChild(QLineEdit, 'last_name_input')
        self.username_input: QLineEdit = self.findChild(QLineEdit, 'username_input')
        self.orders_count_input: QLineEdit = self.findChild(QLineEdit, 'orders_count_input')
        self.national_id_input: QLineEdit = self.findChild(QLineEdit, 'national_id_input')
        self.workplace_input: QLineEdit = self.findChild(QLineEdit, 'workplace_input')
        self.salary_input: QLineEdit = self.findChild(QLineEdit, 'salary_input')
        self.bank_account_input: QLineEdit = self.findChild(QLineEdit, 'bank_account_input')
        self.email_input: QLineEdit = self.findChild(QLineEdit, 'email_input')
        self.phone_input: QLineEdit = self.findChild(QLineEdit, 'phone_input')
        self.address_plain_text: QPlainTextEdit = self.findChild(QPlainTextEdit, 'address_plain_text')

        self.sign_out_btn: QPushButton = self.findChild(QPushButton, 'sign_out')

    def _load_icons(self):
        if self.profile_logo:
            self.profile_logo.setPixmap(QPixmap(get_icon_path(self.root_path, 'user-profile-96.png')))

    def _set_functions(self):
        if self.sign_out_btn:
            self.sign_out_btn.clicked.connect(self._sign_out)

    def load(self, profile_data: dict):
        if self.name_input:
            self.name_input.setText(str(profile_data.get('name', '')))
        if self.last_name_input:
            self.last_name_input.setText(str(profile_data.get('last_name', '')))
        if self.username_input:
            self.username_input.setText(str(profile_data.get('username', '')))
        if self.orders_count_input:
            self.orders_count_input.setText(str(profile_data.get('orders_count', 0)))
        if self.national_id_input:
            self.national_id_input.setText(str(profile_data.get('national_id', '')))
        if self.workplace_input:
            self.workplace_input.setText(str(profile_data.get('workplace', '')))
        if self.salary_input:
            self.salary_input.setText(str(profile_data.get('salary', '')))
        if self.bank_account_input:
            self.bank_account_input.setText(str(profile_data.get('bank_account_number', '')))
        if self.email_input:
            self.email_input.setText(str(profile_data.get('email', '')))
        if self.phone_input:
            self.phone_input.setText(str(profile_data.get('phone', '')))
        if self.address_plain_text:
            self.address_plain_text.setPlainText(str(profile_data.get('address', '')))

    def _sign_out(self):
        self.close()
        if self._main_window is not None:
            self._main_window.sign_out()


class AdminWarehouse(QWidget):
    def __init__(self, jwt_token: str, root_path: Path = None, main_window: MainWindow = None) -> None:
        super().__init__()
        self._jwt_token = jwt_token
        self._main_window = main_window
        self.root_path = Path(root_path) if root_path else Path(__file__).parent

        uic.loadUi(self.root_path / 'UI/warehouse-a.ui', self)
        self.setWindowTitle('Warehouse')

        self._find_all_components()
        self._set_functions()
        self.load_inventory()
        self.show()

    def _find_all_components(self):
        self.warehouse_title_label: QLabel = self.findChild(QLabel, 'warehouse_title_label')
        self.inventory_list: QTableWidget = self.findChild(QTableWidget, 'inventory_list')
        self.isbn_input: QLineEdit = self.findChild(QLineEdit, 'isbn_input')
        self.count_spin_box: QSpinBox = self.findChild(QSpinBox, 'count_spin_box')
        self.update_button: QPushButton = self.findChild(QPushButton, 'update_button')
        self.add_book_button: QPushButton = self.findChild(QPushButton, 'add_book_button')
        self.cancel_button: QPushButton = self.findChild(QPushButton, 'cancel_button')

    def _set_functions(self):
        if self.update_button:
            self.update_button.clicked.connect(self._update_inventory)
        if self.add_book_button:
            self.add_book_button.clicked.connect(self._open_add_book)
        if self.cancel_button:
            self.cancel_button.clicked.connect(self.close)
        if self.inventory_list:
            self.inventory_list.itemClicked.connect(self._on_row_clicked)

    def _open_add_book(self):
        if self._main_window is not None:
            self._main_window.open_book_list()

    def _on_row_clicked(self, item):
        row = item.row()
        isbn_item = self.inventory_list.item(row, 0)
        count_item = self.inventory_list.item(row, 5)
        if isbn_item and self.isbn_input:
            self.isbn_input.setText(isbn_item.text())
        if count_item and self.count_spin_box:
            try:
                self.count_spin_box.setValue(int(count_item.text()))
            except ValueError:
                pass

    def load_inventory(self):
        try:
            res = requests.get(f'{REQUEST_HOST}/admin-warehouse', data={"token": self._jwt_token})
        except requests.exceptions.ConnectionError:
            if self._main_window:
                self._main_window.warning('Internet connection not found or server is down!')
            return

        if res.status_code == 200:
            data = res.json()
            if self.warehouse_title_label and data.get('warehouse_name'):
                self.warehouse_title_label.setText(str(data['warehouse_name']))
            self.inventory_list.setRowCount(0)
            for row_data in data.get('inventory', []):
                row = self.inventory_list.rowCount()
                self.inventory_list.insertRow(row)
                for col, val in enumerate(row_data):
                    cell = QTableWidgetItem(str(val))
                    cell.setFlags(cell.flags() ^ Qt.ItemFlag.ItemIsEditable)
                    self.inventory_list.setItem(row, col, cell)

    def _update_inventory(self):
        book_id = self.isbn_input.text().strip() if self.isbn_input else ''
        count = self.count_spin_box.value() if self.count_spin_box else 0
        if not book_id:
            if self._main_window:
                self._main_window.warning('Please enter or select a Book ISBN.')
            return

        try:
            res = requests.post(f'{REQUEST_HOST}/admin-warehouse', data={
                'token': self._jwt_token,
                'book_id': book_id,
                'count': str(count)
            })
        except requests.exceptions.ConnectionError:
            if self._main_window:
                self._main_window.warning('Internet connection not found or server is down!')
            return

        if res.status_code == 200:
            self.load_inventory()
            if self._main_window:
                self._main_window.info('Inventory count updated successfully.')
        else:
            msg = res.json().get('message', 'Failed to update inventory.')
            if self._main_window:
                self._main_window.warning(msg)


class AdminBooks(QWidget):
    def __init__(self, jwt_token: str, root_path: Path = None, main_window: MainWindow = None) -> None:
        super().__init__()
        self._jwt_token = jwt_token
        self._main_window = main_window
        self.root_path = Path(root_path) if root_path else Path(__file__).parent

        uic.loadUi(self.root_path / 'UI/books-a.ui', self)
        self.setWindowTitle('Book List')

        self._find_all_components()
        self._set_functions()
        self.load_books()
        self.show()

    def _find_all_components(self):
        self.books_table: QTableWidget = self.findChild(QTableWidget, 'books_table')
        self.isbn_input: QLineEdit = self.findChild(QLineEdit, 'isbn_input')
        self.title_input: QLineEdit = self.findChild(QLineEdit, 'title_input')
        self.author_input: QLineEdit = self.findChild(QLineEdit, 'author_input')
        self.publisher_input: QLineEdit = self.findChild(QLineEdit, 'publisher_input')
        self.edition_input: QLineEdit = self.findChild(QLineEdit, 'edition_input')
        self.year_spin_box: QSpinBox = self.findChild(QSpinBox, 'year_spin_box')
        self.price_input: QLineEdit = self.findChild(QLineEdit, 'price_input')
        self.count_spin_box: QSpinBox = self.findChild(QSpinBox, 'count_spin_box')
        self.add_book_button: QPushButton = self.findChild(QPushButton, 'add_book_button')
        self.close_button: QPushButton = self.findChild(QPushButton, 'close_button')

    def _set_functions(self):
        if self.add_book_button:
            self.add_book_button.clicked.connect(self._save_book)
        if self.close_button:
            self.close_button.clicked.connect(self.close)
        if self.books_table:
            self.books_table.itemClicked.connect(self._on_row_clicked)

    def _on_row_clicked(self, item):
        row = item.row()
        vals = [self.books_table.item(row, c).text() if self.books_table.item(row, c) else '' for c in range(7)]
        if self.isbn_input:
            self.isbn_input.setText(vals[0])
        if self.title_input:
            self.title_input.setText(vals[1])
        if self.author_input:
            self.author_input.setText(vals[2])
        if self.publisher_input:
            self.publisher_input.setText(vals[3])
        if self.edition_input:
            self.edition_input.setText(vals[4])
        if self.year_spin_box:
            try:
                self.year_spin_box.setValue(int(vals[5]))
            except ValueError:
                pass
        if self.price_input:
            self.price_input.setText(vals[6])

    def load_books(self):
        try:
            res = requests.get(f'{REQUEST_HOST}/admin-books', data={"token": self._jwt_token})
        except requests.exceptions.ConnectionError:
            if self._main_window:
                self._main_window.warning('Internet connection not found or server is down!')
            return

        if res.status_code == 200:
            self.books_table.setRowCount(0)
            for row_data in res.json().get('books', []):
                row = self.books_table.rowCount()
                self.books_table.insertRow(row)
                for col, val in enumerate(row_data):
                    cell = QTableWidgetItem(str(val))
                    cell.setFlags(cell.flags() ^ Qt.ItemFlag.ItemIsEditable)
                    self.books_table.setItem(row, col, cell)

    def _save_book(self):
        book_id = self.isbn_input.text().strip() if self.isbn_input else ''
        title = self.title_input.text().strip() if self.title_input else ''
        author = self.author_input.text().strip() if self.author_input else ''
        publisher = self.publisher_input.text().strip() if self.publisher_input else ''
        edition = self.edition_input.text().strip() if self.edition_input else ''
        year = str(self.year_spin_box.value()) if self.year_spin_box else '2024'
        price = self.price_input.text().strip() if self.price_input else ''
        count = str(self.count_spin_box.value()) if self.count_spin_box else '0'

        if not all([book_id, title, author, publisher, edition, price]):
            if self._main_window:
                self._main_window.warning('Please fill in all book fields.')
            return

        try:
            res = requests.post(f'{REQUEST_HOST}/admin-books', data={
                'token': self._jwt_token,
                'book_id': book_id,
                'title': title,
                'author': author,
                'publisher': publisher,
                'edition': edition,
                'year': year,
                'price': price,
                'count': count
            })
        except requests.exceptions.ConnectionError:
            if self._main_window:
                self._main_window.warning('Internet connection not found or server is down!')
            return

        if res.status_code in (200, 201):
            self.load_books()
            if self._main_window and getattr(self._main_window, '_warehouse_page', None) is not None:
                try:
                    self._main_window._warehouse_page.load_inventory()
                except Exception:
                    pass
            if self._main_window:
                self._main_window.info('Book saved and added to warehouse inventory.')
        else:
            msg = res.json().get('message', 'Failed to save book.')
            if self._main_window:
                self._main_window.warning(msg)


class Orders(QWidget):
    def __init__(self, orders: dict, root_path: str = None, main_window: MainWindow = None) -> None:
        super().__init__()

        if main_window is None:
            raise ChildProcessError(f'You should pass main window argument.')
        else:
            self._main_window = main_window
        
        if root_path is None:
            self.root_path = Path(__file__).parent
        else:
            self.root_path = root_path
        
        uic.loadUi(self.root_path / 'UI/orders.ui', self)
        self.setWindowTitle('Orders')
        self.show()
        
        self._load_styles()
        self._find_all_components()
        
        self.load(orders)
    
    def __del__(self):
        try:
            self.destroy()
        except Exception:
            pass

    def _load_styles(self):
        pass

    def _find_all_components(self):
        pass

    def load(self, orders: dict):

        tree: QTreeWidget = self.findChild(QTreeWidget, 'order_tree')

        for id in orders.keys():
            item = QTreeWidgetItem([f'{id}'])
            for order_detail in orders[id]:
                order_detail.insert(0, '')

                child = QTreeWidgetItem(map(str, order_detail))
                
                item.addChild(child)
                
            tree.addTopLevelItem(item)

        return

class BookList(QWidget):
    def __init__(self, jwt_token: str) -> None:
        super().__init__()
        self.root_path = Path(__file__).parent
        uic.loadUi(str(self.root_path / 'UI/mdi.ui'), self)
        self.setFixedSize(self.size())
        self._jwt_token = jwt_token
        self.setWindowTitle('Book List')

        self.warehouse_list = self.get_warehouse()

        if self.warehouse_list == False:
            raise ConnectionError('Internet connection not found or server is down!')
        
        self._find_all_components()
        self._load_styles()
        self._set_functions()
        self.search_books()
        self.show()

    def __del__(self):
        try:
            self.destroy()
        except Exception:
            pass

    def get_warehouse(self):
        try:
            temp = requests.get(f'{REQUEST_HOST}/get-warehouse').json()['warehouse']
        except requests.exceptions.ConnectionError as ce:
            return False
        
        return ['همه'] + [i[0] for i in temp]
    
    def error(self, err_message: str='An error has occurred!'):
        msg_box = QMessageBox(self)
        msg_box.setWindowIcon(QIcon(str(self.root_path / "UI/images/error.png")))

        temp = [255, 255, 255] if get_saved_theme(self.root_path) == 'dark' else [int(i) for i in 'rgb(9, 38, 53)'.strip(
            'rgb').strip('()').split(',')]
        QMessageBox.critical(msg_box, 'Error',
                          f"""
            <font color='{'#%02x%02x%02x' % (temp[0], temp[1], temp[2])}'>
            <p>{err_message}</p>
            </font>
            <br>
            <font color='{'#%02x%02x%02x' % (temp[0], temp[1], temp[2])}'>
            <p>Please tap to OK button to continue...</p>
            </font>
        """)

        msg_box.setFixedSize(370, (err_message.count('<br>') + 2) * 100)
        msg_box.move(30, 800)

    def info(self, inf_message: str):
        msg_box = QErrorMessage(self)
        msg_box.setWindowIcon(QIcon(str(self.root_path / "UI/images/info.png")))
        msg_box.setWindowTitle('Info')
        
        temp = [255, 255, 255] if get_saved_theme(self.root_path) == 'dark' else [int(i) for i in 'rgb(9, 38, 53)'.strip(
            'rgb').strip('()').split(',')]
        msg_box.showMessage(f"""
            <font color='{'#%02x%02x%02x' % (temp[0], temp[1], temp[2])}'>
            <p>{inf_message}</p>
            </font>
            <font color='{'#%02x%02x%02x' % (temp[0], temp[1], temp[2])}'>
            <p>Please tap to OK button to close.</p>
            </font>
        """)
        msg_box.setFixedSize(370, (inf_message.count('<br>') + 2) * 100)
    
    def warning(self, war_message: str):
        msg_box = QErrorMessage(self)
        msg_box.setWindowIcon(QIcon(str(self.root_path / "UI/images/warning.png")))
        msg_box.setWindowTitle('Warning')
        
        temp = [255, 255, 255] if get_saved_theme(self.root_path) == 'dark' else [int(i) for i in 'rgb(9, 38, 53)'.strip(
            'rgb').strip('()').split(',')]
        msg_box.showMessage(f"""
            <font color='{'#%02x%02x%02x' % (temp[0], temp[1], temp[2])}'>
            <p>{war_message}</p>
            </font>
            <font color='{'#%02x%02x%02x' % (temp[0], temp[1], temp[2])}'>
            <p>Please tap to OK button to close.</p>
            </font>
        """)
        msg_box.setFixedSize(370, (war_message.count('<br>') + 2) * 100)
    
    def _find_all_components(self):
        self.tool_box: QToolBox = self.findChild(QToolBox, 'tool_box')
        
        self.warehouse_combobox: QComboBox = self.findChild(QComboBox, 'warehouse_combobox')
        self.warehouse_combobox.addItems(self.warehouse_list)
        
        self.author_name: QLabel = self.findChild(QLabel, 'author_name')
        self.isbn_label: QLabel = self.findChild(QLabel, 'isbn_label')
        self.title_label: QLabel = self.findChild(QLabel, 'title_label')
        self.year_label: QLabel = self.findChild(QLabel, 'year_label')
        self.publisher_label: QLabel = self.findChild(QLabel, 'publisher_label')
        
        self.author_input: QLineEdit = self.findChild(QLineEdit, 'author_input')
        self.isbn_input: QLineEdit = self.findChild(QLineEdit, 'isbn_input')
        self.title_input: QLineEdit = self.findChild(QLineEdit, 'title_input')
        self.publisher_input: QLineEdit = self.findChild(QLineEdit, 'publisher_input')
        
        self.year_check_box: QCheckBox = self.findChild(QCheckBox, 'year_check_box')
        
        self.year_spin_box: QSpinBox = self.findChild(QSpinBox, 'year_spin_box')

        self.book_list: QTableWidget = self.findChild(QTableWidget, 'book_list')

        self.search_button: QPushButton = self.findChild(QPushButton, 'search_button')

        self.mdi: QMdiArea = self.findChild(QMdiArea, 'mdiArea')
        self._current_book_widget = None
        self._load_icons()

    def _load_icons(self):
        if self.tool_box:
            self.tool_box.setItemIcon(0, QIcon(get_icon_path(self.root_path, 'book-100.png')))
            self.tool_box.setItemIcon(1, QIcon(get_icon_path(self.root_path, 'pen-96.png')))
            self.tool_box.setItemIcon(2, QIcon(get_icon_path(self.root_path, 'publishing-128.png')))
            self.tool_box.setItemIcon(3, QIcon(get_icon_path(self.root_path, 'warehouse-96.png')))
        if self.search_button:
            self.search_button.setIcon(QIcon(get_icon_path(self.root_path, 'search-96.png')))
        if getattr(self, '_current_book_widget', None) is not None and hasattr(self._current_book_widget, '_load_icons'):
            try:
                self._current_book_widget._load_icons()
            except Exception:
                pass

    def _load_styles(self):
        pass

    def _set_functions(self):
        self.search_button.clicked.connect(self.search_books)
        self.book_list.itemDoubleClicked.connect(self.open_book_info)

    def search_books(self):
        search_params = self.get_search_parameters()
        
        try:
            res = requests.get(f'{REQUEST_HOST}/search', data=search_params)
        except requests.exceptions.ConnectionError as ce:
            self.warning('Internet connection not found or server is down!')
            return 1
        if res.status_code == 400:
            app.exit(1)
        elif re.match(r'5\d\d', str(res.status_code)):
            self.warning(f'Server Error! <br> {res.json()}')
            return 1
        elif res.status_code == 200:
            res = res.json()['books']

        for i in range(self.book_list.rowCount(), -1, -1):
            self.book_list.removeRow(i)

        for isbn, t, a, p, y in res:
            row = self.book_list.rowCount()
            self.book_list.insertRow(row)
            
            title = QTableWidgetItem(t)
            title.setSelected(False)
            title.setWhatsThis(isbn)
            title.setFlags(title.flags() ^ Qt.ItemFlag.ItemIsEditable)
            self.book_list.setItem(row, 0, title)

            author = QTableWidgetItem(a)
            author.setSelected(False)
            author.setWhatsThis(isbn)
            author.setFlags(author.flags() ^ Qt.ItemFlag.ItemIsEditable)
            self.book_list.setItem(row, 1, author)

            publisher = QTableWidgetItem(p)
            publisher.setSelected(False)
            publisher.setWhatsThis(isbn)
            publisher.setFlags(publisher.flags() ^ Qt.ItemFlag.ItemIsEditable)
            self.book_list.setItem(row, 2, publisher)

            year = QTableWidgetItem(str(y))
            year.setSelected(False)
            year.setWhatsThis(isbn)
            year.setFlags(year.flags() ^ Qt.ItemFlag.ItemIsEditable)
            self.book_list.setItem(row, 3, year)

    def open_book_info(self):
        selected_news = self.book_list.currentItem()

        try:
            self.sub_window.close()
        except:
            pass
        
        book = BookInfo(selected_news.whatsThis(), False, self._jwt_token)
        self._current_book_widget = book
        self.sub_window = self.mdi.addSubWindow(book)
        self.sub_window.showFullScreen()
        self.sub_window.setWindowFlags(Qt.WindowType.FramelessWindowHint)

    def get_search_parameters(self):
        isbn = str(self.isbn_input.text()).strip()
        title = str(self.title_input.text()).strip()
        year = self.year_spin_box.value() if self.year_check_box.isChecked() else ''
        author = str(self.author_input.text()).strip()
        publisher = str(self.publisher_input.text()).strip()
        warehouse = str(self.warehouse_combobox.currentText()).strip()

        return {
            'isbn': isbn,
            'title': title,
            'year': year,
            'author': author,
            'publisher': publisher,
            'warehouse': '' if warehouse == 'همه' else warehouse,
        }


class BookInfo(QWidget):
    def __init__(self, isbn: str, show_page: bool, jwt_token: str) -> None:
        super().__init__()
        self.root_path = Path(__file__).parent
        self._jwt_token = jwt_token
        self.isbn = isbn
        uic.loadUi(str(self.root_path / 'UI/book.ui'), self)

        self.setWindowTitle('Book Info')
        self._find_all_components()
        self._load_styles()
        self._set_functions()
        
        res = self.get_info()

        if show_page:
            self.show()
    
    def _find_all_components(self):
        self.warehouse_combobox: QComboBox = self.findChild(QComboBox, 'warehouse_combobox')
        
        self.price_value_label: QLabel = self.findChild(QLabel, 'price_value_label')
        self.price_label: QLabel = self.findChild(QLabel, 'price_label')
        self.title_label: QLabel = self.findChild(QLabel, 'title_label')
        self.title_name_label: QLabel = self.findChild(QLabel, 'title_name_label')
        self.author_name_label: QLabel = self.findChild(QLabel, 'author_name_label')
        self.author_label: QLabel = self.findChild(QLabel, 'author_label')
        self.publisher_name_label: QLabel = self.findChild(QLabel, 'publisher_name_label')
        self.publisher_label: QLabel = self.findChild(QLabel, 'publisher_label')
        self.picture_label: QLabel = self.findChild(QLabel, 'picture_label')
        self.edition_label: QLabel = self.findChild(QLabel, 'edition_label')
        self.edition_name_label: QLabel = self.findChild(QLabel, 'edition_name_label')
        self.year_value_label: QLabel = self.findChild(QLabel, 'year_value_label')
        self.year_label: QLabel = self.findChild(QLabel, 'year_label')
        self.warehouse_label: QLabel = self.findChild(QLabel, 'warehouse_label')
        self.comment_label: QLabel = self.findChild(QLabel, 'comment_label')
        self.score_value_label: QLabel = self.findChild(QLabel, 'score_value_label')
        self.score_label: QLabel = self.findChild(QLabel, 'score_label')
        self.star_label: QLabel = self.findChild(QLabel, 'label_11')
        
        self.amount_spin_box: QSpinBox = self.findChild(QSpinBox, 'amount_spin_box')
        self.star_spin: QSpinBox = self.findChild(QSpinBox, 'star_spin')

        self.add_to_cart_button: QPushButton = self.findChild(QPushButton, 'add_to_cart_button')
        self.send_comment_star_button: QPushButton = self.findChild(QPushButton, 'send_comment_star_button')
        self.delete_comment_button: QPushButton = self.findChild(QPushButton, 'delete_comment_button')
        if self.delete_comment_button:
            self.delete_comment_button.setVisible(False)

        self.comment_table: QTableWidget = self.findChild(QTableWidget, 'comment_table')
        if self.comment_table:
            self.comment_table.setColumnWidth(0, 110)
            self.comment_table.setColumnWidth(1, 380)
            self.comment_table.setColumnWidth(2, 55)
            self.comment_table.setColumnWidth(3, 155)

        self.comment_text: QPlainTextEdit = self.findChild(QPlainTextEdit, 'comment_text')
        self._load_icons()

    def _load_icons(self):
        if self.star_label:
            self.star_label.setPixmap(QPixmap(get_icon_path(self.root_path, 'star-32.png')))

    def _set_all_components(self, data: dict):
        self.price_value_label.setText(data['price'])
        self.title_name_label.setText(data['title'])
        self.author_name_label.setText(data['author'])
        self.edition_name_label.setText(data['edition'])
        self.publisher_name_label.setText(data['publisher'])
        self.year_value_label.setText(data['year'])
        self.picture_label.setPixmap(QPixmap(str(self.root_path / 'UI/images/book-94.png')))
        self.warehouse_combobox.clear()
        self.warehouse_combobox.addItems(data['warehouse'])

        score = 0

        for i in range(self.comment_table.rowCount(), -1, -1):
            self.comment_table.removeRow(i)

        if len(data['comments']) != 0:
            for n, c, s, t in data['comments']:
                row = self.comment_table.rowCount()
                self.comment_table.insertRow(row)
                
                name = QTableWidgetItem(n)
                name.setSelected(False)
                name.setFlags(name.flags() ^ Qt.ItemFlag.ItemIsEditable)
                self.comment_table.setItem(row, 0, name)

                content = QTableWidgetItem(c)
                content.setSelected(False)
                content.setFlags(content.flags() ^ Qt.ItemFlag.ItemIsEditable)
                self.comment_table.setItem(row, 1, content)

                comment_score = QTableWidgetItem(str(s))
                comment_score.setSelected(False)
                comment_score.setFlags(comment_score.flags() ^ Qt.ItemFlag.ItemIsEditable)
                self.comment_table.setItem(row, 2, comment_score)
                score += float(s)

                time = QTableWidgetItem(t)
                time.setSelected(False)
                time.setFlags(time.flags() ^ Qt.ItemFlag.ItemIsEditable)
                self.comment_table.setItem(row, 3, time)

            self.score_value_label.setText(str(score / len(data['comments'])))
        else:
            self.score_value_label.setText('*')

        user_comment = data.get('user_comment')
        if user_comment:
            self.comment_text.setPlainText(str(user_comment.get('content', '')))
            try:
                self.star_spin.setValue(int(user_comment.get('score', 10)))
            except ValueError:
                pass
            self.send_comment_star_button.setText('Update')
            if self.delete_comment_button:
                self.delete_comment_button.setVisible(True)
        else:
            self.comment_text.setPlainText('')
            self.star_spin.setValue(10)
            self.send_comment_star_button.setText('Send')
            if self.delete_comment_button:
                self.delete_comment_button.setVisible(False)

    def _load_styles(self):
        pass

    def get_info(self):
        try:
            res = requests.get(f'{REQUEST_HOST}/get-book-info/{self.isbn}', data={"token": self._jwt_token})
        except requests.exceptions.ConnectionError as ce:
            self.warning('Internet connection not found or server is down!')
            return 1
        if res.status_code == 400:
            app.exit(1)
        elif re.match(r'5\d\d', str(res.status_code)):
            self.warning(f'Server Error! <br> {res.json()}')
            return 1
        elif res.status_code == 200:
            res = res.json()
            data = {
                'title': res['book']['info'][0],
                'author': res['book']['info'][2],
                'publisher': res['book']['info'][3],
                'edition': res['book']['info'][4],
                'price': str(res['book']['info'][1]),
                'year': str(res['book']['info'][5]),
                'warehouse': res['book']['nearest_warehouses'],
                'comments': res['book']['comments'],
                'user_comment': res['book'].get('user_comment')
            }
            self._set_all_components(data)

    def _set_functions(self):
        self.add_to_cart_button.clicked.connect(self._update_cart)
        self.send_comment_star_button.clicked.connect(self._send_comment)
        if self.delete_comment_button:
            self.delete_comment_button.clicked.connect(self._delete_comment)

    def _update_cart(self):
        user_amount = self.amount_spin_box.value()
        if user_amount <= 0:
            self.warning('Count must be greater than 0.')
            return 1

        try:
            res = requests.get(f'{REQUEST_HOST}/check-inventory-book', data={
                "book_id": self.isbn,
                "warehouse_name": str(self.warehouse_combobox.currentText()).strip()
            })
        except requests.exceptions.ConnectionError as ce:
            self.warning('Internet connection not found or server is down!')
            return 1
        if res.status_code == 400:
            app.exit(1)
        elif re.match(r'5\d\d', str(res.status_code)):
            self.warning(f'Server Error! <br> {res.json()}')
            return 1
        elif res.status_code == 200:
            count = int(res.json()['count'])
            warehouse_id = res.json()['warehouse_id']
            
            if count >= user_amount:
                try:
                    with open(self.root_path / 'tmp/cart.json', 'r', encoding='utf-8') as f:
                        cart = json.load(f)
                except:
                    cart = {}
                
                for i in cart.keys():
                    if i == self.isbn:
                        cart[i] = {
                            'count': user_amount,
                            'warehouse_id': warehouse_id
                        }
                        break
                else:
                    cart[self.isbn] = {
                            'count': user_amount,
                            'warehouse_id': warehouse_id
                        }

                (self.root_path / 'tmp').mkdir(parents=True, exist_ok=True)
                with open(self.root_path / 'tmp/cart.json', 'w', encoding='utf-8') as f:
                        cart = json.dump(cart, f, ensure_ascii=False, indent=4)

            else:
                self.error(f'Inventory is not enough! <br> Warehouse: {str(self.warehouse_combobox.currentText()).strip()} <br> Inventory: {count} - Your request: {user_amount}')


    def _send_comment(self):
        text = str(self.comment_text.toPlainText()).strip()
        if text == '':
            self.warning('Please write a texr for comment.')
            return
        
        s = self.star_spin.value()

        try:
            res = requests.post(f'{REQUEST_HOST}/add-comment', data={
                'token': self._jwt_token,
                'book_id': self.isbn,
                'score': s,
                'content': text
            })
        except requests.exceptions.ConnectionError as ce:
            self.warning('Internet connection not found or server is down!')
            return 1
        if res.status_code == 409:
            self.warning(res.json()['message'])
            return 1
        elif res.status_code == 400:
            app.exit(1)
        elif re.match(r'5\d\d', str(res.status_code)):
            self.warning(f'Server Error! <br> {res.json()}')
            return 1
        elif res.status_code == 200:
            self.send_comment_star_button.setText('Update')
            if self.delete_comment_button:
                self.delete_comment_button.setVisible(True)
            self.info('Comment added. please refresh the page to view it.')

    def _delete_comment(self):
        try:
            res = requests.delete(f'{REQUEST_HOST}/delete-comment', data={
                'token': self._jwt_token,
                'book_id': self.isbn
            })
        except requests.exceptions.ConnectionError as ce:
            self.warning('Internet connection not found or server is down!')
            return 1
        if res.status_code == 400:
            app.exit(1)
        elif re.match(r'5\d\d', str(res.status_code)):
            self.warning(f'Server Error! <br> {res.json()}')
            return 1
        elif res.status_code == 200:
            self.comment_text.setPlainText('')
            self.star_spin.setValue(10)
            self.send_comment_star_button.setText('Send')
            if self.delete_comment_button:
                self.delete_comment_button.setVisible(False)
            self.info('Comment deleted. please refresh the page to view it.')


    def error(self, err_message: str='An error has occurred!'):
        msg_box = QMessageBox(self)
        msg_box.setWindowIcon(QIcon(str(self.root_path / "UI/images/error.png")))

        temp = [255, 255, 255] if get_saved_theme(self.root_path) == 'dark' else [int(i) for i in 'rgb(9, 38, 53)'.strip(
            'rgb').strip('()').split(',')]
        QMessageBox.critical(msg_box, 'Error',
                          f"""
            <font color='{'#%02x%02x%02x' % (temp[0], temp[1], temp[2])}'>
            <p>{err_message}</p>
            </font>
            <br>
            <font color='{'#%02x%02x%02x' % (temp[0], temp[1], temp[2])}'>
            <p>Please tap to OK button to continue...</p>
            </font>
        """)

        msg_box.setFixedSize(370, (err_message.count('<br>') + 2) * 100)
        msg_box.move(30, 800)

    def info(self, inf_message: str):
        msg_box = QErrorMessage(self)
        msg_box.setWindowIcon(QIcon(str(self.root_path / "UI/images/info.png")))
        msg_box.setWindowTitle('Info')
        
        temp = [255, 255, 255] if get_saved_theme(self.root_path) == 'dark' else [int(i) for i in 'rgb(9, 38, 53)'.strip(
            'rgb').strip('()').split(',')]
        msg_box.showMessage(f"""
            <font color='{'#%02x%02x%02x' % (temp[0], temp[1], temp[2])}'>
            <p>{inf_message}</p>
            </font>
            <font color='{'#%02x%02x%02x' % (temp[0], temp[1], temp[2])}'>
            <p>Please tap to OK button to close.</p>
            </font>
        """)
        msg_box.setFixedSize(370, (inf_message.count('<br>') + 2) * 100)
    
    def warning(self, war_message: str):
        msg_box = QErrorMessage(self)
        msg_box.setWindowIcon(QIcon(str(self.root_path / "UI/images/warning.png")))
        msg_box.setWindowTitle('Warning')
        
        temp = [255, 255, 255] if get_saved_theme(self.root_path) == 'dark' else [int(i) for i in 'rgb(9, 38, 53)'.strip(
            'rgb').strip('()').split(',')]
        msg_box.showMessage(f"""
            <font color='{'#%02x%02x%02x' % (temp[0], temp[1], temp[2])}'>
            <p>{war_message}</p>
            </font>
            <font color='{'#%02x%02x%02x' % (temp[0], temp[1], temp[2])}'>
            <p>Please tap to OK button to close.</p>
            </font>
        """)
        msg_box.setFixedSize(370, (war_message.count('<br>') + 2) * 100)


class Cart(QWidget):
    def __init__(self, jwt_token: str) -> None:
        super().__init__()
        self.root_path = Path(__file__).parent
        self._jwt_token = jwt_token
        self.cart_info_list = []

        try:
            with open(self.root_path / 'tmp/cart.json', 'r', encoding='utf-8') as f:
                raw_cart = json.load(f)
            self.cart = {k: v for k, v in raw_cart.items() if int(v.get('count', 0)) > 0}
            if not self.cart:
                raise Exception('Cart is empty.')
        except Exception as e:
            raise Exception('Cart is empty.')
        
        uic.loadUi(str(self.root_path / 'UI/cart.ui'), self)
        self.setWindowTitle('Cart')
        self._find_all_components()
        self._load_styles()
        self._set_functions()
        
        self.load_cart()
        self.show()
    
    def _find_all_components(self):
        self.total_price_label: QLabel = self.findChild(QLabel, 'total_price_label')
        self.total_price_value_label: QLabel = self.findChild(QLabel, 'total_price_value_label')
        
        self.cancel_button: QPushButton = self.findChild(QPushButton, 'cancel_button')
        self.delete_button: QPushButton = self.findChild(QPushButton, 'delete_button')
        self.confrime_button: QPushButton = self.findChild(QPushButton, 'confrime_button')

        self.cart_list: QTableWidget = self.findChild(QTableWidget, 'cart_list')

    def _load_styles(self):
        pass

    def _set_functions(self):
        self.cancel_button.clicked.connect(self._close_window)
        self.delete_button.clicked.connect(self._delete_order)
        self.confrime_button.clicked.connect(self._confrime_order)
    
    def _close_window(self):
        self.close()
    
    def _delete_order(self):
        try:
            os.remove(self.root_path / 'tmp/cart.json')
        except:
            pass
        self._close_window()
    
    def _confrime_order(self):
        try:
            res = requests.post(f'{REQUEST_HOST}/send-order', data={
                "token": self._jwt_token,
                "data": json.dumps(self.cart, ensure_ascii=False)
            })
        except requests.exceptions.ConnectionError as ce:
            self.warning('Internet connection not found or server is down!')
            return 1
        if res.status_code == 400:
            app.exit(1)
        elif re.match(r'5\d\d', str(res.status_code)):
            self.warning(f'Server Error! <br> {res.json()}')
            return 1
        elif res.status_code == 200:
            self.info('Order is placed.')
            try:
                os.remove(self.root_path / 'tmp/cart.json')
            except:
                pass
        
    def update_cart_table(self):
        for i in range(self.cart_list.rowCount(), -1, -1):
            self.cart_list.removeRow(i)

        if len(self.cart_info_list) != 0:
            total_price = 0
            for t, pri, c, a, pub, w in self.cart_info_list:
                row = self.cart_list.rowCount()
                self.cart_list.insertRow(row)
                
                title = QTableWidgetItem(t)
                title.setSelected(False)
                # name.setWhatsThis()
                title.setFlags(title.flags() ^ Qt.ItemFlag.ItemIsEditable)
                self.cart_list.setItem(row, 0, title)

                price = QTableWidgetItem(pri)
                price.setSelected(False)
                # author.setWhatsThis()
                price.setFlags(price.flags() ^ Qt.ItemFlag.ItemIsEditable)
                self.cart_list.setItem(row, 1, price)

                count = QTableWidgetItem(str(c))
                count.setSelected(False)
                count.setFlags(count.flags() ^ Qt.ItemFlag.ItemIsEditable)
                self.cart_list.setItem(row, 2, count)
                
                total_price += float(pri) * float(c)

                author = QTableWidgetItem(a)
                author.setSelected(False)
                author.setFlags(author.flags() ^ Qt.ItemFlag.ItemIsEditable)
                self.cart_list.setItem(row, 3, author)

                publisher = QTableWidgetItem(pub)
                publisher.setSelected(False)
                publisher.setFlags(publisher.flags() ^ Qt.ItemFlag.ItemIsEditable)
                self.cart_list.setItem(row, 4, publisher)

                warehouse = QTableWidgetItem(w)
                warehouse.setSelected(False)
                warehouse.setFlags(warehouse.flags() ^ Qt.ItemFlag.ItemIsEditable)
                self.cart_list.setItem(row, 5, warehouse)
            
            self.total_price_value_label.setText(str(total_price))
    
    def load_cart(self):
        for book_id in self.cart:
            try:
                res = requests.get(f'{REQUEST_HOST}/load-book-info-for-cart/{book_id}/{self.cart[book_id]["warehouse_id"]}')
            except requests.exceptions.ConnectionError as ce:
                self.warning('Internet connection not found or server is down!')
                return 1
            if res.status_code == 400:
                app.exit(1)
            elif re.match(r'5\d\d', str(res.status_code)):
                self.warning(f'Server Error! <br> {res.json()}')
                return 1
            elif res.status_code == 200:
                res = res.json()
                self.cart_info_list.append([res['book_info'][0], res['book_info'][1], self.cart[book_id]['count'], res['book_info'][2], res['book_info'][3], res['warehouse']])
        
        self.update_cart_table()

    def error(self, err_message: str='An error has occurred!'):
        msg_box = QMessageBox(self)
        msg_box.setWindowIcon(QIcon(str(self.root_path / "UI/images/error.png")))

        temp = [255, 255, 255] if get_saved_theme(self.root_path) == 'dark' else [int(i) for i in 'rgb(9, 38, 53)'.strip(
            'rgb').strip('()').split(',')]
        QMessageBox.critical(msg_box, 'Error',
                          f"""
            <font color='{'#%02x%02x%02x' % (temp[0], temp[1], temp[2])}'>
            <p>{err_message}</p>
            </font>
            <br>
            <font color='{'#%02x%02x%02x' % (temp[0], temp[1], temp[2])}'>
            <p>Please tap to OK button to continue...</p>
            </font>
        """)

        msg_box.setFixedSize(370, (err_message.count('<br>') + 2) * 100)
        msg_box.move(30, 800)

    def info(self, inf_message: str):
        msg_box = QErrorMessage(self)
        msg_box.setWindowIcon(QIcon(str(self.root_path / "UI/images/info.png")))
        msg_box.setWindowTitle('Info')
        
        temp = [255, 255, 255] if get_saved_theme(self.root_path) == 'dark' else [int(i) for i in 'rgb(9, 38, 53)'.strip(
            'rgb').strip('()').split(',')]
        msg_box.showMessage(f"""
            <font color='{'#%02x%02x%02x' % (temp[0], temp[1], temp[2])}'>
            <p>{inf_message}</p>
            </font>
            <font color='{'#%02x%02x%02x' % (temp[0], temp[1], temp[2])}'>
            <p>Please tap to OK button to close.</p>
            </font>
        """)
        msg_box.setFixedSize(370, (inf_message.count('<br>') + 2) * 100)
    
    def warning(self, war_message: str):
        msg_box = QErrorMessage(self)
        msg_box.setWindowIcon(QIcon(str(self.root_path / "UI/images/warning.png")))
        msg_box.setWindowTitle('Warning')
        
        temp = [255, 255, 255] if get_saved_theme(self.root_path) == 'dark' else [int(i) for i in 'rgb(9, 38, 53)'.strip(
            'rgb').strip('()').split(',')]
        msg_box.showMessage(f"""
            <font color='{'#%02x%02x%02x' % (temp[0], temp[1], temp[2])}'>
            <p>{war_message}</p>
            </font>
            <font color='{'#%02x%02x%02x' % (temp[0], temp[1], temp[2])}'>
            <p>Please tap to OK button to close.</p>
            </font>
        """)
        msg_box.setFixedSize(370, (war_message.count('<br>') + 2) * 100)




if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = MainWindow()
    sys.exit(app.exec())
