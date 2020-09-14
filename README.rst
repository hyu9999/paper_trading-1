项目结构
-----------------

与应用程序相关的文件位于 ``app`` 或 ``tests`` 目录中. 程序目录为:

::

    app
    ├── api                 - 应用web接口
    │   ├── dependencies    - 路由定义的依赖项
    │   └── routes          - web路由
    ├── core                - 应用核心配置
    │   ├── events          - 应用启动相关事件
    │   └── logging         - 日志系统相关配置
    ├── db                  - 数据库相关方法
    ├── errors              - 应用错误处理程序
    ├── models              - 数据模型
    │   ├── domain          - 主要数据模型
    │   ├── schemas         - 用于web服务的数据模型
    │   ├── enums.py        - 枚举数据模型
    │   ├── mixin.py        - 数据模型MIXIN
    │   └── rwmodel.py      - 数据模型基类
    └── settings.toml       - 应用全局配置

