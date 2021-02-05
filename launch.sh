#!/bin/bash

# Method:
# Focus workspace
# Restore a layout that will swallow every (xfce4) terminal called Terminal Casper [0-9]
# Launch (xfce4) terminals with that title
# On any of those terminals launch: i3 focus parent; i3 mark custom-casper to mark the container as casper
# Setup [con_mark=casper] container: floating, position and size, focused on given workspace.
# Excepts: If only one terminal, there will be no container, mark the window
# To hide the marked container, send it to scratchpad

default_config_path="$HOME/.config/casper/default.config"
casper_script="$HOME/.config/casper/casper.py"
config_path="$HOME/.config/casper/config"
layout_path="$HOME/.config/casper/layout.json"
log_file="/home/gb/.config/casper/log"

if [[ ! -f $config_path ]]; then
    config_path=$default_config_path
else
    source $default_config_path
fi

# From config
# CONTAINER_NAME
# width, height, x, y
# wins, win_spawn_cmd
source $config_path
DEFAULT_CONTAINER_NAME="${CONTAINER_NAME:-$DEFAULT_CONTAINER_NAME}"

create_container() {
    local nof_wins="${1:-$CONTAINER_WINS}"; shift
    local spawn_cmd="${1:-$WIN_SPAWN_CMD}"
    i3-msg "workspace 11; append_layout ${layout_path}"
    for (( i = 1; i <= $nof_wins; i++ )); do
        "${spawn_cmd}" --title="Casper Win ${i}" &
    done
}

mark_container() {
    local container_name="${1:-$DEFAULT_CONTAINER_NAME}"; shift
    local nof_wins="${1:-$CONTAINER_WINS}"
    local parent_id=$(python3 $casper_script --child "Casper Win ${nof_wins}")
    if [[ "${parent_id}" == "" ]]; then
        sleep 0.5s
        echo "Could not fetch con_id $(python3 $casper_script --child 'Casper Win ${nof_wins}')"
        parent_id=$(python3 $casper_script --child "Casper Win ${nof_wins}")
    fi
    i3-msg "[con_id=$parent_id] mark $container_name"
}

setup_container() {
    local container_name="${1:-$DEFAULT_CONTAINER_NAME}"; shift
    local width="${1:-$CONTAINER_WIDTH}"; shift
    local height="${1:-$CONTAINER_HEIGHT}"; shift
    local x="${1:-$CONTAINER_X}"; shift
    local y="${1:-$CONTAINER_Y}"; shift
    local mon_data="$(python3 ${casper_script} --get_active_display_rect)"
    local target_wh_str=$(get_target_size $width $height "${mon_data}")
    local target_width=$(echo "${target_wh_str}" | head -n 1)
    local target_height=$(echo "${target_wh_str}" | tail -n 1)
    local target_xy_str=$(get_target_pos $x $y "${mon_data}")
    local target_x=$(echo "${target_xy_str}" | head -n 1)
    local target_y=$(echo "${target_xy_str}" | tail -n 1)
    # set:
    # - floating
    # - position (guess focused ws or default to screen 1) + config position
    # - size + config size (or default half screen)
    str="[con_mark=\"${container_name}\"] "
    str+="resize set ${target_width} ${target_height}, "
    str+="move position ${target_x} ${target_y}"
    echo "${str}"
    i3-msg "${str}"
}

move_to_scratchpad() {
    local target_ws=$1
    local last_child=$(python3 $casper_script --get_childs ${DEFAULT_CONTAINER_NAME} \
        | awk '{print $NF}'
    )
    echo "${last_child}"
    i3-msg "[con_id=${last_child}] move scratchpad"
    i3-msg "workspace ${target_ws}; scratchpad show"
}

get_focused_workspace() {
    ws=$(python3 $casper_script --workspace name)
    echo $ws
}

get_target_size() {
    local width="${1:-$CONTAINER_WIDTH}"; shift
    local height="${1:-$CONTAINER_HEIGHT}"; shift
    local mon_data="${1:-$(python3 ${casper_script} --get_active_display_rect)}"
    local full_width=$(echo $mon_data | awk '{print $1}')
    local full_height=$(echo $mon_data | awk '{print $2}')
    local target_width=$(python3 -c "print(int($full_width * ($width / 100)))")
    local target_height=$(python3 -c "print(int($full_height * ($height / 100)))")
    echo $target_width
    echo $target_height
}

get_target_pos() {
    local x="${1:-$CONTAINER_X}"; shift
    local y="${1:-$CONTAINER_Y}"; shift
    local mon_data="${1:-$(python3 ${casper_script} --get_active_display_rect)}"
    local full_x=$(echo $mon_data | awk '{print $3}')
    local full_y=$(echo $mon_data | awk '{print $4}')
    local target_x=$(( $x + $full_x ))
    local target_y=$(( $y + $full_y ))
    echo $target_x
    echo $target_y
}

is_casper_running() {
    casper_pid=$(pgrep -f 'casper.py')
    nof_childs=$(python3 $casper_script --get_childs ${DEFAULT_CONTAINER_NAME} \
        | wc -w)

    if [[ "${nof_childs}" -gt 0 && ! -z "${casper_pid}" ]]; then
        true
        return
    fi
    for pid in $(pgrep -f 'casper.py'); do
        kill $pid
    done
    false
}

start() {
    echo "Start Casper" >> $log_file
    local current_ws=$(get_focused_workspace)
    create_container 2>&1 >> $log_file
    mark_container 2>&1 >> $log_file
    setup_container 2>&1 >> $log_file
    move_to_scratchpad "${current_ws}" 2>&1 >> $log_file
    python3 $casper_script --listen --marks "${DEFAULT_CONTAINER_NAME}" 2>&1 >> $log_file
}

show() {
    if [[ "${HIDE_BY}" == "scratchpad" ]]; then
        i3-msg 'scratchpad show'
    else
        i3-msg "[con_mark='${DEFAULT_CONTAINER_NAME}'] move to workspace $(get_focused_workspace)"
    fi
    setup_container 2>&1 >> $log_file
}

if is_casper_running; then
    echo "casper running"
    show
else
    echo "casper not running"
    start
fi
