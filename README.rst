项目结构
-----------------

与应用程序相关的文件位于 ``app`` 或 ``tests`` 目录中. 程序目录为:

::

    app
    ├── models              - 数据模型
    │   ├── domain          - 主要数据模型
    │   ├── schemas         - 用于web服务的数据模型
    │   ├── enums.py        - 枚举数据模型
    │   ├── mixin.py        - 数据模型MIXIN
    │   └── rwmodel.py      - 数据模型基类
    └── settings            - 应用配置

