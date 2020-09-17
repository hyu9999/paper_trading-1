from typing import Generator, Callable, Any

# 任何可回调的类型
AnyCallable = Callable[..., Any]

# 可回调的生成器
CallableGenerator = Generator[AnyCallable, None, None]
