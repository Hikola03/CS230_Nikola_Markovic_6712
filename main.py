from client import main as user_mode
from database import admin_menu

ART = [
    "                     .--.  .--.",
    "                    /    \\/    \\",
    "                   | .-.  .-.   \\",
    "                   |/_  |/_  |   \\",
    "                   || `\\|| `\\|    `----.",
    "                   |\\0_/ \\0_/    --,    \\_",
    " .--\"\"\"\"\"-.       /              (` \\     `-.",
    "/          \\-----'-.              \\          \\",
    "\\  () ()                         /`\\          \\",
    "|                         .___.-'   |          \\",
    "\\                        /` \\|      /           ;",
    " `-.___             ___.' .-.`.---.|             \\",
    "    \\| ``-..___,.-'`\\| / /   /     |              `\\",
    "     `      \\|      ,`/ /   /   ,  /",
    "             `      |\\ /   /    |\\/",
    "              ,   .'`-;   '     \\/",
    "         ,    |\\-'  .'   ,   .-'`",
    "       .-|\\--;`` .-'     |\\.'",
    "      ( `\"'-.|\\ (___,.--'`'   ",
    "       `-.    `\"`          _.--'",
    "          `.          _.-'`-.",
    "            `''---''``       `.",
]


def main():
    for line in ART:
        print(line)

    print("===== SYSTEM LOGIN =====")
    print("1. User")
    print("2. Admin")

    choice = input("> ")

    if choice == "2":
        password = input("Admin password: ")

        if password != "adminadmin":
            print("Wrong password")
            return

        admin_menu()
    else:
        user_mode()


if __name__ == "__main__":
    main()