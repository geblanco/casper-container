import re
import i3
import json
import argparse

from os import path
from pathlib import Path

import gi
gi.require_version('Gdk', '3.0')

from gi.repository import Gdk  # noqa: E402


previous_focus = None
previous_workspace = None
casper_marks = None
skip_frame = 0
config = None


def parse_flags():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-c", "--child", type=str, required=False,
        help="Child node of the one to mark"
    )
    parser.add_argument(
        "-l", "--listen", action="store_true",
        help="Start listening to focus events"
    )
    parser.add_argument(
        "--marks", type=str, nargs="*",
        help="Marks of the container with the windows to listen for focus "
    )
    parser.add_argument(
        "--workspace", type=str, required=False,
        help="Get given property from focused workspace"
    )
    parser.add_argument(
        "--get_childs", type=str, required=False,
        help="Get child ids of a given container mark"
    )
    parser.add_argument(
        "--get_active_display_rect", action="store_true", required=False,
        help="Get currently active display's data (width, height, x, y)"
    )
    args = parser.parse_args()
    if args.listen and len(args.marks) == 0:
        raise RuntimeError("You must provide marks to listen for")

    return args


def filter(tree=None, function=None, **conditions):
    if tree is None:
        tree = i3.get_tree()
    elif isinstance(tree, list):
        tree = {"list": tree}

    matches = []
    if function:
        try:
            if function(tree):
                return [tree]
        except (KeyError, IndexError):
            pass
    else:

        for key, value in conditions.items():
            if key in tree and tree[key] == value:
                matches.append(tree)

    for nodes in ["nodes", "floating_nodes", "list"]:
        if nodes in tree:
            for node in tree[nodes]:
                matches += filter(node, function, **conditions)
    return matches


def parent(con_id, tree=None):
    """
    Searches for a parent of a node/container, given the container id.
    Returns None if no container with given id exists (or if the
    container is already a root node).
    """
    def has_child(tree_node):
        for node in ["nodes", "floating_nodes", "list"]:
            if node in tree_node:
                for child in tree_node[node]:
                    if child["id"] == con_id:
                        return True
        return False
    parents = filter(tree, has_child)
    if not parents or len(parents) > 1:
        return None
    return parents[0]


def childs(**kwargs):
    trees = filter(**kwargs)
    childs = []
    for tree in trees:
        for node in ["nodes", "floating_nodes", "list"]:
            if node in tree:
                for child in tree[node]:
                    childs.append(child)

    return childs


def bash_to_dict(cfg_path):
    ret = {}
    if Path(cfg_path).exists():
        reg = re.compile(r"(?P<name>\w+)(\=['\"]?(?P<value>[^'\"]+)['\"]?)")
        for line in open(cfg_path):
            m = reg.match(line.strip())
            if m:
                name = m.group("name")
                value = ""
                if m.group("value"):
                    value = m.group("value")
                    ret[name.lower()] = value
    return ret


def parse_config():
    home = str(Path.home())
    default_config_path = path.join(
        home, ".config", "casper", "default.config"
    )
    config_path = path.join(home, ".config", "casper", "config")
    default_config = bash_to_dict(default_config_path)
    config = bash_to_dict(config_path)
    default_config.update(**config)
    return default_config


def print_parent_id(child_name):
    nodes = filter(name=child_name)
    if len(nodes):
        parent_node = parent(nodes[0]["id"])
        if parent_node:
            print(parent_node["id"])


def get_casper_windows(casper_container):
    if not isinstance(casper_container, list):
        casper_container = [casper_container]
    child_windows = childs(marks=casper_container)
    return [c["id"] for c in child_windows]


def get_focused_workspace(prop=None):
    if prop is None:
        prop = "id"
    workspaces = i3.get_workspaces()
    focused = [w for w in workspaces if w["focused"]]
    if len(focused) == 0:
        raise ValueError(
            "Unable to fetch current workspace" +
            json.dumps(i3.get_workspaces(), indent=2)
        )
    focused = focused[0]
    return focused[prop]


def get_window_name_from_id(id):
    wins = filter(id=id)
    if len(wins):
        wins = wins[0]["name"]
    else:
        wins = "Not Found"
    return wins


def get_active_display_rect():
    # get pointer
    display = Gdk.Display.get_default()
    dev_manager = Gdk.Display.get_device_manager(display)
    pointer = Gdk.DeviceManager.get_client_pointer(dev_manager)
    pointer_position = pointer.get_position()
    pointer_x, pointer_y = pointer_position.x, pointer_position.y

    # get display pointer is in
    active_display = display.get_monitor_at_point(pointer_x, pointer_y)
    active_rect = active_display.get_geometry()
    width, height = active_rect.width, active_rect.height
    x, y = active_rect.x, active_rect.y
    return width, height, x, y


def hide_container():
    global config, casper_marks
    if config is None:
        config = parse_config()

    if config["hide_by"] == "scratchpad":
        # Trick to make it work, as it has lost focus, first call regains it,
        # second really hide the scratchpad. This can generate an infinite loop
        # of focus-refocus, unsubscribe and resubscribe again
        i3.scratchpad("show")
        i3.scratchpad("show")
    else:
        mark = casper_marks
        if isinstance(casper_marks, list):
            mark = casper_marks[0]

        i3.command(f"[con_mark='{mark}'] move to workspace 11")


def box_is_checked():
    ret = False
    checkbox_file = Path("/tmp/casper_checkbox_value")
    if checkbox_file.exists():
        try:
            value = bool(open(str(checkbox_file)).read())
        except Exception as e:
            ret = False
    return ret


def focus_action(window_data, tree, subscription):
    global previous_focus, previous_workspace, casper_marks

    focus = window_data["container"]["id"]
    workspace = get_focused_workspace()
    casper_windows = get_casper_windows(casper_marks)
    if focus is not None:
        print(
            f"Got new focus {get_window_name_from_id(focus)}"
            f", previous {get_window_name_from_id(previous_focus)}"
            "\n\tCaspers " + str([
                get_window_name_from_id(c) for c in casper_windows
            ])
        )
        if (
            previous_focus in casper_windows and
            focus not in casper_windows and
            not box_is_checked()
        ):
            subscription.close()
            hide_container()
            setup_listener(casper_marks)

        previous_focus = focus
        previous_workspace = workspace


def enter_focus():
    global previous_focus, previous_workspace
    previous_focus = i3.filter(focused=True)[0]["id"]
    previous_workspace = get_focused_workspace()


def setup_listener(marks):
    global casper_marks
    casper_marks = marks
    print(f"Registering listener for {', '.join(casper_marks)}")
    enter_focus()
    i3.subscribe("window", "focus", callback=focus_action)


if __name__ == "__main__":
    args = parse_flags()
    if args.child is not None:
        print_parent_id(args.child)
    if args.workspace is not None:
        print(get_focused_workspace(prop=args.workspace))
    if args.get_childs is not None:
        print(' '.join([str(s) for s in get_casper_windows(args.get_childs)]))
    if args.get_active_display_rect:
        w, h, x, y = get_active_display_rect()
        print(f"{w} {h} {x} {y}")
    if args.listen:
        setup_listener(args.marks)
