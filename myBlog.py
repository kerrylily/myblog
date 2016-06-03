#!/usr/bin/python
# -*- coding: utf8 -*-

import os
import random, datetime

from hashlib import md5
import MySQLdb.cursors

from flask import Flask, request, session, redirect, url_for, render_template, make_response

app = Flask(__name__)


def sql_connection():
    conn = MySQLdb.connect(host='127.0.0.1', user='root', passwd='malele', db='blog',
                           charset="utf8", cursorclass=MySQLdb.cursors.DictCursor)
    conn.autocommit(True)
    return conn.cursor()


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None

    db = sql_connection()

    if request.method == 'POST':
        db.execute('SELECT password FROM blog.user WHERE username=%s', (request.form['username'],))
        password = db.fetchone()

        if password == None:
            error = "User Error!"
        elif password['password'] == request.form['password']:
            session['username'] = request.form['username']
            return redirect(url_for('blog_index'))
        elif password:
            error = "Password Error!"
        else:
            error = 'No Found Error!'

    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))


@app.route('/')
def index():
    data = None

    db = sql_connection()
    try:
        db.execute('SELECT b.id, b.title, b.content, b.username, b.time, u.email FROM blog.user AS u, blog.blogs AS b WHERE u.username=b.username ORDER BY id DESC')
        data = gravatar(db.fetchall())
    except Exception as e:
        print e.message

    return render_template('blogs_list.html', entries=data)


@app.route('/blog_index')
def blog_index():
    data = None

    db = sql_connection()
    try:
        db.execute('SELECT id, title, content, time FROM blog.blogs WHERE username=%s ORDER BY id DESC ', (
                    session['username'],))
        data = db.fetchall()
    except Exception as e:
        print e.message

    return render_template('blog_index.html', entries=data)


@app.route('/create_blog', methods=['POST'])
def create_blog():
    db = sql_connection()
    try:
        db.execute('INSERT INTO blog.blogs (`username`, `title`, `content`) VALUES (%s, %s, %s)', (
                    session['username'], request.form['title'], request.form['content']))
    except Exception as e:
        print e.message

    return redirect(url_for('blog_index'))


@app.route('/ckupload/', methods=['POST', 'OPTIONS'])
def ckupload():
    """CKEditor file upload"""
    error = ''
    url = ''
    callback = request.args.get("CKEditorFuncNum")

    def gen_rnd_filename():
        filename_prefix = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        return '%s%s' % (filename_prefix, str(random.randrange(1000, 10000)))

    if request.method == 'POST' and 'upload' in request.files:
        fileobj = request.files['upload']
        fname, fext = os.path.splitext(fileobj.filename)
        rnd_name = '%s%s' % (gen_rnd_filename(), fext)

        filepath = os.path.join(app.static_folder, 'upload', rnd_name)

        dirname = os.path.dirname(filepath)
        if not os.path.exists(dirname):
            try:
                os.makedirs(dirname)
            except:
                error = 'ERROR_CREATE_DIR'
        elif not os.access(dirname, os.W_OK):
            error = 'ERROR_DIR_NOT_WRITEABLE'

        if not error:
            fileobj.save(filepath)
            url = url_for('static', filename='%s/%s' % ('upload', rnd_name))
    else:
        error = 'post error'

    res = """<script type="text/javascript">
  window.parent.CKEDITOR.tools.callFunction(%s, '%s', '%s');
</script>""" % (callback, url, error)

    response = make_response(res)
    response.headers["Content-Type"] = "text/html"
    return response


@app.route('/update_blog/<int:blog_id>', methods=['POST', 'GET'])
def update_blog(blog_id):
    db = sql_connection()

    if request.form['action'] == 'Update':
        db.execute('SELECT * FROM blog.blogs where id=%s', (blog_id,))
        blog = db.fetchone()
        return render_template('change.html', blog=blog)
    elif request.form['action'] == 'Delete':
        db.execute('DELETE FROM blog.blogs WHERE id=%s', (blog_id,))

    return redirect(url_for('blog_index'))


@app.route('/commit/<int:blog_id>', methods=['POST'])
def commit(blog_id):
    db = sql_connection()
    db.execute('UPDATE blog.blogs SET title=%s, content=%s WHERE id=%s', (request.form['title'],
                                                                          request.form['content'], blog_id))
    return redirect(url_for('blog_index'))


def gravatar(data):
    for info in data:
        info['email'] = 'http://www.gravatar.com/avatar/' + md5(info['email']).hexdigest() + '?d=mm&s=' + '128'
    return data


if __name__ == '__main__':
    app.secret_key = 'super secret key'
    app.config['SESSION_TYPE'] = 'filesystem'

    app.run()
