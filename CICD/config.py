# -*- coding: utf-8 -*-
"""
Created on Mon Aug 12 19:28:48 2024

@author: arsca
"""

import os

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'mysecretkey')
    SQLALCHEMY_DATABASE_URI = 'sqlite:///site.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MYSQL_DATABASE_URI = os.getenv('MYSQL_DATABASE_URI', 'mysql+pymysql://username:password@localhost/mydatabase')
