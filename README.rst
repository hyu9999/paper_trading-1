==================================
Paper Trading
==================================
*基于Python的证券市场模拟交易后台服务器*

|Test Status| |Codecov Status| |License|

.. |Test Status| image:: https://github.com/Chaoyingz/paper_trading/workflows/Test/badge.svg

.. |Codecov Status| image:: https://codecov.io/gh/Chaoyingz/paper_trading/branch/paper_trading_v2/graph/badge.svg

.. |License| image:: https://img.shields.io/github/license/Naereen/StrapDown.js.svg


Quickstart
==========

系统要求:

Python3.7^

MongoDB4.4^

克隆项目到本地

.. code-block:: shell

    $ git clone https://github.com/Chaoyingz/paper_trading.git

安装项目依赖

.. code-block:: shell

    $ pip install poetry && poetry install --no-dev


配置本地环境变量

.. code-block:: shell

    $ cp .env.example .env
    $ echo DYNACONF_DB_USER=$MONGO_USER >> .env
    $ echo DYNACONF_DB_PASSWORD=$MONGO_PASSWORD >> .env
    $ . .env

运行项目

.. code-block:: shell

    $ make server


Docker 部署
-----------

需要安装Docker和Docker-Compose来运行下方的代码，运行之前需要像上面的步骤一样克隆项目和配置本地环境变量。

.. code-block:: shell

    $ docker-compose up -d db
    $ docker-compose up -d app

然后应用将在本地运行。

项目结构
========

与应用程序相关的文件位于 ``app`` 或 ``tests`` 目录中. 程序目录为:

::

    app
    ├── api                 - 网络接口
    │   ├── dependencies    - 路由定义中的依赖项
    │   └── routes          - 路由
    ├── core                - 核心配置
    │   ├── event           - 全局事件配置
    │   ├── jwt             - JWT鉴权配置
    │   └── logging         - 日志配置
    ├── db                  - 数据库
    │   ├── repositories    - 与数据库交互的相关方法
    │   └── events          - 数据库相关事件
    ├── exceptions          - 异常的定义与处理
    ├── models              - 数据模型
    │   ├── domain          - 数据模型基类与数据库模型
    │   ├── schemas         - 数据验证模型
    │   └── enums.py        - 枚举模型
    ├── services            - 服务
    │   ├── engines         - 引擎服务
    │   └── quotes          - 行情服务
    └── settings.toml       - 应用全局配置
