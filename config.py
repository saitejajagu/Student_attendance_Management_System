# import os
#
# class Config:
#     SECRET_KEY = os.environ.get('SECRET_KEY', 'ams-secret-key-change-in-production-2024')
#     SQLALCHEMY_DATABASE_URI = os.environ.get(
#         'DATABASE_URL',
#         'mysql+pymysql://root:root@localhost/attendance_db'
#     )
#     SQLALCHEMY_TRACK_MODIFICATIONS = False
#     SQLALCHEMY_ENGINE_OPTIONS = {
#         'pool_pre_ping': True,
#         'pool_recycle': 3600,
#     }
#
# class DevelopmentConfig(Config):
#     DEBUG = True
#
# class ProductionConfig(Config):
#     DEBUG = False
#
# config = {
#     'development': DevelopmentConfig,
#     'production': ProductionConfig,
#     'default': DevelopmentConfig
# }

import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'change-this-in-production')

    # Use cloud database if available
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL'
    ) or 'sqlite:///local.db'  # fallback for local development

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 3600,
    }

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}