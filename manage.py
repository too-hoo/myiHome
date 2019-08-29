# coding: utf-8

from myihome import create_app, db
from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand  # 使用数据库迁移插件


app = create_app("develop")
manager = Manager(app)

Migrate(app, db)
# 添加指令 :db-> 对应的指令就是MigrateCommand
manager.add_command("db", MigrateCommand)


if __name__ == '__main__':
    # 直接启动
    manager.run()
