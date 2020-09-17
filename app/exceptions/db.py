class DbError(Exception):
    """数据库异常基类
    """


class EntityDoesNotExist(DbError):
    """在数据库中找不到实体时触发
    """
