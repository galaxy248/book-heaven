from flask import Flask, request, Response
from flask_restful import Api, Resource, reqparse
import psycopg2
from token_generator import TokenGenerator
import time
import json
import os
from pathlib import Path
from dotenv import load_dotenv


load_dotenv(Path(__file__).parent / '.env')
load_dotenv(Path(__file__).parent.parent / '.env')

app = Flask(__name__)
api = Api(app)
tg = TokenGenerator()

sign_in_parser = reqparse.RequestParser()
sign_in_parser.add_argument('username', type=str, help='Username required.', required=True, location='form')
sign_in_parser.add_argument('password', type=str, help='Password required.', required=True, location='form')

sign_up_parser = reqparse.RequestParser()
sign_up_parser.add_argument('username', type=str, help='Username required.', required=True, location='form')
sign_up_parser.add_argument('password', type=str, help='Password required.', required=True, location='form')
sign_up_parser.add_argument('name', type=str, help='Name required.', required=True, location='form')
sign_up_parser.add_argument('last_name', type=str, help='Last name required.', required=True, location='form')
sign_up_parser.add_argument('email', type=str, help='Email required.', required=True, location='form')
sign_up_parser.add_argument('phone', type=str, help='Phone required.', required=True, location='form')
sign_up_parser.add_argument('address', type=str, help='Address optional.', required=False, default='', location='form')

validate_parser = reqparse.RequestParser()
validate_parser.add_argument('token', type=str, help='Token required.', required=True, location='form')
validate_parser.add_argument('rule', type=str, help='Rule required.', required=True, location='form')

orders_parser = reqparse.RequestParser()
orders_parser.add_argument('token', type=str, help='Token required.', required=True, location='form')

search_parser = reqparse.RequestParser()
search_parser.add_argument('isbn', type=str, help='isbn required.', required=True, location='form')
search_parser.add_argument('title', type=str, help='title required.', required=True, location='form')
search_parser.add_argument('year', type=str, help='year required.', required=True, location='form')
search_parser.add_argument('author', type=str, help='author required.', required=True, location='form')
search_parser.add_argument('publisher', type=str, help='publisher required.', required=True, location='form')
search_parser.add_argument('warehouse', type=str, help='warehouse required.', required=True, location='form')

bookinfo_parser = reqparse.RequestParser()
bookinfo_parser.add_argument('token', type=str, help='Token required.', required=True, location='form')

add_comment_parser = reqparse.RequestParser()
add_comment_parser.add_argument('token', type=str, help='Token required.', required=True, location='form')
add_comment_parser.add_argument('book_id', type=str, help='Book id required.', required=True, location='form')
add_comment_parser.add_argument('score', type=str, help='Score required.', required=True, location='form')
add_comment_parser.add_argument('content', type=str, help='Content required.', required=True, location='form')

delete_comment_parser = reqparse.RequestParser()
delete_comment_parser.add_argument('token', type=str, help='Token required.', required=True, location='form')
delete_comment_parser.add_argument('book_id', type=str, help='Book id required.', required=True, location='form')

check_inventory_book_parser = reqparse.RequestParser()
check_inventory_book_parser.add_argument('book_id', type=str, help='Book id required.', required=True, location='form')
check_inventory_book_parser.add_argument('warehouse_name', type=str, help='Warehouse name required.', required=True, location='form')

cursor = None
connection = None

def connect_to_database():
    global cursor
    global connection
    time.sleep(0.5)
    try:
        if connection:
            connection.close()
    except Exception:
        pass

    db_name = os.getenv('DATABASE_NAME') or os.getenv('DB_NAME') or 'postgres'
    db_host = os.getenv('DATABASE_HOST') or os.getenv('DB_HOST') or '127.0.0.1'
    db_port = os.getenv('DATABASE_PORT') or os.getenv('DB_PORT') or '5432'
    db_user = os.getenv('DATABASE_USER') or os.getenv('DB_USER') or 'postgres'
    db_password = os.getenv('DATABASE_PASSWORD') or os.getenv('DB_PASSWORD') or 'postgres'
    db_schema = os.getenv('DATABASE_SCHEMA') or os.getenv('DB_SCHEMA') or 'book_heaven'

    connection = psycopg2.connect(
        database=db_name,
        host=db_host,
        user=db_user,
        password=db_password,
        port=db_port,
        options=f'-c search_path={db_schema}'
    )

    cursor = connection.cursor()

try:
    connect_to_database()
except Exception as e:
    print(f"Warning: Could not connect to database on startup: {e}")


class root(Resource):
    def get(self):
        return Response('{"message": "Hello ^&^. I\'m here *@*"}', 200, mimetype='application/json')

