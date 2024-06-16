import psycopg2
import psycopg2.extras
from flask import Flask, request, render_template, g, current_app

# Ініціалізація Flask
app = Flask(__name__)

# Маршрути
@app.route("/")
def index():
    return render_template("home.html")

@app.route("/dump")
def dump_entries_route():
    conn = get_db()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute('SELECT id, date, title, content FROM entries ORDER BY date')
    rows = cursor.fetchall()
    output = ""
    for r in rows:
        debug(str(dict(r)))
        output += str(dict(r))
        output += "\n"
    return "SQL dump нижче:\n<pre>" + output + "</pre>"

@app.route("/browse")
def browse():
    conn = get_db()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute('SELECT id, date, title, content, comment FROM entries ORDER BY date')
    rowlist = cursor.fetchall()
    return render_template('browse.html', entries=rowlist)

@app.route("/write", methods=['GET', 'POST'])
def write():
    if request.method == 'GET':
        return render_template('write.html', step="compose_entry")

    if request.method == 'POST':
        if "step" not in request.form:
            return render_template('write.html', step="compose_entry")

        if request.form["step"] == "add_entry":
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO entries (title, content, comment) VALUES (%s, %s, %s)",
                           [request.form['title'], request.form['content'], request.form['comment']])
            conn.commit()
            return render_template("write.html", step="add_entry")

@app.route("/edit", methods=['GET', 'POST'])
def edit():
    debug("дані форми=" + str(request.form))
    if request.method == 'GET':
        conn = get_db()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute('SELECT id, date, title, content, comment FROM entries ORDER BY date')
        rowlist = cursor.fetchall()
        return render_template('edit.html', step="display_entries", entries=rowlist)

    if request.method == 'POST':
        if request.form["step"] == "make_edits":
            conn = get_db()
            cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            postid = int(request.form["postid"])
            debug("Використовується postid=" + str(postid))
            cursor.execute("SELECT id, date, title, content, comment FROM entries WHERE id=%s", [postid])
            row = cursor.fetchone()
            debug("отримано з БД: " + str(dict(row)))
            return render_template("edit.html", step="make_edits", entry=row)

        if request.form["step"] == "update_database":
            conn = get_db()
            cursor = conn.cursor()
            postid = int(request.form["postid"])
            changedate = "changedate" in request.form
            if changedate:
                cursor.execute("UPDATE entries SET title=%s, content=%s, comment=%s, date=now() WHERE id=%s",
                               [request.form['title'], request.form['content'], request.form['comment'], postid])
            else:
                cursor.execute("UPDATE entries SET title=%s, content=%s, comment=%s WHERE id=%s",
                               [request.form['title'], request.form['content'], request.form['comment'], postid])
            conn.commit()
            return render_template("edit.html", step="update_database")

@app.route("/delete", methods=['GET', 'POST'])
def delete():
    debug("дані форми=" + str(request.form))
    if request.method == 'GET':
        conn = get_db()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute('SELECT id, date, title, content FROM entries ORDER BY date')
        rowlist = cursor.fetchall()
        return render_template('delete.html', step="display_entries", entries=rowlist)

    if request.method == 'POST':
        if request.form["step"] == "delete_entry":
            conn = get_db()
            cursor = conn.cursor()
            postid = int(request.form["postid"])
            cursor.execute("DELETE FROM entries WHERE id=%s", [postid])
            conn.commit()
            return render_template("delete.html", step="delete_entry")

def dump_entries():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM entries")
    rows = cur.fetchall()
    print("Ось записи:")
    print(rows)

# Обробка бази даних
def connect_db():
    """Підключається до бази даних."""
    debug("Підключення до БД.")
    conn = psycopg2.connect(host="localhost", user="postgres", password="123", dbname="flask",
                            cursor_factory=psycopg2.extras.DictCursor)
    return conn

def get_db():
    """Отримує з'єднання з базою даних або ініціалізує його. З'єднання унікальне для кожного запиту і буде повторно використано, якщо цей метод буде викликано знову."""
    if "db" not in g:
        g.db = connect_db()

    return g.db

@app.teardown_appcontext
def close_db(e=None):
    """Якщо цей запит підключився до бази даних, закрийте з'єднання."""
    db = g.pop("db", None)

    if db is not None:
        db.close()
        debug("Закриття БД")

@app.cli.command("init")
def init_db():
    """Очистити існуючі дані та створити нові таблиці."""
    conn = get_db()
    cur = conn.cursor()
    with current_app.open_resource("schema.sql") as file:  # відкрити файл
        alltext = file.read()  # прочитати весь текст
        cur.execute(alltext)  # виконати весь SQL у файлі
    conn.commit()
    print("Базу даних ініціалізовано.")

@app.cli.command('populate')
def populate_db():
    conn = get_db()
    cur = conn.cursor()
    with current_app.open_resource("populate.sql") as file:  # відкрити файл
        alltext = file.read()  # прочитати весь текст
        cur.execute(alltext)  # виконати весь SQL у файлі
    conn.commit()
    print("Базу даних заповнено інформацією.")
    dump_entries()

# Налагодження
def debug(s):
    """Виводить повідомлення на екран (не у веб-браузері)
    якщо FLASK_DEBUG встановлено."""
    if app.config['DEBUG']:
        print(s)

# Початок запуску
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080, debug=True)
