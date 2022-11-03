from flask import Flask, render_template, request, redirect, url_for, session, jsonify, make_response
from mysql.connector import Error, pooling

app = Flask(__name__)
app.secret_key="donotguessyouwillbeafraid"
connection_pool = pooling.MySQLConnectionPool(pool_name="pynative_pool",
                                                pool_size=5,
                                                pool_reset_session=True,
                                                host='localhost',
                                                database='website',
                                                user='yan',
                                                password='!QAZ2wsx')

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/signup", methods=["POST"])
def register():
    name = request.form["name"]
    username = request.form["usrname"]
    pwd = request.form["passwd"]
    if(name and username and pwd):
        try:
            # Get connection object from a pool
            connection_object = connection_pool.get_connection()
            cursor = connection_object.cursor()
            check_user_exist = ("SELECT * FROM member WHERE username = %s;")
            cursor.execute(check_user_exist,(username,))
            if (cursor.fetchone() is not None):
                return redirect(url_for("error", message="帳號已經被註冊"))
            else:
                create_user = ("INSERT INTO member "
                                "(name, username, password)"
                                "VALUES (%s, %s, %s);")  
                cursor.execute(create_user,(name,username,pwd))
                connection_object.commit()
                return redirect(url_for("index"))
        except Error as e:
            print("Error while connecting to MySQL using Connection pool ", e)
        finally:
            # closing database connection.
            cursor.close()
            connection_object.close()
    else:
        return redirect(url_for("error", message="姓名、帳號、密碼不能空"))

@app.route("/signin", methods=["POST"])
def signIn():
    usrname = request.form["username"]
    passwd = request.form["pwd"]
    if(usrname and passwd):
        try:
            connection_object = connection_pool.get_connection()
            cursor = connection_object.cursor()
            check_user_passwd = ("SELECT id, name, follower_count FROM member WHERE BINARY username = %s and BINARY password = %s;")
            cursor.execute(check_user_passwd,(usrname,passwd))
            fetchdata = cursor.fetchone()
            if (fetchdata is not None):
                session["login"] = "success"
                session["userProfile"] = list(fetchdata)
                return redirect("/member")
            else:
                session["login"] = "fail"
                return redirect(url_for("error", message="帳號、或密碼輸入錯誤"))
        except Error as e:
            print("Error while connecting to MySQL using Connection pool ", e)
        finally:
            cursor.close()
            connection_object.close()

    else:
        session["login"] = "fail"
        return redirect(url_for("error", message="請輸入帳號、密碼"))

@app.route("/member")
def member():
    if (session["login"] == "success"):
        data = getData()
        username = session["userProfile"][1]
        return render_template("member.html", name=username, datum=data)
    return redirect("/")

@app.route("/error")
def error():
    message = request.args.get("message")
    return render_template("error.html", mes=message)

@app.route("/signout")
def signOut():
    session["login"] = "fail"
    session["userProfile"] = ""
    return render_template("index.html")       

@app.route("/message", methods=["POST"])
def addCom():
    comment = request.form["comment"]
    if(comment):
        try:
            connection_object = connection_pool.get_connection()
            cursor = connection_object.cursor()
            add_comment = ("INSERT INTO message "
                        "(member_id, content)"
                        "VALUES (%s, %s);")
            cursor.execute(add_comment,(session["userProfile"][0],comment))
            connection_object.commit() 
            return redirect("/member")
        except Error as e:
            print("Error while connecting to MySQL using Connection pool ", e)
        finally:
            cursor.close()
            connection_object.close()
    else:
        return redirect("/member")

def getData():
    if (session["login"] == "success"):
        try:
            connection_object = connection_pool.get_connection()
            cursor = connection_object.cursor()
            get_commemt = ("SELECT name, content, message.time from message left join member on member.id = message.member_id order by message.time DESC;")
            cursor.execute(get_commemt)
            data = cursor.fetchall()
            return data
        except Error as e:
            print("Error while connecting to MySQL using Connection pool ", e)
        finally:
            cursor.close()
            connection_object.close()   

# API
@app.route("/api/member", methods=["GET"])
def apiMember():
    if 'username' in request.args:
        try:
                username = request.args['username']
                connection_object = connection_pool.get_connection()
                cursor = connection_object.cursor()
                get_profile = ("SELECT id, name, username FROM member WHERE username = %s;")
                cursor.execute(get_profile,(username,))
                data = cursor.fetchone()
                if data:
                    profile = { 
                            "id": data[0],
                            "name": data[1],
                            "username" : data[2]
                    }
                    return jsonify({"data":profile})
                else:
                    return jsonify({"data":None})
        except Error as e:
            print("Error while connecting to MySQL using Connection pool ", e)
        finally:
                cursor.close()
                connection_object.close()   
    else:
        return jsonify({"data":None})

@app.route("/api/member", methods=["PATCH"])
def apiUpdateMember():
    req = request.get_json()
    if (req['name'] and session["login"] == "success"):
        try:
            connection_object = connection_pool.get_connection()
            cursor = connection_object.cursor()
            check_user_exist = ("SELECT * FROM member WHERE name = %s;")
            cursor.execute(check_user_exist,(req['name'],))
            if (cursor.fetchone() is not None):
                return make_response(jsonify({"error":"true"}),404)
            else:
                update_name = ("UPDATE member "
                                "SET name = %s"
                                "WHERE id = %s;")  
                cursor.execute(update_name,(req['name'],session["userProfile"][0]))
                connection_object.commit()
                temp = (session["userProfile"][0],req['name'],session["userProfile"][2])
                session.pop('userProfile', default=None)
                session['userProfile'] = list(temp)
                return make_response(jsonify({"ok":"true"}),200)
        except Error as e:
            print("Error while connecting to MySQL using Connection pool ", e)
            return make_response(jsonify({"error":"true"}),404)
        finally:
            cursor.close()
            connection_object.close()
    else:
        return make_response(jsonify({"error":"true"}),404)

app.run(port=3000)
