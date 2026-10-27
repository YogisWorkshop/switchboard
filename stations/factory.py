import config

def create_bridge():
    """Returns a bridge for the configured station, or None for offline."""
    if config.STATION_TYPE == "Simulator":
        from stations.fake import FakeBridge
        return FakeBridge()
    
    if config.STATION_TYPE == "ECoS":
        if not config.STATION_HOST:
            print("ECoS selected, but no host/IP address is set")
            return None
        from stations.ecos.ecos_bridge import EcosBridge
        return EcosBridge(config.STATION_HOST)
    
    if config.STATION_TYPE == "CS3":
        if not config.STATION_HOST:
            print("CS3 selected, but no host/IP address is set")
            return None
        from stations.cs3.cs3_bridge import Cs3Bridge
        return Cs3Bridge(config.STATION_HOST)
    
    if config.STATION_TYPE != "None":
        print(f"Station type {config.STATION_TYPE} in not implemented yet")
    return None
    