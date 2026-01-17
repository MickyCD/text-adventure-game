# terminal-dungeon-crawler

This is a basic dungeon-crawler game, used as a personal project to explore C++, concepts taught in my classes (ex. Conway's Game of Life, Greedy Algorithm), and linking scipts in different languages. This project embeds a Python interpreter inside a C++ host to link the two languages, and also uses SQL for persistent data.

## Gameplay
* **`W`, `A`, `S`, `D`**: Move and Attack (bump combat).
* **`E`**: Interact / Pick up items.
* **`X`**: Save & Quit.

## Technical Features
* **Language:** The core engine is written in **C++** for performance, while game logic and events are scripted in **Python**, linked via the Python C API.
* **Procedural Generation:** Maps are generated dynamically using rules inspired by **Conway's Game of Life**, ensuring no two maps are identical.
* **Algorithmic AI:** Enemies track the player using a **Greedy Best-First Search** algorithm, based on my what I learned in class.
* **Save and Store:** Player stats and inventory are stored in an **SQLite** database.

## Setting Up
1. System Requirements
# Install GCC, Make, CMake, Python headers, and SQLite3
-sudo apt-get install build-essential cmake python3-dev libsqlite3-dev
2. Compilation
# This project uses CMake to manage dependencies. Pybind11 will be automatically fetched during the build process; no manual installation is required.
- git clone https://github.com/MickyCD/text-adventure-game.git
- mkdir build
- cd build
- cmake ..
- make
3. Running the Game
- ./text_adventure