class SignIn(Resource):
    def get(self):
        global cursor
        args = sign_in_parser.parse_args()
        for _ in range(5):
            try:
                cursor.execute(f'''
                    SELECT rule, CONCAT(name, ' ', last_name) AS "name"
                    FROM users
                    WHERE username = '{(args['username'])}' AND
                        password = '{args['password']}'
                ''')
                break
            except psycopg2.InterfaceError as e:
                connect_to_database()
            except psycopg2.OperationalError as e:
                connect_to_database()
        else:
            return Response('{"status": "database down", "message": "database is down"}', 500, mimetype='application/json')

        res = cursor.fetchone()
        if res is None:
            return Response('{"status": "invalied username or password", "message": "invalied username or password"}', 401, mimetype='application/json')
        else:
            return self._get_new_token(args['username'], res[0], res[1])

    def _get_new_token(self, username: str, rule: str, name: str):
        global tg
        encrypted_message = tg.encrypt(
            {
                'sub': username,
                'name': name,
                'rule': rule,
                'iat': int(time.time())
            }
        )
        return Response('{{"status": "new token", "message": "new token received", "token": "{0}", "rule": "{1}"}}'.format(encrypted_message, rule), 200, mimetype='application/json')

class SignUp(Resource):
    def post(self):
        global cursor, connection
        args = sign_up_parser.parse_args()

        username = (args['username'] or '').strip()
        password = (args['password'] or '').strip()
        name = (args['name'] or '').strip()
        last_name = (args['last_name'] or '').strip()
        email = (args['email'] or '').strip()
        phone = (args['phone'] or '').strip()
        address = (args['address'] or '').strip()

        if not all([username, password, name, last_name, email, phone]):
            return Response('{"status": "error", "message": "All required fields must be filled."}', 400, mimetype='application/json')

        for _ in range(5):
            try:
                cursor.execute("""
                    SELECT username FROM users WHERE username = %s OR email = %s;
                """, (username, email))
                break
            except (psycopg2.InterfaceError, psycopg2.OperationalError):
                connect_to_database()
        else:
            return Response('{"status": "database down", "message": "database is down"}', 500, mimetype='application/json')

        if cursor.fetchone():
            return Response('{"status": "error", "message": "Username or email is already registered."}', 409, mimetype='application/json')

        for _ in range(5):
            try:
                cursor.execute("""
                    INSERT INTO users (username, email, password, name, last_name, phone, rule)
                    VALUES (%s, %s, %s, %s, %s, %s, 'c');
                """, (username, email, password, name, last_name, phone))

                cursor.execute("""
                    INSERT INTO customer (customer_id, address, location)
                    VALUES (%s, %s, point(0, 0));
                """, (username, address))

                connection.commit()
                break
            except psycopg2.IntegrityError as ie:
                connection.rollback()
                err_str = str(ie).lower()
                if "phone" in err_str:
                    msg = "Invalid phone number. Must start with 09 or +989 followed by 9 digits."
                elif "email" in err_str:
                    msg = "Invalid email address format."
                else:
                    msg = "Validation error: " + str(ie)
                return Response(json.dumps({"status": "error", "message": msg}), 400, mimetype='application/json')
            except psycopg2.Error as e:
                connection.rollback()
                return Response(json.dumps({"status": "error", "message": str(e)}), 400, mimetype='application/json')
            except (psycopg2.InterfaceError, psycopg2.OperationalError):
                connect_to_database()
        else:
            return Response('{"status": "database down", "message": "database is down"}', 500, mimetype='application/json')

        return Response('{"status": "success", "message": "User registered successfully"}', 201, mimetype='application/json')

    def get(self):
        return self.post()

class Validate(Resource):
    def get(self):
        global tg
        args = validate_parser.parse_args()
        try:
            decrypted_message = tg.decrypt(args['token'].encode('ascii'))
        except ValueError as ve:
            return Response('{"status": "invalied token", "message": "the token is not valied"}', 401, mimetype='application/json')
        except Exception as e:
            return Response('{"status": "server error", "message": "internal server error"}', 500, mimetype='application/json')

        if decrypted_message['rule'] == 'c' and decrypted_message['rule'] != args['rule']:
            return Response('{"status": "block the user", "message": "your account will be block"}', 403, mimetype='application/json')
        elif decrypted_message['rule'] == 'a' and args['rule'] == 'm':
            return Response('{"status": "block the user", "message": "your account will be block"}', 403, mimetype='application/json')
        elif int(time.time()) - decrypted_message['iat'] >= 864_000: # 10 days
            return Response('{"status": "expired token", "message": "your token is expired please sign-in again"}', 302, mimetype='application/json')
        else:
            return Response('{"status": "valied token", "message": "your token is valied"}', 200, mimetype='application/json')


