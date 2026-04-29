facade = None


def init_facade():
    global facade
    from app.services.facade import HBnBFacade
    facade = HBnBFacade()
