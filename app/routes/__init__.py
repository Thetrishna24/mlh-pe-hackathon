#def register_routes(app):
#    """Register all route blueprints with the Flask app.
#
#    Add your blueprints here. Example:
#        from app.routes.products import products_bp
#        app.register_blueprint(products_bp)
#    """
#    pass
def register_routes(app):
    from app.routes.health import health_bp
    from app.routes.link import links_bp

    app.register_blueprint(health_bp)
    app.register_blueprint(links_bp)