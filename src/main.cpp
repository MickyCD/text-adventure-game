#include <pybind11/embed.h>
#include <pybind11/stl.h> 
#include <sqlite3.h> 
#include <iostream>
#include <vector>
#include <string>
#include <queue>      
#include <algorithm>  

namespace py = pybind11;

// Forward Declarations
std::string getItemName(int id);
std::vector<int> allItemIDS();

// Game Data Structures
struct SaveData 
{
    int hp;
    int weaponType;
    bool isValid;
};

class Enemy 
{
public:
    int x, y;
    int hp;
    int damage;
    int typeID; 

    Enemy(int _x, int _y, int _hp, int _dmg, int _type) 
        : x(_x), y(_y), hp(_hp), damage(_dmg), typeID(_type) {}
};

class Chest {
public:
    int x, y;
    bool isEmpty; 

    Chest(int _x, int _y) : x(_x), y(_y), isEmpty(false) {}
};

class Player 
{
public:
    int hp;
    int weaponType; 
    std::string current_weapon_id;
    int x, y; 
    std::vector<int> inventory; 

    Player() : hp(20), weaponType(0), x(1), y(1) {} 

    void addItem(int itemID)
    {
        if (inventory.size() >= 5) {
            std::cout << "Inventory is full.\n";
            return;
        }
        std::string name = getItemName(itemID);
        if (name == "Unknown") {
            std::cout << "Error: Item " << itemID << " not in DB.\n";
        } else {
            inventory.push_back(itemID);
            std::cout << "Picked up: " << name << "\n";
        }
    }

    std::string inspectItem(int itemID) {
        return getItemName(itemID); 
    }

    void printInventory() {
        std::cout << "--- INVENTORY ---\n";
        if (inventory.empty()) std::cout << "(Empty)\n";
        else {
            for(int id : inventory) 
            {
                std::cout << "- " << getItemName(id) << " (ID: " << id << ")\n";
            }
        }
    }
};

// SQLite Database Management
void initializeDB() {
    sqlite3 *db;
    sqlite3_open("save_data.db", &db);
    sqlite3_exec(db, "CREATE TABLE IF NOT EXISTS savedData (hp INTEGER, weaponType INTEGER);", 0,0,0);
    sqlite3_exec(db, "CREATE TABLE IF NOT EXISTS itemRegistry (id INTEGER PRIMARY KEY, name TEXT, power INTEGER);", 0,0,0);
    // Seed initial data
    sqlite3_exec(db, "INSERT OR IGNORE INTO itemRegistry (id, name, power) VALUES (101, 'Wooden Sword', 2), (102, 'Iron Sword', 5), (103, 'Steel Sword', 7), (104, 'Obsidian Blade', 10), (105, 'Godly Sword', 20);", 0,0,0);
    sqlite3_close(db);
}

std::string getItemName(int id) {
    sqlite3 *db; sqlite3_stmt *stmt;
    sqlite3_open("save_data.db", &db);
    std::string result = "Unknown";
    
    if (sqlite3_prepare_v2(db, "SELECT name FROM itemRegistry WHERE id = ?;", -1, &stmt, 0) == SQLITE_OK) {
        sqlite3_bind_int(stmt, 1, id);
        if (sqlite3_step(stmt) == SQLITE_ROW) 
            result = std::string(reinterpret_cast<const char*>(sqlite3_column_text(stmt, 0)));
    }
    sqlite3_finalize(stmt); sqlite3_close(db);
    return result;
}

std::vector<int> allItemIDS() {
    sqlite3 *db; sqlite3_stmt *stmt;
    sqlite3_open("save_data.db", &db);
    std::vector<int> idList;
    
    if (sqlite3_prepare_v2(db, "SELECT id FROM itemRegistry ORDER BY id ASC;", -1, &stmt, 0) == SQLITE_OK) 
    {
        while (sqlite3_step(stmt) == SQLITE_ROW) 
            idList.push_back(sqlite3_column_int(stmt, 0));
    }
    sqlite3_finalize(stmt); sqlite3_close(db);
    return idList;
}

void save_game(Player *p) {
    sqlite3 *db; sqlite3_stmt *stmt;
    sqlite3_open("save_data.db", &db);
    
    // Clear previous save
    sqlite3_exec(db, "DELETE FROM savedData;", 0, 0, 0);
    
    if (sqlite3_prepare_v2(db, "INSERT INTO savedData (hp, weaponType) VALUES (?, ?);", -1, &stmt, 0) == SQLITE_OK) { 
        sqlite3_bind_int(stmt, 1, p->hp);
        sqlite3_bind_int(stmt, 2, p->weaponType);
        if (sqlite3_step(stmt) == SQLITE_DONE) printf("\nGame Saved.\n");
    }
    sqlite3_finalize(stmt); sqlite3_close(db);
}

void load_game(Player *p) {
    sqlite3 *db; sqlite3_stmt *stmt;
    sqlite3_open("save_data.db", &db);
    
    if (sqlite3_prepare_v2(db, "SELECT hp, weaponType FROM savedData LIMIT 1;", -1, &stmt, 0) == SQLITE_OK) {
        if (sqlite3_step(stmt) == SQLITE_ROW) {
            p->hp = sqlite3_column_int(stmt, 0);
            p->weaponType = sqlite3_column_int(stmt, 1);
            printf("\nGame Loaded.\n");
        }
    }    
    sqlite3_finalize(stmt); sqlite3_close(db);
}

// Pybind11 Module Definition
PYBIND11_EMBEDDED_MODULE(engine, m) 
{
    // Player Bindings
    py::class_<Player>(m, "Player")
        .def(py::init<>())
        .def_readwrite("hp", &Player::hp)
        .def_readwrite("current_weapon_id", &Player::current_weapon_id) 
        .def_readwrite("x", &Player::x)
        .def_readwrite("y", &Player::y)
        .def("addItem", &Player::addItem)
        .def("inspectItem", &Player::inspectItem)
        .def("printInventory", &Player::printInventory);

    // Enemy Bindings
    py::class_<Enemy>(m, "Enemy")
        .def(py::init<int, int, int, int, int>()) 
        .def_readwrite("x", &Enemy::x)
        .def_readwrite("y", &Enemy::y)
        .def_readwrite("hp", &Enemy::hp)
        .def_readwrite("damage", &Enemy::damage)
        .def_readwrite("typeID", &Enemy::typeID);

    // Chest Bindings
    py::class_<Chest>(m, "Chest")
        .def(py::init<int, int>())
        .def_readwrite("x", &Chest::x)
        .def_readwrite("y", &Chest::y)
        .def_readwrite("isEmpty", &Chest::isEmpty);

    // Global Function Exports
    m.def("save_game", &save_game); 
    m.def("load_game", &load_game); 
    m.def("getAllItemIDs", &allItemIDS);
    // m.def("find_path", &find_path); // TODO: Implement A* or JPS in C++
}

// Main Entry Point
int main() {
    initializeDB();
    py::scoped_interpreter guard{}; 
    
    try 
    {
        py::module_ logic = py::module_::import("game_logic"); 
        logic.attr("start_game")(); 
    } catch (py::error_already_set &e) {
        std::cout << "Python Error: " << e.what() << std::endl;
    }

    return 0;
}