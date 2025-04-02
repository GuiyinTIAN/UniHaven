from django.apps import AppConfig
from django.db.backends.signals import connection_created

def register_sqlite_functions(sender, connection, **kwargs):
    if connection.vendor == 'sqlite':
        connection.connection.create_function("POW", 2, lambda x, y: x ** y)

class AccommodationConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "accommodation"
    
    def ready(self):
        # 使用信号注册SQLite函数
        connection_created.connect(register_sqlite_functions)