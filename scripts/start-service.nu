def main [] {
    print "start or stop a service with a local overlay for testing."
}

def "main start" [service: string, local: bool = true] {
    let serviceDir = $'services/($service)'
    if not ($serviceDir | path exists) {
        error make {msg: $"Service '($service)' does not exist."}
    }

    let service = $'($serviceDir)/docker-compose.yaml'
    
    if not ($serviceDir | path exists) {
        error make {msg: $"Service '($service)' does not have a valid 'docker-compose.yaml' file defined."}
    }
    if $local {
        let localService = $'($serviceDir)/docker-compose.local.yaml'
        if not ($serviceDir | path exists) {
            error make {msg: $"Service '($service)' does not have a valid 'docker-compose.local.yaml' file defined. Create a local overlay before running the service locally."}
        }
        docker compose -f $'($service)' -f $'($localService)' up -d
    } else {
        docker compose -f $'($service)' up -d
    }
}

def "main stop" [service: string, local: bool = true] {
    let serviceDir = $'services/($service)'
    if not ($serviceDir | path exists) {
        error make {msg: $"Service '($service)' does not exist."}
    }

    let service = $'($serviceDir)/docker-compose.yaml'
    
    if not ($serviceDir | path exists) {
        error make {msg: $"Service '($service)' does not have a valid 'docker-compose.yaml' file defined."}
    }
    if $local {
        let localService = $'($serviceDir)/docker-compose.local.yaml'
        if not ($serviceDir | path exists) {
            error make {msg: $"Service '($service)' does not have a valid 'docker-compose.local.yaml' file defined. Create a local overlay before running the service locally."}
        }
        docker compose -f $'($service)' -f $'($localService)' down
    } else {
        docker compose -f $'($service)' down
    }
}