class Orders(Resource):
    def get(self):
        global tg
        args = orders_parser.parse_args()
        try:
            decrypted_message = tg.decrypt(args['token'].encode('ascii'))
        except ValueError as ve:
            return Response('{"status": "invalied token", "message": "the token is not valied"}', 401, mimetype='application/json')
        except Exception as e:
            return Response('{"status": "server error", "message": "internal server error"}', 500, mimetype='application/json')

        864_000 # 10 days
        if int(time.time()) - decrypted_message['iat'] >= 864_000: # 10 days
            return Response('{"status": "expired token", "message": "your token is expired please sign-in again"}', 302, mimetype='application/json')

        for _ in range(5):
            try:
                if decrypted_message.get('rule') == 'a':
                    cursor.execute('''
                        SELECT o.customer_id, o.order_id, o.title, o.price, o.count, o.author_name
                        FROM orders o
                        JOIN order_list ol ON o.order_id = ol.order_id
                        WHERE ol.warehouse_id = (
                            SELECT workplace FROM admin WHERE admin_id = %s
                        );
                    ''', (decrypted_message['sub'],))
                else:
                    cursor.execute(f'''
                        SELECT *
                        FROM orders o
                        WHERE customer_id = '{decrypted_message['sub']}';
                    ''')
                break
            except psycopg2.InterfaceError as e:
                connect_to_database()
            except psycopg2.OperationalError as e:
                connect_to_database()
        else:
            return Response('{"status": "database down", "message": "database is down"}', 500, mimetype='application/json')

        result = cursor.fetchall()

        response = {}
        for orders_detail in result:
            try:
                response[orders_detail[1]].append(
                    [orders_detail[2], orders_detail[5],
                     float(orders_detail[3]), orders_detail[4]]
                )
            except:
                response[orders_detail[1]] = [
                    [orders_detail[2], orders_detail[5],
                     float(orders_detail[3]), orders_detail[4]]
                ]

        return Response('{{"status": "orders", "message": "orders recievd", "orders": {0}}}'.format(json.dumps(response)), 200, mimetype='application/json')


class BookList(Resource):
    def get(self):
        global cursor
        args = search_parser.parse_args()
        if args['isbn'] != '':
            if args['warehouse'] == '':
                for _ in range(5):
                    try:
                        cursor.execute(f'''
                            SELECT i.book_id, title, author_name, publisher, year
                            FROM inventory i
                            JOIN book b ON i.book_id = b.book_id
                            WHERE i.book_id = '{args['isbn']}';
                        ''')
                        break
                    except psycopg2.InterfaceError as e:
                        connect_to_database()
                    except psycopg2.OperationalError as e:
                        connect_to_database()
                else:
                    return Response('{"status": "database down", "message": "database is down"}', 500, mimetype='application/json')

                res = cursor.fetchone()

                return Response('{{"status": "search", "message": "search finished", "books": {0}}}'.format(json.dumps(() if res is None else res)), 200, mimetype='application/json')

            else:
                for _ in range(5):
                    try:
                        cursor.execute(f'''
                            SELECT i.book_id, title, author_name, publisher, year
                            FROM inventory i
                            JOIN book b ON i.book_id = b.book_id
                            WHERE i.book_id = '{args['isbn']}' AND
                                i.warehouse_id = (
                                    SELECT warehouse_id
                                    FROM warehouse w
                                    WHERE name = '{args['warehouse']}'
                                    );
                        ''')
                        break
                    except psycopg2.InterfaceError as e:
                        connect_to_database()
                    except psycopg2.OperationalError as e:
                        connect_to_database()
                else:
                    return Response('{"status": "database down", "message": "database is down"}', 500, mimetype='application/json')

                res = cursor.fetchone()

                return Response('{{"status": "search", "message": "search finished", "books": {0}}}'.format(json.dumps(() if res is None else res)), 200, mimetype='application/json')

        else:
            query = f'''
                SELECT DISTINCT i.book_id, title, author_name, publisher, year
                FROM inventory i
                JOIN book b ON i.book_id = b.book_id
                WHERE
            '''
            # if args['title'] != '':
            query += f'''
            regexp_like(title, '.*{args['title']}.*', 'i')
            AND regexp_like(author_name, '.*{args['author']}.*', 'i')
            AND regexp_like(publisher, '.*{args['publisher']}.*', 'i')
            '''
            if args['year'] != '':
                query += f'''
                AND year = {args['year']}
                '''
            if args['warehouse'] != '':
                query += f'''
                    AND
                        i.warehouse_id = (
                        SELECT warehouse_id
                        FROM warehouse w
                        WHERE name = '{args['warehouse']}'
                        );
                '''
            for _ in range(5):
                try:
                    cursor.execute(query)
                    break
                except psycopg2.InterfaceError as e:
                    connect_to_database()
                except psycopg2.OperationalError as e:
                    connect_to_database()
            else:
                return Response('{"status": "database down", "message": "database is down"}', 500, mimetype='application/json')

            res = cursor.fetchall()

            return Response('{{"status": "search", "message": "search finished", "books": {0}}}'.format(json.dumps(() if res is None else res)), 200, mimetype='application/json')


