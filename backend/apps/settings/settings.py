MIDDLEWARE = [
    # Other middleware classes...
    "apps.settings.middleware.self_ping_middleware.SelfPingMiddleware",
    "apps.settings.cleanup_demo_users_middleware.CleanupDemoUsersMiddleware",
]
