==================================
Paper Trading
==================================
*基于Python的证券市场模拟交易后台服务器*

|Test Status| |Codecov Status| |License| |Style|

.. |Test Status| image:: https://github.com/Chaoyingz/paper_trading/workflows/Test/badge.svg

.. |Codecov Status| image:: https://codecov.io/gh/Chaoyingz/paper_trading/branch/paper_trading_v2/graph/badge.svg

.. |License| image:: https://img.shields.io/github/license/Naereen/StrapDown.js.svg

.. |Style| image:: https://img.shields.io/badge/code%20style-black-000000.svg
   :target: https://github.com/ambv/black


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

首先安装Docker，修改.env文件
# 在.env文件设置好环境变量后写入环境变量到当前环境
$ export $(grep -v '^#' .env | xargs -d '\n')
# 打包容器镜像
$ docker build -t paper-trading --build-arg ZVT_USERNAME --build-arg ZVT_PASSWORD --build-arg ZVT_HOST --build-arg ZVT_PORT --build-arg ZVT_DB .
# 运行容器
$ docker run -dp 5000:80 --env-file=./.env --name pt paper-trading

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