class Warehouse(Resource):
    def get(self):
        for _ in range(5):
            try:
                cursor.execute(f'''
                    SELECT name
                    FROM warehouse w;
                ''')
                break
            except psycopg2.InterfaceError as e:
                connect_to_database()
            except psycopg2.OperationalError as e:
                connect_to_database()
        else:
            return Response('{"status": "database down", "message": "database is down"}', 500, mimetype='application/json')

        res = cursor.fetchall()

        return Response('{{"status": "get warehouse", "message": "get warehouse", "warehouse": {0}}}'.format(json.dumps(() if res is None else res)), 200, mimetype='application/json')


class BookInfo(Resource):
    def get(self, isbn: str):
        args = bookinfo_parser.parse_args()
        try:
            decrypted_message = tg.decrypt(args['token'].encode('ascii'))
        except ValueError as ve:
            return Response('{"status": "invalied token", "message": "the token is not valied"}', 401, mimetype='application/json')
        except Exception as e:
            return Response('{"status": "server error", "message": "internal server error"}', 500, mimetype='application/json')

        for _ in range(5):
            try:
                cursor.execute(f'''
                    SELECT title, price, author_name, publisher, edition, year
                    FROM book b
                    WHERE book_id = '{isbn}';
                ''')
                break
            except psycopg2.InterfaceError as e:
                connect_to_database()
            except psycopg2.OperationalError as e:
                connect_to_database()
        else:
            return Response('{"status": "database down", "message": "database is down"}', 500, mimetype='application/json')

        information = list(cursor.fetchone())

        information[1] = str(information[1])

        for _ in range(5):
            try:
                cursor.execute(f'''
                    SELECT concat(name, ' ', last_name), content, score, updated_time, c.user_id
                    FROM comments c
                    JOIN users u ON c.user_id = u.username
                    WHERE book_id = '{isbn}'
                    ORDER BY updated_time DESC;
                ''')
                break
            except psycopg2.InterfaceError as e:
                connect_to_database()
            except psycopg2.OperationalError as e:
                connect_to_database()
        else:
            return Response('{"status": "database down", "message": "database is down"}', 500, mimetype='application/json')

        temp_list = cursor.fetchall()
        comment_list = []
        user_comment = None

        for i in temp_list:
            comment_list.append([i[0], i[1], i[2], i[3].strftime('%Y-%m-%d %H-%M-%S')])
            if i[4] == decrypted_message['sub']:
                user_comment = {'content': i[1], 'score': int(i[2])}

        for _ in range(5):
            try:
                cursor.execute(f'''
                    SELECT name
                    FROM warehouse w
                    JOIN inventory i ON w.warehouse_id = i.warehouse_id
                    WHERE book_id = '{isbn}'
                    ORDER BY location <-> (
                        SELECT location
                        FROM customer c
                        WHERE customer_id = '{decrypted_message['sub']}'
                        );
                ''')
                break
            except psycopg2.InterfaceError as e:
                connect_to_database()
            except psycopg2.OperationalError as e:
                connect_to_database()
        else:
            return Response('{"status": "database down", "message": "database is down"}', 500, mimetype='application/json')

        nearest_warehouses = cursor.fetchall()

        if nearest_warehouses is None:
            return Response('{"status": "nearest warehouses", "message": "nearest warehouses can not empty"}', 500, mimetype='application/json')

        return Response(
            '{{ "status": "book info", "message": "book info", "book": {{ "info": {0}, "comments": {1}, "nearest_warehouses": {2}, "user_comment": {3} }} }}'.format(
                json.dumps(information, ensure_ascii=False),
                json.dumps(comment_list, ensure_ascii=False),
                json.dumps([i[0] for i in nearest_warehouses], ensure_ascii=False),
                json.dumps(user_comment, ensure_ascii=False)
            ),
            200,
            mimetype='application/json'
        )


