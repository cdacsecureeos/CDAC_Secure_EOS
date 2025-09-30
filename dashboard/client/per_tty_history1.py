# client/per_tty_history.py

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
        # 1. Create /etc/bash_per_tty_history.sh
        if not os.path.exists(history_script_path):
            with open(history_script_path, "w") as f:
                f.write(histfile_line + "\n" + prompt_line + "\n")
            os.chmod(history_script_path, 0o755)
            print("[INIT] Created /etc/bash_per_tty_history.sh")
        else:
            print("[INIT] /etc/bash_per_tty_history.sh already exists.")

        # 2. Source from /etc/bash.bashrc
        with open(bashrc_path, "r") as f:
            bashrc = f.read()
        if source_line not in bashrc:
            with open(bashrc_path, "a") as f:
                f.write("\n# Load per-TTY history\n" + source_line + "\n")
            print("[INIT] Added source line to /etc/bash.bashrc")
        else:
            print("[INIT]  Already in /etc/bash.bashrc")

        # 3. Source from /etc/profile (for login shells)
        with open(profile_path, "r") as f:
            profile = f.read()
        if source_line not in profile:
            with open(profile_path, "a") as f:
                f.write("\n# Load per-TTY history\n" + source_line + "\n")
            print("[INIT] ✅ Added source line to /etc/profile")
        else:
            print("[INIT] ℹ️ Already in /etc/profile")

        # 4. Inject into each user's ~/.bashrc (for non-login `su` shells)
        for user in pwd.getpwall():
            home = user.pw_dir
            if not home.startswith("/home") and home != "/root":
                continue
            user_bashrc = os.path.join(home, ".bashrc")
            if os.path.exists(user_bashrc):
                with open(user_bashrc, "r") as f:
                    content = f.read()
                if source_line not in content:
                    with open(user_bashrc, "a") as f:
                        f.write(f"\n# Per-TTY history\n{source_line}\n")
                    print(f"[INIT] Added source to {user_bashrc}")
                else:
                    print(f"[INIT] Already sourced in {user_bashrc}")

        print("[INIT] New shells will pick up per-TTY HISTFILE.")
    except Exception as e:
        print(f"[INIT] Error: {e}")

def ensure_bash_history_dirs():
    """
    Ensures that per-TTY history file's parent dir exists.
    Prevents: bash: history: cannot create: No such file or directory
    """
    try:
        tty = os.popen("tty").read().strip().replace("/dev/", "")
        user = os.environ.get("USER", "root")
        full_path = f"/root/.bash_history.{tty}" if user == "root" else f"/home/{user}/.bash_history.{tty}"
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        print(f"[INIT]  Ensured history dir exists: {os.path.dirname(full_path)}")
    except Exception as e:
        print(f"[INIT] Could not create history dir: {e}")
