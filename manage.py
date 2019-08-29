# coding: utf-8

from myihome import create_app, db
from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand  # 使用数据库迁移插件


app = create_app("develop")
manager = Manager(app)

# 首次迁移的命令: python manage.py db init
# 然后,注意需要使用models.py,导入也行: python manage.py db migrate -m 'init tables' 数据库中只增加alembic_version版本表
# 接着升级一下: python manage.py db upgrade # 查看数据库可见全部表都建立出来了

Migrate(app, db)
# 添加指令 :db-> 对应的指令就是MigrateCommand
manager.add_command("db", MigrateCommand)


if __name__ == '__main__':
    # 直接启动
    manager.run()