class AddComment(Resource):
    def post(self):
        args = add_comment_parser.parse_args()
        try:
            decrypted_message = tg.decrypt(args['token'].encode('ascii'))
        except ValueError as ve:
            return Response('{"status": "invalied token", "message": "the token is not valied"}', 401, mimetype='application/json')
        except Exception as e:
            return Response('{"status": "server error", "message": "internal server error"}', 500, mimetype='application/json')

        for _ in range(5):
            try:
                cursor.execute(
                    '''
                    INSERT INTO comments (book_id, user_id, score, content)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (book_id, user_id) DO UPDATE SET
                        score = EXCLUDED.score,
                        content = EXCLUDED.content,
                        updated_time = current_timestamp;
                    ''',
                    (args['book_id'], decrypted_message['sub'], int(args['score']), args['content'])
                )
                connection.commit()
                break
            except psycopg2.InterfaceError as e:
                connect_to_database()
            except psycopg2.OperationalError as e:
                connect_to_database()

        else:
            return Response('{"status": "database down", "message": "database is down"}', 500, mimetype='application/json')

        return Response('{"status": "new comment", "message": "new comment added"}', 200, mimetype='application/json')


class DeleteComment(Resource):
    def delete(self):
        args = delete_comment_parser.parse_args()
        try:
            decrypted_message = tg.decrypt(args['token'].encode('ascii'))
        except ValueError as ve:
            return Response('{"status": "invalied token", "message": "the token is not valied"}', 401, mimetype='application/json')
        except Exception as e:
            return Response('{"status": "server error", "message": "internal server error"}', 500, mimetype='application/json')

        for _ in range(5):
            try:
                cursor.execute(
                    '''
                    DELETE FROM comments
                    WHERE book_id = %s AND user_id = %s;
                    ''',
                    (args['book_id'], decrypted_message['sub'])
                )
                connection.commit()
                break
            except psycopg2.InterfaceError as e:
                connect_to_database()
            except psycopg2.OperationalError as e:
                connect_to_database()
        else:
            return Response('{"status": "database down", "message": "database is down"}', 500, mimetype='application/json')

        return Response('{"status": "comment deleted", "message": "comment deleted"}', 200, mimetype='application/json')

    def post(self):
        return self.delete()


class CheckInventoryBook(Resource):
    def get(self):
        args = check_inventory_book_parser.parse_args()

        for _ in range(5):
            try:
                cursor.execute(f'''
                    SELECT warehouse_id, count
                    FROM inventory i
                    WHERE book_id = '{args['book_id']}' AND
                        warehouse_id = (
                            SELECT w.warehouse_id
                            FROM warehouse w
                            WHERE name = '{args['warehouse_name']}'
                            );
                ''')
                break
            except psycopg2.InterfaceError as e:
                connect_to_database()
            except psycopg2.OperationalError as e:
                connect_to_database()
        else:
            return Response('{"status": "database down", "message": "database is down"}', 500, mimetype='application/json')

        res = cursor.fetchone()

        return Response('{{"status": "check inventory", "message": "check inventory", "count": {0}, "warehouse_id": {1} }}'.format(json.dumps(res[1]), json.dumps(res[0])), 200, mimetype='application/json')


class LoadBookInfoForCart(Resource):
    def get(self, isbn: str, warehouse_id: str):
        for _ in range(5):
            try:
                cursor.execute(f'''
                    SELECT title, price, author_name, publisher
                    FROM book b
                    WHERE book_id = '{isbn}';
                ''')
                break
            except psycopg2.InterfaceError as e:
                connect_to_database()
            except psycopg2.OperationalError as e:
                connect_to_database()
        else:
            return Response('{"status": "database down", "message": "database is down"}', 500, mimetype='application/json')

        book = list(cursor.fetchone())

        book[1] = str(book[1])

        for _ in range(5):
            try:
                cursor.execute(f'''
                    SELECT name
                    FROM warehouse w
                    WHERE warehouse_id = '{warehouse_id}';
                ''')
                break
            except psycopg2.InterfaceError as e:
                connect_to_database()
            except psycopg2.OperationalError as e:
                connect_to_database()
        else:
            return Response('{"status": "database down", "message": "database is down"}', 500, mimetype='application/json')

        warehouse = cursor.fetchone()

        return Response('{{ "status": "load book info for cart", "message": "load book info for cart", "warehouse": {0}, "book_info": {1} }}'.format(json.dumps(warehouse[0]), json.dumps(book)), 200, mimetype='application/json')

