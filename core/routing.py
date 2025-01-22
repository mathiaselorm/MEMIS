
from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import path
from notification.routing import websocket_urlpatterns  # or wherever

application = ProtocolTypeRouter({
    # (http->django views is added by default)
    "websocket": URLRouter(websocket_urlpatterns),
})
