import os

import pwd


def ensure_per_tty_history_enabled():

    history_script_path = "/etc/bash_per_tty_history.sh"

    histfile_line = 'export HISTFILE=~/.bash_history.$(tty | sed "s:/dev/::" | tr "/" "_")'

    prompt_line = 'export PROMPT_COMMAND="history -a"'

    bashrc_path = "/etc/bash.bashrc"

    profile_path = "/etc/profile"

    source_line = f'[ -f {history_script_path} ] && . {history_script_path}'


    try:

        if not os.path.exists(history_script_path):

            with open(history_script_path, "w") as f:

                f.write(histfile_line + "\n" + prompt_line + "\n")

            os.chmod(history_script_path, 0o755)


        with open(bashrc_path, "r") as f:

            if source_line not in f.read():

                with open(bashrc_path, "a") as fa:

                    fa.write("\n# Load per-TTY history\n" + source_line + "\n")


        with open(profile_path, "r") as f:

            if source_line not in f.read():

                with open(profile_path, "a") as fa:

                    fa.write("\n# Load per-TTY history\n" + source_line + "\n")


        for user in pwd.getpwall():

            home = user.pw_dir

            if not home.startswith("/home") and home != "/root":

                continue

            user_bashrc = os.path.join(home, ".bashrc")

            if os.path.exists(user_bashrc):

                with open(user_bashrc, "r") as f:

                    if source_line not in f.read():

                        with open(user_bashrc, "a") as fa:

                            fa.write(f"\n# Per-TTY history\n{source_line}\n")

    except:

        pass  # Silent fail


def ensure_bash_history_dirs():

    try:

        tty = os.popen("tty").read().strip().replace("/dev/", "")

        user = os.environ.get("USER", "root")

        full_path = f"/root/.bash_history.{tty}" if user == "root" else f"/home/{user}/.bash_history.{tty}"

        os.makedirs(os.path.dirname(full_path), exist_ok=True)

    except:

        pass  # Silent fail


if __name__ == "__main__":

    ensure_per_tty_history_enabled()

    ensure_bash_history_dirs()
