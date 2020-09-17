==================================
Paper Trading
==================================
*基于Python的证券市场模拟交易后台服务器*

项目结构
-----------------

与应用程序相关的文件位于 ``app`` 或 ``tests`` 目录中. 程序目录为:

::

    app
    ├── api                 - 网络接口
    │   ├── dependencies    - 路由定义中的依赖项
    │   └── routes          - 路由
    ├── core                - 核心配置
    │   ├── events          - 全局事件配置
    │   ├── jwt             - JWT鉴权配置
    │   └── logging         - 日志配置
    ├── db                  - 数据库
    │   ├── repositories    - 与数据库交互的相关方法
    │   └── events          - 数据库相关事件
    ├── errors              - 异常的定义与处理
    ├── models              - 数据模型
    │   ├── domain          - 数据模型基类与数据库模型
    │   ├── schemas         - 数据验证模型
    │   └── enums.py        - 枚举模型
    ├── services            - 服务
    │   ├── engines         - 引擎服务
    │   ├── markets         - 交易市场服务
    │   └── quotes          - 行情服务
    └── settings.toml       - 应用全局配置