class SendOrder(Resource):
    def post(self):
        args = request.form.to_dict()

        try:
            decrypted_message = tg.decrypt(args['token'].encode('ascii'))
        except ValueError as ve:
            return Response('{"status": "invalied token", "message": "the token is not valied"}', 401, mimetype='application/json')
        except Exception as e:
            return Response('{"status": "server error", "message": "internal server error"}', 500, mimetype='application/json')


        formatted_data = {}

        args['data'] = json.loads(args['data'])

        for i in args['data'].keys():
            try:
                formatted_data[args['data'][i]['warehouse_id']].append([i, args['data'][i]['count']])
            except:
                formatted_data[args['data'][i]['warehouse_id']] = [[i, args['data'][i]['count']]]

        for w_id in formatted_data.keys():

            for _ in range(5):
                try:
                    cursor.execute(f'''
                        INSERT INTO order_list AS ol (customer_id, warehouse_id)
                        VALUES ('{decrypted_message['sub']}', '{w_id}')
                        RETURNING order_id;
                    ''')

                    id = cursor.fetchone()[0]

                    for book_id, count in formatted_data[w_id]:

                        for _ in range(5):
                            try:
                                cursor.execute(f'''
                                    INSERT INTO books_per_order AS bpo (order_id, book_id, count)
                                    VALUES ({id}, '{book_id}', {count});
                                ''')
                                break

                            except psycopg2.InterfaceError as e:
                                connect_to_database()
                            except psycopg2.OperationalError as e:
                                connect_to_database()
                        else:
                            return Response('{"status": "database down", "message": "database is down"}', 500, mimetype='application/json')

                    connection.commit()
                    connection.reset()

                    break

                except psycopg2.InterfaceError as e:
                    connect_to_database()
                except psycopg2.OperationalError as e:
                    connect_to_database()
            else:
                return Response('{"status": "database down", "message": "database is down"}', 500, mimetype='application/json')

        connection.reset()

        return Response('{"status": "new order", "message": "new order added"}', 200, mimetype='application/json')

class Profile(Resource):
    def get(self):
        global tg, cursor
        args = orders_parser.parse_args()
        try:
            decrypted_message = tg.decrypt(args['token'].encode('ascii'))
        except ValueError:
            return Response('{"status": "invalied token", "message": "the token is not valied"}', 401, mimetype='application/json')
        except Exception:
            return Response('{"status": "server error", "message": "internal server error"}', 500, mimetype='application/json')

        if int(time.time()) - decrypted_message['iat'] >= 864_000:  # 10 days
            return Response('{"status": "expired token", "message": "your token is expired please sign-in again"}', 302, mimetype='application/json')

        username = decrypted_message['sub']
        rule = decrypted_message.get('rule', 'c')

        if rule == 'a':
            for _ in range(5):
                try:
                    cursor.execute("""
                        SELECT u.username, u.name, u.last_name, u.email, u.phone,
                               COALESCE(a.national_id, '') AS national_id,
                               COALESCE(w.name, a.workplace, '') AS workplace,
                               COALESCE(a.salary, 0) AS salary,
                               COALESCE(a.bank_account_number, '') AS bank_account_number
                        FROM users u
                        LEFT JOIN admin a ON u.username = a.admin_id
                        LEFT JOIN warehouse w ON a.workplace = w.warehouse_id
                        WHERE u.username = %s;
                    """, (username,))
                    break
                except (psycopg2.InterfaceError, psycopg2.OperationalError):
                    connect_to_database()
            else:
                return Response('{"status": "database down", "message": "database is down"}', 500, mimetype='application/json')

            res = cursor.fetchone()
            if res is None:
                return Response('{"status": "not found", "message": "user not found"}', 404, mimetype='application/json')

            profile_data = {
                'rule': 'a',
                'username': res[0],
                'name': res[1],
                'last_name': res[2],
                'email': res[3],
                'phone': res[4],
                'national_id': res[5],
                'workplace': res[6],
                'salary': str(res[7]),
                'bank_account_number': res[8]
            }
        else:
            for _ in range(5):
                try:
                    cursor.execute("""
                        SELECT u.username, u.name, u.last_name, u.email, u.phone,
                               COALESCE(c.address, '') AS address,
                               (SELECT COUNT(*) FROM order_list ol WHERE ol.customer_id = u.username) AS orders_count
                        FROM users u
                        LEFT JOIN customer c ON u.username = c.customer_id
                        WHERE u.username = %s;
                    """, (username,))
                    break
                except (psycopg2.InterfaceError, psycopg2.OperationalError):
                    connect_to_database()
            else:
                return Response('{"status": "database down", "message": "database is down"}', 500, mimetype='application/json')

            res = cursor.fetchone()
            if res is None:
                return Response('{"status": "not found", "message": "user not found"}', 404, mimetype='application/json')

            profile_data = {
                'rule': 'c',
                'username': res[0],
                'name': res[1],
                'last_name': res[2],
                'email': res[3],
                'phone': res[4],
                'address': res[5],
                'orders_count': int(res[6])
            }

        return Response(json.dumps({
            "status": "profile",
            "message": "profile received",
            "profile": profile_data
        }, ensure_ascii=False), 200, mimetype='application/json')


