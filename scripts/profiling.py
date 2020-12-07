import click
import uvicorn
from viztracer import VizTracer


@click.command("profiling")
def profiling():
    """分析代码."""
    tracer = VizTracer()
    tracer.start()
    uvicorn.run("app.main:app", host="localhost", port=5000)
    tracer.stop()
    tracer.save()
