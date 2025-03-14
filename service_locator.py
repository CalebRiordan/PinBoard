class Services():
    _services = {}
    
    @staticmethod
    def register(service_name, service_instance):
        Services._services[service_name] = service_instance
    
    @staticmethod
    def get(service_name):
        try:
            return Services._services[service_name]
        except KeyError:
            return None
        except Exception as e:
            raise e
            
        