#!/usr/bin/env bash
set -euo pipefail

COMPOSE_FILE="$(dirname "$0")/compose.yaml"

# check DISPLAY
if [ -z "${DISPLAY:-}" ]; then
    echo "Error: DISPLAY is not set."
    exit 1
fi

attach_to_container() {
    local container="$1"
    local status
    status=$(docker inspect -f '{{.State.Status}}' "$container")

    xhost +local:docker > /dev/null

    if [ "$status" = "running" ]; then
        docker exec -e DISPLAY="$DISPLAY" -it "$container" /usr/bin/fish
    elif [ "$status" = "exited" ]; then
        echo "Starting $container..."
        docker start "$container"
        docker exec -e DISPLAY="$DISPLAY" -it "$container" /usr/bin/fish
    else
        echo "Error: container '$container' is in unexpected state: $status"
        exit 1
    fi
}

launch_new_project() {
    read -rp "Enter project name: " project_name
    if [ -z "$project_name" ]; then
        echo "Error: project name cannot be empty."
        exit 1
    fi

    # build images only if they don't exist yet
    if ! docker image inspect eda_docker_ubuntu > /dev/null 2>&1 || \
       ! docker image inspect eda_docker_rocky  > /dev/null 2>&1; then
        echo "Building images (first time)..."
        docker compose -f "$COMPOSE_FILE" build
    fi

    local volume_name="${project_name}_workspace"
    docker volume create "$volume_name" > /dev/null
    echo "Volume: $volume_name"

    echo "Launching project '$project_name'..."
    PROJECT_VOLUME="$volume_name" docker compose -p "$project_name" -f "$COMPOSE_FILE" up -d

    # wait briefly for containers to be registered
    sleep 1

    local container="${project_name}-ubuntu_server-1"
    echo "Attaching to $container..."
    attach_to_container "$container"
}

teardown_project() {
    mapfile -t running < <(
        docker ps \
            --filter "name=ubuntu" \
            --filter "status=running" \
            --format "{{.Names}}" \
        | sort
    )

    if [ ${#running[@]} -eq 0 ]; then
        echo "No running projects found."
        return
    fi

    # derive project names from container names (<project>-ubuntu_server-1)
    local labels=()
    local projects=()
    for container in "${running[@]}"; do
        local project
        project="${container%-ubuntu_server-1}"
        labels+=("$project")
        projects+=("$project")
    done

    echo "Select a project to turn down:"
    echo ""
    local chosen_project=""
    select label in "${labels[@]}" "Back"; do
        if [ "$label" = "Back" ]; then
            return
        fi
        for i in "${!labels[@]}"; do
            if [ "${labels[$i]}" = "$label" ]; then
                chosen_project="${projects[$i]}"
                break
            fi
        done
        [ -n "$chosen_project" ] && break
        echo "Invalid selection, try again."
    done

    echo "Turning down project '$chosen_project'..."
    local volume_name="${chosen_project}_workspace"
    PROJECT_VOLUME="$volume_name" docker compose -p "$chosen_project" -f "$COMPOSE_FILE" down
    echo "Project '$chosen_project' stopped."
}

attach_existing_project() {
    mapfile -t containers < <(
        docker ps -a \
            --filter "name=ubuntu" \
            --format "{{.Names}}\t{{.Status}}" \
        | sort
    )

    if [ ${#containers[@]} -eq 0 ]; then
        echo "No existing ubuntu containers found."
        exit 1
    fi

    local labels=()
    local names=()
    for entry in "${containers[@]}"; do
        local name status
        name=$(echo "$entry" | cut -f1)
        status=$(echo "$entry" | cut -f2)
        labels+=("$name  [$status]")
        names+=("$name")
    done

    echo "Select a container to attach to:"
    echo ""
    local chosen_container=""
    select label in "${labels[@]}" "Back"; do
        if [ "$label" = "Back" ]; then
            return
        fi
        for i in "${!labels[@]}"; do
            if [ "${labels[$i]}" = "$label" ]; then
                chosen_container="${names[$i]}"
                break
            fi
        done
        [ -n "$chosen_container" ] && break
        echo "Invalid selection, try again."
    done

    attach_to_container "$chosen_container"
}

# main menu
echo "=== EDA Docker Manager ==="
echo ""
select action in "Launch new project" "Attach to existing project" "Turn down a project" "Quit"; do
    case "$action" in
        "Launch new project")
            launch_new_project
            break
            ;;
        "Attach to existing project")
            attach_existing_project
            break
            ;;
        "Turn down a project")
            teardown_project
            break
            ;;
        "Quit")
            echo "Aborted."
            exit 0
            ;;
        *)
            echo "Invalid selection, try again."
            ;;
    esac
done
