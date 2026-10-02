from aiohttp import web


async def health(request):
    return web.json_response({
        "status": "ok",
        "service": "thezake"
    })


async def home(request):
    return web.Response(text="Hit @TheZake on TG")


async def start_web(port):
    app = web.Application()

    app.router.add_get("/", home)
    app.router.add_get("/health", health)
    app.router.add_get("/healthz", health)
    app.router.add_get("/ping", health)

    runner = web.AppRunner(app)
    await runner.setup()

    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

    return runner