class AdminWarehouse(Resource):
    def get(self):
        global tg, cursor
        args = orders_parser.parse_args()
        try:
            decrypted_message = tg.decrypt(args['token'].encode('ascii'))
        except ValueError:
            return Response('{"status": "invalied token", "message": "the token is not valied"}', 401, mimetype='application/json')
        except Exception:
            return Response('{"status": "server error", "message": "internal server error"}', 500, mimetype='application/json')

        if int(time.time()) - decrypted_message['iat'] >= 864_000:
            return Response('{"status": "expired token", "message": "your token is expired please sign-in again"}', 302, mimetype='application/json')

        username = decrypted_message['sub']
        for _ in range(5):
            try:
                cursor.execute("""
                    SELECT w.warehouse_id, w.name
                    FROM admin a
                    JOIN warehouse w ON a.workplace = w.warehouse_id
                    WHERE a.admin_id = %s;
                """, (username,))
                wh = cursor.fetchone()
                warehouse_id = wh[0] if wh else 'tehran_001'
                warehouse_name = wh[1] if wh else 'Warehouse'

                cursor.execute("""
                    SELECT b.book_id, b.title, b.author_name, b.publisher, b.price, i.count
                    FROM inventory i
                    JOIN book b ON i.book_id = b.book_id
                    WHERE i.warehouse_id = %s
                    ORDER BY b.book_id;
                """, (warehouse_id,))
                rows = cursor.fetchall()
                break
            except (psycopg2.InterfaceError, psycopg2.OperationalError):
                connect_to_database()
        else:
            return Response('{"status": "database down", "message": "database is down"}', 500, mimetype='application/json')

        inventory_list = [
            [r[0], r[1], r[2], r[3], str(r[4]), int(r[5])]
            for r in rows
        ]
        return Response(json.dumps({
            "status": "warehouse",
            "warehouse_id": warehouse_id,
            "warehouse_name": warehouse_name,
            "inventory": inventory_list
        }, ensure_ascii=False), 200, mimetype='application/json')

    def post(self):
        global tg, cursor, connection
        args = request.form.to_dict()
        try:
            decrypted_message = tg.decrypt(args['token'].encode('ascii'))
        except ValueError:
            return Response('{"status": "invalied token", "message": "the token is not valied"}', 401, mimetype='application/json')
        except Exception:
            return Response('{"status": "server error", "message": "internal server error"}', 500, mimetype='application/json')

        if int(time.time()) - decrypted_message['iat'] >= 864_000:
            return Response('{"status": "expired token", "message": "your token is expired please sign-in again"}', 302, mimetype='application/json')

        username = decrypted_message['sub']
        book_id = (args.get('book_id') or '').strip()
        try:
            count = int(args.get('count', 0))
        except ValueError:
            return Response('{"status": "error", "message": "Invalid count"}', 400, mimetype='application/json')

        if not book_id:
            return Response('{"status": "error", "message": "ISBN is required."}', 400, mimetype='application/json')

        for _ in range(5):
            try:
                cursor.execute("SELECT workplace FROM admin WHERE admin_id = %s;", (username,))
                wh = cursor.fetchone()
                warehouse_id = wh[0] if wh else 'tehran_001'

                cursor.execute("SELECT book_id FROM book WHERE book_id = %s;", (book_id,))
                if not cursor.fetchone():
                    return Response('{"status": "error", "message": "Book ISBN not found in catalog."}', 404, mimetype='application/json')

                cursor.execute("""
                    INSERT INTO inventory (warehouse_id, book_id, count)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (warehouse_id, book_id) DO UPDATE SET count = EXCLUDED.count;
                """, (warehouse_id, book_id, count))
                connection.commit()
                break
            except psycopg2.Error as e:
                connection.rollback()
                return Response(json.dumps({"status": "error", "message": str(e)}), 400, mimetype='application/json')
            except (psycopg2.InterfaceError, psycopg2.OperationalError):
                connect_to_database()
        else:
            return Response('{"status": "database down", "message": "database is down"}', 500, mimetype='application/json')

        return Response('{"status": "updated", "message": "Inventory updated successfully"}', 200, mimetype='application/json')


