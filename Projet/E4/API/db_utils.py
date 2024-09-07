# -*- coding: utf-8 -*-
"""
Created on Fri Jun 28 14:03:07 2024

@author: arsca
"""

import sqlite3
import datetime
import jwt

DATABASE = 'tokens.db'

def init_db():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                token TEXT NOT NULL,
                username TEXT NOT NULL,
                expiration DATETIME NOT NULL
            )
        ''')
        conn.commit()

def add_user(username, password):
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()

def authenticate_user(username, password, secret_key):
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        user = cursor.fetchone()
        if user:
            expiration = datetime.datetime.utcnow() + datetime.timedelta(hours=12)
            token = jwt.encode({'user': username, 'exp': expiration}, secret_key, algorithm="HS256")
            cursor.execute("INSERT INTO tokens (token, username, expiration) VALUES (?, ?, ?)", (token, username, expiration))
            conn.commit()
            return token
    return None