class AdminBooks(Resource):
    def get(self):
        global tg, cursor
        args = orders_parser.parse_args()
        try:
            decrypted_message = tg.decrypt(args['token'].encode('ascii'))
        except ValueError:
            return Response('{"status": "invalied token", "message": "the token is not valied"}', 401, mimetype='application/json')
        except Exception:
            return Response('{"status": "server error", "message": "internal server error"}', 500, mimetype='application/json')

        if int(time.time()) - decrypted_message['iat'] >= 864_000:
            return Response('{"status": "expired token", "message": "your token is expired please sign-in again"}', 302, mimetype='application/json')

        for _ in range(5):
            try:
                cursor.execute("""
                    SELECT book_id, title, author_name, publisher, edition, year, price
                    FROM book
                    ORDER BY book_id;
                """)
                rows = cursor.fetchall()
                break
            except (psycopg2.InterfaceError, psycopg2.OperationalError):
                connect_to_database()
        else:
            return Response('{"status": "database down", "message": "database is down"}', 500, mimetype='application/json')

        books_list = [
            [r[0], r[1], r[2], r[3], r[4], int(r[5]), str(r[6])]
            for r in rows
        ]
        return Response(json.dumps({
            "status": "books",
            "books": books_list
        }, ensure_ascii=False), 200, mimetype='application/json')

    def post(self):
        global tg, cursor, connection
        args = request.form.to_dict()
        try:
            decrypted_message = tg.decrypt(args['token'].encode('ascii'))
        except ValueError:
            return Response('{"status": "invalied token", "message": "the token is not valied"}', 401, mimetype='application/json')
        except Exception:
            return Response('{"status": "server error", "message": "internal server error"}', 500, mimetype='application/json')

        if int(time.time()) - decrypted_message['iat'] >= 864_000:
            return Response('{"status": "expired token", "message": "your token is expired please sign-in again"}', 302, mimetype='application/json')

        username = decrypted_message['sub']
        book_id = (args.get('book_id') or '').strip()
        title = (args.get('title') or '').strip()
        author = (args.get('author') or '').strip()
        publisher = (args.get('publisher') or '').strip()
        edition = (args.get('edition') or '').strip()
        price_str = (args.get('price') or '').strip()
        year_str = (args.get('year') or '2024').strip()
        count_str = (args.get('count') or '0').strip()

        if not all([book_id, title, author, publisher, edition, price_str]):
            return Response('{"status": "error", "message": "Please fill in all book fields."}', 400, mimetype='application/json')

        try:
            price = float(price_str)
            year = int(year_str)
            count = int(count_str)
        except ValueError:
            return Response('{"status": "error", "message": "Invalid price, year, or count value."}', 400, mimetype='application/json')

        for _ in range(5):
            try:
                cursor.execute("SELECT workplace FROM admin WHERE admin_id = %s;", (username,))
                wh = cursor.fetchone()
                warehouse_id = wh[0] if wh else 'tehran_001'

                cursor.execute("""
                    INSERT INTO book (book_id, title, price, author_name, publisher, edition, year)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (book_id) DO UPDATE SET
                        title = EXCLUDED.title,
                        price = EXCLUDED.price,
                        author_name = EXCLUDED.author_name,
                        publisher = EXCLUDED.publisher,
                        edition = EXCLUDED.edition,
                        year = EXCLUDED.year;
                """, (book_id, title, price, author, publisher, edition, year))

                cursor.execute("""
                    INSERT INTO inventory (warehouse_id, book_id, count)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (warehouse_id, book_id) DO UPDATE SET count = EXCLUDED.count;
                """, (warehouse_id, book_id, count))
                connection.commit()
                break
            except psycopg2.Error as e:
                connection.rollback()
                return Response(json.dumps({"status": "error", "message": str(e)}), 400, mimetype='application/json')
            except (psycopg2.InterfaceError, psycopg2.OperationalError):
                connect_to_database()
        else:
            return Response('{"status": "database down", "message": "database is down"}', 500, mimetype='application/json')

        return Response('{"status": "added", "message": "Book saved successfully"}', 201, mimetype='application/json')


api.add_resource(SignIn, '/signin')
api.add_resource(SignUp, '/signup')
api.add_resource(Validate, '/validate')
api.add_resource(Profile, '/profile')
api.add_resource(AdminWarehouse, '/admin-warehouse')
api.add_resource(AdminBooks, '/admin-books')
api.add_resource(Orders, '/orders')
api.add_resource(BookList, '/search')
api.add_resource(Warehouse, '/get-warehouse')
api.add_resource(BookInfo, '/get-book-info/<string:isbn>')
api.add_resource(AddComment, '/add-comment')
api.add_resource(DeleteComment, '/delete-comment')
api.add_resource(CheckInventoryBook, '/check-inventory-book')
api.add_resource(LoadBookInfoForCart, '/load-book-info-for-cart/<string:isbn>/<string:warehouse_id>')
api.add_resource(SendOrder, '/send-order')
api.add_resource(root, '/')

if __name__ == '__main__':
    port = int(os.getenv('FLASK_PORT', 8080))
    debug = os.getenv('FLASK_DEBUG', '1') in ('1', 'true', 'True')
    app.run(host='0.0.0.0', port=port, debug=debug)


